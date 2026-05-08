from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import List, Optional
from app.api.deps.database import get_db
from app.api.deps.auth import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.models.post import Post
from app.models.tag import Tag
from app.models.like import Like
from app.models.comment import Comment
from app.models.follow import Follow
from app.schemas.post import PostCreate, PostUpdate, PostWithUser
from app.services.upload import UploadService, CloudinaryService
from app.utils.slug import generate_unique_slug
from app.core.config import settings
from app.services.cache import get_cached_post, set_cached_post, invalidate_cached_post, get_cached_posts_feed, get_cached_posts_list, set_cached_posts_feed, set_cached_posts_list
from app.core.limiter import limiter

router = APIRouter()

@router.get("/", response_model=List[PostWithUser])
@limiter.limit('60/minute')
async def list_posts(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """List all posts with filtering"""

    cache_key = f"{skip}:{limit}:{search}:{tag}"
    cached = await get_cached_posts_list(cache_key)
    if cached:
        return cached

    query = db.query(Post).filter(Post.is_published == True)

    if tag:
        tag_obj = db.query(Tag).filter(Tag.slug == tag).first()
        if tag_obj:
            query = query.filter(Post.tags.contains(tag_obj))

    if search:
        query = query.filter(Post.content.ilike(f"%{search}%"))

    posts = query.order_by(desc(Post.created_at)).offset(skip).limit(limit).all()

    result = [enrich_post(post, current_user, db) for post in posts]
    serialized = [p.model_dump() for p in result]
    await set_cached_posts_list(cache_key, serialized)
    return result

@router.get("/feed", response_model=List[PostWithUser])
@limiter.limit('60/minute')
async def get_feed(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get personalized feed (posts from followed users)"""

    cache_key = f"{current_user.id}:{skip}:{limit}"
    cached = await get_cached_posts_feed(cache_key)
    if cached:
        return cached

    following_ids = db.query(Follow.following_id).filter(
        Follow.follower_id == current_user.id
    ).subquery()

    posts = db.query(Post).filter(
        or_(
            Post.user_id.in_(following_ids),
            Post.user_id == current_user.id
        ),
        Post.is_published == True
    ).order_by(desc(Post.created_at)).offset(skip).limit(limit).all()

    result = [enrich_post(post, current_user, db) for post in posts]
    serialized = [p.model_dump() for p in result]
    await set_cached_posts_feed(cache_key, serialized)
    return result

@router.get("/user/{username}", response_model=List[PostWithUser])
@limiter.limit('60/minute')
async def get_user_posts(
    request: Request,
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Get posts by specific user"""

    user = db.query(User).filter(username == User.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    if current_user and current_user.id == user.id:
        query = db.query(Post).filter(Post.user_id == user.id)
    else:
        query = db.query(Post).filter(
            Post.user_id == user.id,
            Post.is_published == True
        )

    posts =query.order_by(desc(Post.created_at)).offset(skip).limit(limit).all()

    return [enrich_post(post, current_user, db) for post in posts]

@router.get("/{post_id}", response_model=PostWithUser)
@limiter.limit('60/minute')
async def get_post(
    request: Request,
    post_id: int,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Get single post"""

    cached = await get_cached_post(post_id)
    if cached:
        return cached

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found"
        )
    
    post.view_count += 1
    db.commit()

    result = enrich_post(post, current_user, db)
    await set_cached_post(post_id, result.model_dump())
    return result
 
@router.post("/", response_model=PostWithUser, status_code=status.HTTP_201_CREATED)
@limiter.limit('60/minute')
async def create_post(
    request: Request,
    post_in: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create new post"""

    post = Post(
        user_id=current_user.id,
        content=post_in.content,
        image_url=post_in.image_url,
        is_published=True
    )

    db.add(post)
    db.flush()

    if post_in.tag_names:
        for tag_name in post_in.tag_names:

            tag = db.query(Tag).filter(Tag.name == tag_name).first()

            if not tag:
                tag_slug = generate_unique_slug(tag_name)[:50]
                tag = Tag(name=tag_name, slug=tag_slug)
                db.add(tag)
                db.flush()

            post.tags.append(tag)


    db.commit() 
    db.refresh(post)

    await invalidate_cached_post(post.id)
    return enrich_post(post, current_user, db)

@router.post("/{post_id}/image", response_model=PostWithUser)
@limiter.limit('60/minute')
async def upload_post_image(
    request: Request,
    post_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload image for post"""

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found"
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized"
        )


    try:
        if settings.CLOUDINARY_CLOUD_NAME and CloudinaryService:
            image_url = await CloudinaryService.upload(file, folder='posts')
        else:
            image_url = await UploadService.save_local(file, folder='posts')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Upload failed: {str(e)}'
        )
    
    post.image_url = image_url
    db.commit()
    db.refresh(post)

    await invalidate_cached_post(post.id)
    return enrich_post(post, current_user, db)

@router.put("/{post_id}", response_model=PostWithUser)
@limiter.limit('60/minute')
async def update_post(
    request: Request,
    post_id: int,
    post_update: PostUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update post (own only)"""

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found"
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized"
        )

    update_data = post_update.model_dump(exclude_unset=True)

    if "tag_names" in update_data:
        tag_names = update_data.pop('tag_names')

        if tag_names is not None:
            post.tags = []

            for tag_name in tag_names:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()

                if not tag:
                    tag_slug = generate_unique_slug(tag_name)[:50]
                    tag = Tag(name=tag_name, slug=tag_slug)
                    db.add(tag)
                    db.flush()

                post.tags.append(tag)

    for field, value in update_data.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)

    await invalidate_cached_post(post.id)
    return enrich_post(post, current_user, db)

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit('60/minute')
async def delete_post(
    request: Request,
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete post (own only)"""

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found"
        )
    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized"
        )
    
    db.delete(post)
    db.commit()

    await invalidate_cached_post(post.id)
    return None

def enrich_post(post: Post, current_user: Optional[User], db: Session) -> PostWithUser:
    """Add stats and current user context to post"""

    likes_count = db.query(func.count(Like.id)).filter(Like.post_id == post.id).scalar()
    comments_count = db.query(func.count(Comment.id)).filter(Comment.post_id == post.id).scalar()

    is_liked = None

    if current_user:
        is_liked=db.query(Like).filter(
            Like.post_id == post.id,
            Like.user_id == current_user.id,
        ).first() is not None


    return PostWithUser.model_validate(
        {
            **post.__dict__,
            'user': post.user,
            'tags': post.tags,
            'likes_count': likes_count,
            'comments_count': comments_count,
            'is_liked': is_liked,
        }
    )
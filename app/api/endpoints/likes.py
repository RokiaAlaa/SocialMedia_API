from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.api.deps.database import get_db
from app.api.deps.auth import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.models.post import Post
from app.models.like import Like
from app.schemas.like import Like as LikeSchema, LikeCreate, LikeWithUser, PostLikesResponse, ReactionCount
from app.services.notification import create_notification
from app.models.notification import NotificationType
from app.core.limiter import limiter

router = APIRouter()

@router.post("/posts/{post_id}/like", response_model=LikeSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit('60/minute')
async def like_post(
    request: Request,
    post_id: int,
    like_in: LikeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Like/react to a post"""

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found"
        )
    
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == post_id
    ).first()

    if existing_like:

        existing_like.reaction_type = like_in.reaction_type
        db.commit()
        db.refresh(existing_like)

        return existing_like
    
    like = Like(
        user_id=current_user.id,
        post_id=post_id,
        reaction_type=like_in.reaction_type
    )

    db.add(like)
    db.commit()
    db.refresh(like)

    if post.user_id != current_user.id:
        await create_notification(
            db=db,
            user_id=post.user_id,
            sender_id=current_user.id,
            type=NotificationType.LIKE,
            post_id=post_id
        )
    return like

@router.delete("/posts/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit('60/minute')
async def unlike_post(
    request: Request,
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Unlike a post"""
    
    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == post_id
    ).first()

    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Like not found"
        )

    db.delete(like)
    db.commit()

    return None

@router.get("/posts/{post_id}/likes", response_model=PostLikesResponse)
@limiter.limit('60/minute')
async def get_post_likes(
    request: Request,
    post_id: int,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Get post likes with reaction breakdown"""

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found"
        )
    
    total_likes = db.query(func.count(Like.id)).filter(Like.post_id == post_id).scalar()

    reactions = db.query(
        Like.reaction_type,
        func.count(Like.id).label('count')
    ).filter(
        Like.post_id == post.id
    ).group_by(Like.reaction_type).all()

    reactions_count = [
        ReactionCount(reaction_type=r[0], count=r[1])
        for r in reactions
    ]

    user_reaction = None
    if current_user:
        user_like = db.query(Like).filter(
            Like.post_id == post_id,
            Like.user_id == current_user.id
        ).first()

        if user_like:
            user_reaction = user_like.reaction_type

    return PostLikesResponse(
        total_likes=total_likes,
        reactions=reactions_count,
        user_reaction=user_reaction
    )

@router.get("/posts/{post_id}/likes/users", response_model=List[LikeWithUser])
@limiter.limit('60/minute')
async def get_post_likes_users(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get users who liked a post"""

    likes = db.query(Like).filter(Like.post_id == post_id).all()

    return likes
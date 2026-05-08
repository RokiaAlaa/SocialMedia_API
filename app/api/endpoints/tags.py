from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List
from app.api.deps.database import get_db
from app.models.tag import Tag
from app.models.user import User
from app.models.post import Post, post_tags
from datetime import datetime, timezone, timedelta
from app.schemas.tag import TagWithCount
from app.schemas.post import PostWithUser
from app.api.endpoints.posts import enrich_post
from app.api.deps.auth import get_optional_current_user
from app.services.cache import get_cached_tag, get_cached_tags_list, get_cached_tags_trending, set_cached_tag, set_cached_tags_list, set_cached_tags_trending
from app.core.limiter import limiter

router = APIRouter()

@router.get("/", response_model=List[TagWithCount])
@limiter.limit('60/minute')
async def list_tags(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all tags with post counts"""

    cache_key = f"{skip}:{limit}"
    cached = await get_cached_tags_list(cache_key)
    if cached:
        return cached

    tags = db.query(
        Tag, func.count(post_tags.c.post_id).label('posts_count')
        ).outerjoin(post_tags, Tag.id == post_tags.c.tag_id
        ).group_by(Tag.id
        ).order_by(desc('posts_count')
        ).offset(skip).limit(limit).all()
    
    result = [TagWithCount.model_validate({**tag[0].__dict__, 'posts_count':tag[1]}) for tag in tags]
    serialized = [t.model_dump() for t in result]
    await set_cached_tags_list(cache_key, serialized)
    return result

@router.get("/trending", response_model=List[TagWithCount])
@limiter.limit('60/minute')
async def get_trending_tags(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get trending tags (most used in last 7 days)"""
    
    cached = await get_cached_tags_trending()
    if cached:
        return cached

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    trending = db.query(
        Tag, func.count(post_tags.c.post_id).label('posts_count')
        ).join(post_tags, Tag.id == post_tags.c.tag_id
        ).join(Post, Post.id == post_tags.c.post_id
        ).filter(
            Post.created_at >= seven_days_ago,
            Post.is_published == True
        ).group_by(Tag.id
        ).order_by(desc('posts_count')
        ).limit(limit).all()

    result = [TagWithCount.model_validate({**tag[0].__dict__, 'posts_count':tag[1]}) for tag in trending]
    serialized = [t.model_dump() for t in result]
    await set_cached_tags_trending(serialized)
    return result  

@router.get("/{slug}", response_model=TagWithCount)
@limiter.limit('60/minute')
async def get_tag(
    request: Request,
    slug: str,
    db: Session = Depends(get_db),
):
    """Get tag by slug"""
    cached = await get_cached_tag(slug)
    if cached:
        return cached
    
    tag = db.query(Tag).filter(Tag.slug == slug).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tag not found'
        )
    
    posts_count = db.query(func.count(post_tags.c.post_id)).filter(
        post_tags.c.tag_id == tag.id
    ).scalar()
    
    result = TagWithCount.model_validate({**tag.__dict__, 'posts_count':posts_count})
    await set_cached_tag(slug, result.model_dump())
    return result  

@router.get("/{slug}/posts", response_model=List[PostWithUser])
@limiter.limit('60/minute')
async def get_posts_by_tag(
    request: Request,
    slug: str,
    current_user: User = Depends(get_optional_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get posts with specific tag"""
    
    tag = db.query(Tag).filter(Tag.slug == slug).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tag not found'
        )
    
    posts = db.query(Post).join(
        post_tags, Post.id == post_tags.c.post_id
    ).filter(
        post_tags.c.tag_id == tag.id,
        Post.is_published == True
    ).order_by(
        desc(Post.created_at)
    ).offset(skip).limit(limit).all()

    return [enrich_post(post, current_user, db) for post in posts]
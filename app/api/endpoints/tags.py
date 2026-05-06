from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List
from app.api.deps.database import get_db
from app.models.tag import Tag
from app.models.user import User
from app.models.post import Post, post_tags
from datetime import datetime, timezone, timedelta
from app.schemas.tag import Tag as TagSchema, TagWithCount
from app.schemas.post import PostWithUser
from app.api.endpoints.posts import enrich_post
from app.api.deps.auth import get_optional_current_user

router = APIRouter()

@router.get("/", response_model=List[TagWithCount])
async def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all tags with post counts"""

    tags = db.query(
        Tag, func.count(post_tags.c.post_id).label('posts_count')
        ).outerjoin(post_tags, Tag.id == post_tags.c.tag_id
        ).group_by(Tag.id
        ).order_by(desc('posts_count')
        ).offset(skip).limit(limit).all()
    
    return [
        TagWithCount.model_validate({**tag[0].__dict__, 'posts_count':tag[1]})
        for tag in tags
    ]

@router.get("/trending", response_model=List[TagWithCount])
async def get_trending_tags(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get trending tags (most used in last 7 days)"""
    
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
    
    return [
        TagWithCount.model_validate({**tag[0].__dict__, 'posts_count':tag[1]})
        for tag in trending
    ]

@router.get("/{slug}", response_model=TagWithCount)
async def get_tag(
    slug: str,
    db: Session = Depends(get_db),
):
    """Get tag by slug"""
    
    tag = db.query(Tag).filter(Tag.slug == slug).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Tag not found'
        )
    
    posts_count = db.query(func.count(post_tags.c.post_id)).filter(
        post_tags.c.tag_id == tag.id
    ).scalar()
    
    return TagWithCount.model_validate({**tag.__dict__, 'posts_count':posts_count})

@router.get("/{slug}/posts", response_model=List[PostWithUser])
async def get_posts_by_tag(
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
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.api.deps.database import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.follow import Follow
from app.schemas.follow import Follow as FollowSchema, FollowResponse, FollowWithUser
from app.schemas.user import UserPublic
from app.services.notification import create_notification
from app.models.notification import NotificationType

router = APIRouter()

@router.post("/users/{username}/follow", response_model=FollowResponse, status_code=status.HTTP_201_CREATED)
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    
    """Follow a user"""

    user_to_follow = db.query(User).filter(User.username == username).first()
    if not user_to_follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    if user_to_follow.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot follow yourself"
        )
    
    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_to_follow.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Already following this user"
        )
    
    follow = Follow(
        follower_id = current_user.id,
        following_id = user_to_follow.id
    )

    db.add(follow)
    db.commit()

    await create_notification(
        db=db,
        user_id=user_to_follow.id,
        sender_id=current_user.id,
        type=NotificationType.FOLLOW
    )

    followers_count = db.query(func.count(Follow.id)).filter(
        Follow.following_id == user_to_follow.id
    ).scalar()

    following_count = db.query(func.count(Follow.id)).filter(
        Follow.follower_id == user_to_follow.id
    ).scalar()

    return FollowResponse(
        is_following=True,
        followers_count=followers_count,
        following_count=following_count
    )

@router.delete("/users/{username}/follow", response_model=FollowResponse, status_code=status.HTTP_200_OK)
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    
    """Unfollow a user"""

    user_to_follow = db.query(User).filter(User.username == username).first()
    if not user_to_follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_to_follow.id
    ).first()
    
    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Not following this user"
        )

    db.delete(follow)
    db.commit()

    followers_count = db.query(func.count(Follow.id)).filter(
        Follow.following_id == user_to_follow.id
    ).scalar()

    following_count = db.query(func.count(Follow.id)).filter(
        Follow.follower_id == user_to_follow.id
    ).scalar()

    return FollowResponse(
        is_following=False,
        followers_count=followers_count,
        following_count=following_count
    )

@router.get("/users/{username}/followers", response_model=List[UserPublic])
async def get_followers(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    
    """Get user's followers"""

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    

    follower_ids = db.query(Follow.follower_id).filter(
        Follow.following_id == user.id
    ).offset(skip).limit(limit).all()

    follower_ids = [f[0] for f in follower_ids]

    followers = db.query(User).filter(User.id.in_(follower_ids)).all()

    return followers

@router.get("/users/{username}/following", response_model=List[UserPublic])
async def get_following(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    
    """Get users that this user follows"""

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    

    following_ids = db.query(Follow.following_id).filter(
        Follow.follower_id == user.id
    ).offset(skip).limit(limit).all()

    following_ids = [f[0] for f in following_ids]

    followings = db.query(User).filter(User.id.in_(following_ids)).all()

    return followings
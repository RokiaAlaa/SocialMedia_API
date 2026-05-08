from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps.database import get_db
from app.api.deps.auth import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.models.post import Post
from app.models.follow import Follow
from app.schemas.user import User as UserSchema, UserProfile, UserUpdate
from app.services.upload import UploadService, CloudinaryService
from app.core.security import hash_password
from app.core.config import settings
from app.core.limiter import limiter
import logging

logger = logging.getLogger("app")

router = APIRouter()
@router.get("/{username}", response_model=UserProfile)
@limiter.limit('60/minute')
async def get_user_profile(
    request: Request,
    username: str,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Get user profile by username"""
    user = db.query(User).filter(username == User.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )

    posts_count = db.query(func.count(Post.id)).filter(Post.user_id == user.id).scalar()
    followers_count = db.query(func.count(Follow.id)).filter(Follow.following_id == user.id).scalar()
    following_count = db.query(func.count(Follow.id)).filter(Follow.follower_id == user.id).scalar()
    
    is_following = None

    if current_user:
        is_following=db.query(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user.id,
        ).first() is not None


    profile = UserProfile.model_validate(
        {
            **user.__dict__,
            'posts_count': posts_count,
            'followers_count': followers_count,
            'following_count': following_count,
            'is_following': is_following,

        }
    )

    return profile

@router.put("/{username}", response_model=UserSchema)
@limiter.limit('60/minute')
async def update_user_profile(
    request: Request,
    username: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user profile (own only)"""

    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only update your own profile'
        )

    update_data = user_update.model_dump(exclude_unset=True)

    if 'email' in update_data and update_data['email'] != current_user.email:
        existing = db.query(User).filter(User.email == update_data['email']).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
    if 'username' in update_data and update_data['username'] != current_user.username:
        existing = db.query(User).filter(User.username == update_data['username']).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )


    if 'password' in update_data:
        update_data['hashed_password'] = hash_password(update_data['password'])
        del update_data['password']


    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user

@router.put("/{username}/avatar", response_model=UserSchema)
@limiter.limit('60/minute')
async def upload_avatar(
    request: Request,
    username: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload user avatar"""

    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only update your own avatar'
        )

    if current_user.avatar_url:
        try:
            if settings.CLOUDINARY_CLOUD_NAME and CloudinaryService:
                CloudinaryService.delete(current_user.avatar_url)
            else:
                UploadService.delete_local(current_user.avatar_url)
        except Exception as e:
            logger.error(f"Failed to delete old avatar: {e}")

    try:
        if settings.CLOUDINARY_CLOUD_NAME and CloudinaryService:
            avatar_url = await CloudinaryService.upload(file, folder='avatars')
        else:
            avatar_url = await UploadService.save_local(file, folder='avatars')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Upload failed: {str(e)}'
        )
    
    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)

    return current_user

@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit('60/minute')
async def delete_user(
    request: Request,
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete user account (soft delete)"""

    if current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only delete your own profile'
        )
    
    current_user.is_active = False
    db.commit()

    return None
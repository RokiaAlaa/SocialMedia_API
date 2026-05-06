from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List

from app.api.deps.database import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import Notification as NotificationSchema, NotificationWithSender, UnreadCountResponse

router = APIRouter()

@router.get("/", response_model=List[NotificationWithSender])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get user's notifications"""
    
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()

    return notifications


@router.get("/unread-count", response_model=UnreadCountResponse) 
async def get_unread_counts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get count of unread notifications"""
    
    count = db.query(func.count(Notification.id)).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).scalar()

    return UnreadCountResponse(unread_count=count)


@router.put("/read-all", status_code=status.HTTP_200_OK) 
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read"""
    
    notification = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})

    db.commit()

    return {"message": "All notifications marked as read"}


@router.put("/{notification_id}/read", response_model=NotificationSchema) 
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark notification as read"""
    
    notification = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return notification


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT) 
async def delete_notification(
    notification_id: int, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete notification"""
    
    notification = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()

    return None
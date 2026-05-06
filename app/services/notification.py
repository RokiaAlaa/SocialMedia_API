from sqlalchemy.orm import Session
from app.services.websocket import manager
from app.models.notification import Notification, NotificationType
from app.models.user import User

async def create_notification(
    db:Session,
    user_id: int,
    sender_id: int,
    type: NotificationType,
    post_id: int = None,
    comment_id: int = None
) -> Notification:
    
    """Create notification and send via WebSocket"""
    
    if user_id == sender_id:
        return None
    
    notification = Notification(
        user_id=user_id,
        sender_id=sender_id,
        type=type,
        post_id=post_id,
        comment_id=comment_id,
        is_read=False
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    await send_notification_websocket(notification, db)

    return notification

async def send_notification_websocket(notification: Notification, db: Session):
    """Send notification via WebSocket"""

    sender = db.query(User).filter(User.id == notification.sender_id).first()

    message = {
        "type": "notification",
        "data": {
            "id": notification.id,
            "type": notification.type.value, 
            "sender": {
                "id": sender.id,
                "username": sender.username,
                "avatar_url": sender.avatar_url
            },
            "post_id":notification.post_id,
            "comment_id":notification.comment_id,
            "is_read":notification.is_read,
            "created_at":notification.created_at.isoformat()
        }
    }

    await manager.send_personal_message(notification.user_id, message)
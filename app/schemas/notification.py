from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.notification import NotificationType
from app.schemas.user import UserPublic

class NotificationBase(BaseModel):
    type: NotificationType

class Notification(NotificationBase):
    id: int
    user_id: int
    sender_id: int
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 

class NotificationWithSender(Notification):
    sender: UserPublic

class NotificationCreate(BaseModel):
    user_id: int
    sender_id: int
    type: NotificationType
    post_id: Optional[int] = None
    comment_id: Optional[int] = None

class UnreadCountResponse(BaseModel):
    unread_count: int
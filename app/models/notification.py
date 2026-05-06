from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
import enum

from app.api.deps.database import Base

class NotificationType(enum.Enum):
    FOLLOW = 'follow'
    LIKE = 'like'
    COMMENT = 'comment'
    REPLY = 'reply'


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    type = Column(Enum(NotificationType), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'))
    comment_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'))
    is_read = Column(Boolean, default=False)
    created_at = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=text('CURRENT_TIMESTAMP')
    ) 


    post = relationship('Post', back_populates="notifications")
    comment = relationship('Comment', back_populates="notifications")
    
    user = relationship(
        "User", 
        foreign_keys=[user_id], 
        back_populates="notifications"
    )

    sender = relationship(
        "User", 
        foreign_keys=[sender_id], 
        back_populates="sent_notifications"
    )
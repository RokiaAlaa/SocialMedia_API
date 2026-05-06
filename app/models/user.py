from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.api.deps.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    fullname = Column(String)
    bio = Column(Text) 
    avatar_url = Column(String)
    is_active = Column(Boolean, server_default='1')
    is_verified = Column(Boolean, server_default='0')

    created_at = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=text('CURRENT_TIMESTAMP')
    ) 

    updated_at = Column(
        TIMESTAMP(timezone=True), 
        nullable=True, 
        server_default=text('CURRENT_TIMESTAMP'),
        onupdate=text('CURRENT_TIMESTAMP')
    ) 

    posts = relationship('Post', back_populates="user", cascade='all, delete-orphan')
    comments = relationship('Comment', back_populates="user", cascade='all, delete-orphan')
    likes = relationship('Like', back_populates="user", cascade='all, delete-orphan')

    notifications = relationship(
        "Notification", 
        foreign_keys="Notification.user_id", 
        back_populates="user", 
        cascade='all, delete-orphan'
    )

    sent_notifications = relationship(
        "Notification", 
        foreign_keys="Notification.sender_id", 
        back_populates="sender"
    )

    followers = relationship(
        "Follow", 
        foreign_keys="Follow.following_id", 
        back_populates="following_user", 
        cascade='all, delete-orphan'
    )

    following = relationship(
        "Follow", 
        foreign_keys="Follow.follower_id", 
        back_populates="follower_user", 
        cascade='all, delete-orphan'
    )
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.api.deps.database import Base

post_tags = Table( 
    'post_tags',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'))
)

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String)
    is_published = Column(Boolean, server_default='1')
    view_count = Column(Integer, server_default='0')

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

    user = relationship('User', back_populates="posts")
    comments = relationship('Comment', back_populates="post", cascade='all, delete-orphan')
    likes = relationship('Like', back_populates="post", cascade='all, delete-orphan')
    tags = relationship('Tag', secondary=post_tags, back_populates="posts")
    notifications = relationship('Notification', back_populates="post", cascade='all, delete-orphan') 

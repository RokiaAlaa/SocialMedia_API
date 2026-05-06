from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.api.deps.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    parent_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'))
    content = Column(Text, nullable=False)
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

    post = relationship('Post', back_populates="comments")
    user = relationship('User', back_populates="comments")
    parent = relationship('Comment', remote_side=[id], backref='replies')
    notifications = relationship('Notification', back_populates="comment", cascade='all, delete-orphan') 

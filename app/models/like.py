from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
import enum

from app.api.deps.database import Base

class ReactionType(enum.Enum):
    LIKE = 'like'
    LOVE = 'love'
    LAUGH = 'laugh'
    WOW = 'wow'
    SAD = 'sad'
    ANGRY = 'angry'


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reaction_type = Column(Enum(ReactionType), default=ReactionType.LIKE)
    created_at = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=text('CURRENT_TIMESTAMP')
    ) 

    __table_args__ = (UniqueConstraint('user_id', 'post_id', name='_user_post_uc'),)

    user = relationship('User', back_populates="likes")
    post = relationship('Post', back_populates="likes")
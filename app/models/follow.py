from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.api.deps.database import Base

class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    following_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=text('CURRENT_TIMESTAMP')
    ) 

    __table_args__ = (UniqueConstraint('follower_id', 'following_id', name='_follower_following_uc'),)


    following_user = relationship(
        "User", 
        foreign_keys=[following_id], 
        back_populates="followers", 
    )

    follower_user = relationship(
        "User", 
        foreign_keys=[follower_id], 
        back_populates="following", 
    )

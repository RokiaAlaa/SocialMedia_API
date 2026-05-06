from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from app.models.post import post_tags

from app.api.deps.database import Base

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)

    created_at = Column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=text('CURRENT_TIMESTAMP')
    ) 

    posts = relationship('Post', secondary=post_tags, back_populates="tags")
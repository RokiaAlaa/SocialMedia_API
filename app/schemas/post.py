from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.tag import Tag
from app.schemas.user import UserPublic

class PostBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000) 
    image_url: Optional[str] = None

class PostCreate(PostBase):
    tag_names: Optional[List[str]] = []

class PostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=5000) 
    image_url: Optional[str] = None
    is_published: Optional[bool] = None
    tag_names: Optional[List[str]] = None 

class Post(PostBase):
    id: int
    user_id: int
    is_published: bool
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None 

    model_config = ConfigDict(from_attributes=True) 

class PostWithUser(Post):
    user: UserPublic
    tags: List[Tag] = []
    likes_count: int = 0
    comments_count: int = 0
    is_liked: Optional[bool] = None
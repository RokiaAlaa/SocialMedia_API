from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.user import UserPublic

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000) 

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    content: str= Field(..., min_length=1, max_length=1000) 


class Comment(CommentBase):
    id: int
    post_id: int
    user_id: int
    parent_id: Optional[int] = None 
    created_at: datetime
    updated_at: Optional[datetime] = None 

    model_config = ConfigDict(from_attributes=True) 

class CommentWithUser(Comment):
    user: UserPublic
    replies: List['CommentWithUser'] = [] 

CommentWithUser.model_rebuild() 
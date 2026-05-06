from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.like import ReactionType
from app.schemas.user import UserPublic

class LikeCreate(BaseModel):
    reaction_type: ReactionType = ReactionType.LIKE

class Like(BaseModel):
    id: int
    user_id: int
    post_id: int
    reaction_type: ReactionType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 

class LikeWithUser(Like):
    user: UserPublic

class ReactionCount(BaseModel):
    reaction_type: ReactionType
    count: int

class PostLikesResponse(BaseModel):
    total_likes: int
    reactions: List[ReactionCount]
    user_reaction: Optional[ReactionType] = None 
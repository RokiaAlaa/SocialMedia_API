from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.user import UserPublic

class Follow(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 

class FollowWithUser(Follow):
    user: UserPublic

class FollowResponse(BaseModel):
    is_following: bool
    followers_count: int
    following_count: int
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50) 
    fullname: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(min_length=6) 

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None,  min_length=3, max_length=50) 
    fullname: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500) 
    password: Optional[str] = Field(None, min_length=6)

class User(UserBase):
    id: int
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None 

    model_config = ConfigDict(from_attributes=True) 

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(User):
    posts_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    is_following: Optional[bool] = None

class UserPublic(BaseModel):
    id: int
    username: str
    fullname: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True) 
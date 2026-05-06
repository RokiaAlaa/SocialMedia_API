from pydantic import BaseModel, ConfigDict
from datetime import datetime

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    slug: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 

class TagWithCount(Tag):
    posts_count: int = 0
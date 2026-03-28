from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class PartCategoryCreate(BaseModel):
    name: str
    slug: str


class PartCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None


class PartCategoryResponse(BaseModel):
    id  : UUID
    name: str
    slug: str

    class Config:
        orm_mode = True
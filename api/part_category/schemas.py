from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class PartCategoryCreate(BaseModel):
    name                 : str
    slug                 : str
    part_category_img_url: Optional[str] = None


class PartCategoryUpdate(BaseModel):
    name                  : Optional[str] = None
    slug                  : Optional[str] = None
    part_category_img_url : Optional[str] = None


class PartCategoryResponse(BaseModel):
    id                   : UUID
    name                 : str
    slug                 : str
    part_category_img_url: Optional[str] = None

    class Config:
        orm_mode = True
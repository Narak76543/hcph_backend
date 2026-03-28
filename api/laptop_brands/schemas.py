from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class LaptopBrandCreate(BaseModel):
    name         : str
    slug         : str
    brand_img_url: Optional[str] = None


class LaptopBrandUpdate(BaseModel):
    name         : Optional[str] = None
    slug         : Optional[str] = None
    brand_img_url: Optional[str] = None


class LaptopBrandResponse(BaseModel):
    id           : UUID
    name         : str
    slug         : str
    brand_img_url: Optional[str] = None

    class Config:
        orm_mode = True
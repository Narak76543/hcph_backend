from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from api.laptop_brands.schemas import LaptopBrandResponse


class LaptopSubBrandCreate(BaseModel):
    brand_id         : UUID
    name             : str
    slug             : str
    sub_brand_img_url: Optional[str] = None


class LaptopSubBrandUpdate(BaseModel):
    name             : Optional[str] = None
    slug             : Optional[str] = None
    sub_brand_img_url: Optional[str] = None


class LaptopSubBrandResponse(BaseModel):
    id               : UUID
    brand_id         : UUID
    name             : str
    slug             : str
    sub_brand_img_url: Optional[str] = None
    brand            : Optional[LaptopBrandResponse] = None

    class Config:
        orm_mode = True

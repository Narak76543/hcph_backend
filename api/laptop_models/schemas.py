from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from api.laptop_brands.schemas import LaptopBrandResponse


class LaptopModelCreate(BaseModel):
    brand_id    : UUID
    name        : str
    slug        : str
    release_year: Optional[int] = None
    cpu         : Optional[str] = None
    gpu         : Optional[str] = None
    form_factor : Optional[str] = None


class LaptopModelUpdate(BaseModel):
    brand_id    : Optional[UUID] = None
    name        : Optional[str]  = None
    slug        : Optional[str]  = None
    release_year: Optional[int]  = None
    cpu         : Optional[str]  = None
    gpu         : Optional[str]  = None
    form_factor : Optional[str]  = None


class LaptopModelResponse(BaseModel):
    id          : UUID
    brand_id    : UUID
    name        : str
    slug        : str
    release_year: Optional[int]
    cpu         : Optional[str]
    gpu         : Optional[str]
    form_factor : Optional[str]
    brand       : Optional[LaptopBrandResponse] = None

    class Config:
        orm_mode = True
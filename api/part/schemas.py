from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class PartCreate(BaseModel):
    category_id  : UUID
    brand        : str
    model_name   : str
    specification: Optional[str] = None
    img_url      : Optional[str] = None


class PartUpdate(BaseModel):
    category_id  : Optional[UUID] = None
    brand        : Optional[str]  = None
    model_name   : Optional[str]  = None
    specification: Optional[str]  = None
    img_url      : Optional[str]  = None


class PartResponse(BaseModel):
    id           : UUID
    category_id  : UUID
    brand        : str
    model_name   : str
    specification: Optional[str]
    img_url      : Optional[str]
    create_at    : datetime

    class Config:
        orm_mode = True
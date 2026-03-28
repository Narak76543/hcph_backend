from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID

from api.laptop_models.schemas import LaptopModelResponse


class UserLaptopCreate(BaseModel):
    laptop_model_id: UUID
    nickname       : Optional[str] = None


class UserLaptopUpdate(BaseModel):
    nickname: Optional[str] = None


class UserLaptopResponse(BaseModel):
    id             : UUID
    user_id        : UUID
    laptop_model_id: UUID
    nickname       : Optional[str]
    laptop_model   : Optional[LaptopModelResponse] = None

    class Config:
        orm_mode = True
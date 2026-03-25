from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from api.shops.models import ShopStatus


class ShopCreate(BaseModel):
    name            : str
    address         : str
    phone           : str
    telegram_handle : Optional[str] = None
    shop_pro_img_url: Optional[str] = None


class ShopUpdate(BaseModel):
    name            : Optional[str] = None
    address         : Optional[str] = None
    phone           : Optional[str] = None
    telegram_handle : Optional[str] = None
    shop_pro_img_url: Optional[str] = None


class ShopResponse(BaseModel):
    id              : UUID
    owner_id        : UUID
    name            : str
    address         : str
    phone           : str
    telegram_handle : Optional[str]
    status          : ShopStatus
    create_at       : datetime
    shop_pro_img_url: Optional[str]

    class Config:
        orm_mode = True

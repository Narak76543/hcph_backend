from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from api.shops.models import ShopStatus


class ShopCreate(BaseModel):
    name            : str
    phone           : str
    telegram_handle : Optional[str] = None
    
    province        : Optional[str] = None
    district        : Optional[str] = None
    detail          : Optional[str] = None
    google_maps_url : Optional[str] = None
    address         : Optional[str] = None
    
    shop_pro_img_url: Optional[str] = None


class ShopUpdate(BaseModel):
    name            : Optional[str] = None
    phone           : Optional[str] = None
    telegram_handle : Optional[str] = None
    
    province        : Optional[str] = None
    district        : Optional[str] = None
    detail          : Optional[str] = None
    google_maps_url : Optional[str] = None
    address         : Optional[str] = None
    
    shop_pro_img_url: Optional[str] = None


class ShopResponse(BaseModel):
    id              : UUID
    owner_id        : UUID
    name            : str
    phone           : str
    telegram_handle : Optional[str]
    
    province        : Optional[str] = None
    district        : Optional[str] = None
    detail          : Optional[str] = None
    google_maps_url : Optional[str] = None
    address         : Optional[str] = None
    
    status          : ShopStatus
    create_at       : datetime
    shop_pro_img_url: Optional[str]

    class Config:
        orm_mode = True

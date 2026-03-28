from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from api.shop_listing.models import PartCondition



class ShopListingCreate(BaseModel):
    part_id       : UUID
    price         : Decimal
    stock_quantity: int
    condition     : PartCondition = PartCondition.new


class ShopListingUpdate(BaseModel):
    price         : Optional[Decimal]        = None
    stock_quantity: Optional[int]            = None
    condition     : Optional[PartCondition]  = None


class ShopListingResponse(BaseModel):
    id            : UUID
    shop_id       : UUID
    part_id       : UUID
    price         : Decimal
    stock_quantity: int
    condition     : PartCondition
    update_at     : datetime

    class Config:
        orm_mode = True
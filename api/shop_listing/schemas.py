from pydantic import BaseModel
from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from api.part.schemas import PartResponse
from api.part_category.schemas import PartCategoryResponse
from api.shop_listing.models import PartCondition
from api.shops.schemas import ShopResponse



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


class HardwareListingResponse(BaseModel):
    listing      : ShopListingResponse
    part         : PartResponse
    category     : PartCategoryResponse
    hardware_type: str
    spec         : dict[str, Any]


class ShopListingWithDetails(BaseModel):
    listing: ShopListingResponse
    part   : PartResponse
    shop   : ShopResponse

    class Config:
        orm_mode = True


class ShopListingCard(BaseModel):
    # core listing fields
    id            : UUID
    shop_id       : UUID
    part_id       : UUID
    price         : Decimal
    stock_quantity: int
    condition     : PartCondition
    update_at     : datetime
    # denormalized helpers for frontend
    shop_name     : Optional[str] = None
    shop_image    : Optional[str] = None
    part_image    : Optional[str] = None
    part_brand    : Optional[str] = None
    part_model    : Optional[str] = None
    # owner info for delete/edit permissions
    owner_id      : Optional[UUID] = None
    owner_full_name: Optional[str] = None
    # nested objects for legacy client parsing
    shop          : Optional[ShopResponse] = None
    part          : Optional[PartResponse] = None

    class Config:
        orm_mode = True

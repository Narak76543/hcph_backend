from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class ShopAddressCreate(BaseModel):
    province       : str
    district       : str
    detail         : Optional[str]   = None
    google_maps_url: Optional[str]   = None
    latitude       : Optional[float] = None
    longitude      : Optional[float] = None
    is_main        : bool            = False


class ShopAddressUpdate(BaseModel):
    province       : Optional[str]   = None
    district       : Optional[str]   = None
    detail         : Optional[str]   = None
    google_maps_url: Optional[str]   = None
    latitude       : Optional[float] = None
    longitude      : Optional[float] = None
    is_main        : Optional[bool]  = None


class ShopAddressResponse(BaseModel):
    id             : UUID
    shop_id        : UUID
    province       : str
    district       : str
    detail         : Optional[str]
    google_maps_url: Optional[str]
    latitude       : Optional[float]
    longitude      : Optional[float]
    is_main        : bool

    class Config:
        from_attributes = True
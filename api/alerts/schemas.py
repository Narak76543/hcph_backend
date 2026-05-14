from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from api.shop_listing.schemas import ShopListingCard


class AlertResponse(BaseModel):
    id: str
    title: str
    subtitle: str
    type: str
    created_at: Optional[datetime] = None
    is_unread: bool = False
    listing_id: Optional[UUID] = None


class SavedListingCreate(BaseModel):
    listing_id: UUID


class ListingEngagementResponse(BaseModel):
    listing_id: UUID
    reaction_count: int = 0
    save_count: int = 0
    share_count: int = 0
    reacted: bool = False
    saved: bool = False
    link_url: str


class SavedListingResponse(BaseModel):
    id: UUID
    user_id: UUID
    listing_id: UUID
    created_at: datetime
    listing: Optional[ShopListingCard] = None

    class Config:
        orm_mode = True

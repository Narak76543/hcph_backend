import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db import Base


class SavedListing(Base):
    __tablename__ = "TBL_SAVED_LISTINGS"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"), nullable=False)
    listing_id = Column(
        UUID(as_uuid=True),
        ForeignKey("TBL_SHOP_LISTING.id"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", name="uq_saved_listing_user_listing"),
    )


class ListingReaction(Base):
    __tablename__ = "TBL_LISTING_REACTIONS"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"), nullable=False)
    listing_id = Column(
        UUID(as_uuid=True),
        ForeignKey("TBL_SHOP_LISTING.id"),
        nullable=False,
    )
    reaction_type = Column(String(30), nullable=False, default="flame")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "listing_id",
            "reaction_type",
            name="uq_listing_reaction_user_listing_type",
        ),
    )


class ListingShare(Base):
    __tablename__ = "TBL_LISTING_SHARES"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"), nullable=True)
    listing_id = Column(
        UUID(as_uuid=True),
        ForeignKey("TBL_SHOP_LISTING.id"),
        nullable=False,
    )
    channel = Column(String(30), nullable=False, default="copy_link")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

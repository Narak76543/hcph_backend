import uuid
from sqlalchemy import Column, String, Boolean, Float, ForeignKey, Text, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Session
from core.db import Base


class ShopAddress(Base):
    __tablename__ = "TBL_ADDRESSES"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id        = Column(UUID(as_uuid=True), ForeignKey("TBL_SHOPS.id"), nullable=False)
    province       = Column(String(100), nullable=False)
    district       = Column(String(100), nullable=False)
    detail         = Column(String(255), nullable=True)   # street/building detail
    google_maps_url= Column(Text,        nullable=True)
    latitude       = Column(Float,       nullable=True)
    longitude      = Column(Float,       nullable=True)
    is_main        = Column(Boolean,     default=False)

    shop = relationship("Shop", backref="addresses")

# ── Auto enforce only one is_main per shop 
@event.listens_for(ShopAddress, "before_insert")
@event.listens_for(ShopAddress, "before_update")
def enforce_single_main(mapper, connection, target):
    if target.is_main:
        connection.execute(
            ShopAddress.__table__.update()
            .where(ShopAddress.__table__.c.shop_id == target.shop_id)
            .where(ShopAddress.__table__.c.id != target.id)
            .values(is_main=False)
        )
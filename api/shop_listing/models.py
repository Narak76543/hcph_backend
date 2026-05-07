import uuid
import enum
from sqlalchemy import Column, String, Integer, Numeric, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db import Base


class PartCondition(str, enum.Enum):
    NEW          = "NEW"
    USED         = "USED"
    REFURBISHED  = "REFURBISHED"
    # Handling lowercase data from database
    new          = "new"
    used         = "used"
    refurbished  = "refurbished"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value.upper() == other.upper()
        if isinstance(other, PartCondition):
            return self.value.upper() == other.value.upper()
        return False

    def __hash__(self):
        return hash(self.value.upper())


class ShopListing(Base):
    __tablename__ = "TBL_SHOP_LISTING"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id        = Column(UUID(as_uuid=True), ForeignKey("TBL_SHOPS.id"), nullable=False)
    part_id        = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"),  nullable=False)
    price          = Column(Numeric(10, 2),     nullable=False)
    stock_quantity = Column(Integer,            nullable=False, default=0)
    condition      = Column(Enum(PartCondition), default=PartCondition.NEW, nullable=False)
    update_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    shop = relationship("Shop", backref="listings")
    part = relationship("Part", backref="listings")
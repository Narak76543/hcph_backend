import uuid
import enum
from sqlalchemy import Column, String, Enum, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db import Base


class ShopStatus(str, enum.Enum):
    pending  = "PENDING"
    active   = "ACTIVE"
    inactive = "INACTIVE"


class Shop(Base):
    __tablename__ = "TBL_SHOPS"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id         = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"), nullable=False)
    name             = Column(String(100), nullable=False)
    phone            = Column(String(20),  nullable=False)
    telegram_handle  = Column(String(100), nullable=True)
    
    # Detailed Address
    province         = Column(String(100), nullable=True)
    district         = Column(String(100), nullable=True)
    detail           = Column(String(255), nullable=True)
    google_maps_url  = Column(Text,        nullable=True)
    
    # Summary/Legacy Address
    address          = Column(String(255), nullable=True)
    
    status           = Column(Enum(ShopStatus), default=ShopStatus.pending, nullable=False)
    create_at        = Column(DateTime(timezone=True), server_default=func.now())
    shop_pro_img_url = Column(Text, nullable=True)

    owner = relationship("User", backref="shops")
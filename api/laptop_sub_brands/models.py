import uuid
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import Base


class LaptopSubBrand(Base):
    __tablename__ = "TBL_LAPTOP_SUB_BRANDS"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id         = Column(UUID(as_uuid=True), ForeignKey("TBL_LAPTOP_BRANDS.id"), nullable=False)
    name             = Column(String(100), nullable=False)
    slug             = Column(String(100), unique=True, nullable=False)
    sub_brand_img_url = Column(Text, nullable=True)

    brand  = relationship("LaptopBrand", backref="sub_brands")
    models = relationship("LaptopModel", backref="sub_brand")

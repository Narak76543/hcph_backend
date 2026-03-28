import uuid
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import Base


class LaptopBrand(Base):
    __tablename__ = "TBL_LAPTOP_BRANDS"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name          = Column(String(100), unique=True, nullable=False)
    slug          = Column(String(100), unique=True, nullable=False)
    brand_img_url = Column(Text, nullable=True)

    models = relationship("LaptopModel", backref="brand")
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db import Base


class Part(Base):
    __tablename__ = "TBL_PART"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id   = Column(UUID(as_uuid=True), ForeignKey("TBL_PART_CATEGORIES.id"), nullable=False)
    brand         = Column(String(100), nullable=False)
    model_name    = Column(String(100), nullable=False)
    specification = Column(Text, nullable=True)
    img_url       = Column(Text, nullable=True)
    create_at     = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("PartCategory", back_populates="parts")
import uuid
from sqlalchemy import Column, String , Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import Base

class PartCategory(Base):
    __tablename__ = "TBL_PART_CATEGORIES"

    id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    part_category_img_url = Column(Text , nullable= True)

    parts = relationship("Part", back_populates="category")
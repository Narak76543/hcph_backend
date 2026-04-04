import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import Base


class LaptopModel(Base):
    __tablename__ = "TBL_LAPTOP_MODELS"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id     = Column(UUID(as_uuid=True), ForeignKey("TBL_LAPTOP_BRANDS.id"), nullable=False)
    name         = Column(String(150), nullable=False)
    slug         = Column(String(150), unique=True, nullable=False)
    release_year = Column(Integer,     nullable=True)
    cpu          = Column(String(100), nullable=True)
    gpu          = Column(String(100), nullable=True)
    form_factor  = Column(String(50),  nullable=True)
    created_by   = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"), nullable=True)

    user = relationship("User", backref="created_models")
    spec = relationship("LaptopSpec", uselist=False, back_populates="laptop_model")
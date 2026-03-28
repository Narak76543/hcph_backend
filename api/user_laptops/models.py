import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import Base


class UserLaptop(Base):
    __tablename__ = "TBL_USER_LAPTOPS"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"),         nullable=False)
    laptop_model_id = Column(UUID(as_uuid=True), ForeignKey("TBL_LAPTOP_MODELS.id"), nullable=False)
    nickname        = Column(String(100), nullable=True)   # e.g. "My Work Laptop"

    user         = relationship("User",        backref="laptops")
    laptop_model = relationship("LaptopModel", backref="user_laptops")
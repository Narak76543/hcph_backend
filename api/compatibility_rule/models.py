import uuid
from sqlalchemy import Column, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import Base


class CompatibilityRule(Base):
    __tablename__ = "TBL_COMPATIBILITY_RULE"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    laptop_model_id = Column(UUID(as_uuid=True), ForeignKey("TBL_LAPTOP_MODELS.id"), nullable=False)
    part_id         = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"),           nullable=False)
    is_compatible   = Column(Boolean, nullable=False, default=True)
    notes           = Column(Text, nullable=True)
    verify_by       = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"),          nullable=True)

    laptop_model = relationship("LaptopModel", backref="compatibility_rules")
    part         = relationship("Part",        backref="compatibility_rules")
    verifier     = relationship("User",        backref="verified_rules")
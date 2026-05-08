import uuid
import enum
from sqlalchemy import Column, String, Enum, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db import Base


class RequestStatus(str, enum.Enum):
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RoleRequest(Base):
    __tablename__ = "TBL_ROLE_REQUESTS"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"), nullable=False)
    shop_name    = Column(String(100), nullable=False)
    shop_address = Column(String(255), nullable=False)
    phone        = Column(String(20),  nullable=False)
    reason       = Column(Text,        nullable=True)
    status       = Column(Enum(RequestStatus, values_callable=lambda x: [e.value for e in x]), default=RequestStatus.PENDING, nullable=False)
    admin_note   = Column(Text,        nullable=True)
    create_at    = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="role_requests")
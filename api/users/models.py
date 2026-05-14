import uuid
import enum
from sqlalchemy import Column, String, Boolean, Enum, DateTime, Text, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from core.db import Base


class UserRole(str, enum.Enum):
    USER      = "user"
    TECHNICAL = "technical"
    ADMIN     = "admin"


class AuthProvider(str, enum.Enum):
    LOCAL    = "local"
    TELEGRAM = "telegram"
    GOOGLE   = "google"


class User(Base):
    __tablename__ = "TBL_USERS"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    firstname_lc      = Column(String(100), nullable=False)
    lastname_lc       = Column(String(100), nullable=False)
    firstname         = Column(String(100), nullable=False)
    lastname          = Column(String(100), nullable=False)
    username          = Column(String(50),  unique=True, nullable=False)
    email             = Column(String(100), unique=True, nullable=False)
    phone_number      = Column(String(20),  unique=True, nullable=False)
    password_hash     = Column(String(255), nullable=False)

    # auth Provider
    auth_provider     = Column(Enum(AuthProvider), default=AuthProvider.LOCAL, nullable=False)

    # google field
    google_id         = Column(String(100), unique=True, nullable=True)

    telegram_id       = Column(BigInteger,  unique=True, nullable=True)
    telegram_username = Column(String(100), nullable=True)

    role              = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_verified       = Column(Boolean,  default=False)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), server_default=func.now())
    profile_image_url = Column(Text, nullable=True)


class UserFollow(Base):
    __tablename__ = "TBL_USER_FOLLOWS"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"), nullable=False)
    following_id = Column(UUID(as_uuid=True), ForeignKey("TBL_USERS.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_user_follow_pair"),
    )

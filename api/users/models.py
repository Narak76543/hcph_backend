import uuid
import enum
from sqlalchemy import Column, String, Boolean, Enum, DateTime , Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import Column
from core.db import Base

class UserRole (str , enum.Enum):
    user      = "USER"
    technical = "TECHNICAL"
    admin     = "ADMIN"

class User (Base):
    __tablename__ = "TBL_USERS"

    id                = Column(UUID(as_uuid= True) , primary_key= True , default=uuid.uuid4)
    firstname_lc      = Column(String(100), nullable= False)
    lastname_lc       = Column(String(100), nullable= False)
    firstname         = Column(String(100), nullable= False)
    lastname          = Column(String(100), nullable= False)
    username          = Column(String(50) , unique= True , nullable= False)
    email             = Column(String(100), unique= True , nullable= False)
    phone_number      = Column(String(20) , unique= True , nullable= False)
    password_hash     = Column(String(255), nullable= False)
    role              = Column(Enum(UserRole) , default= UserRole.user , nullable= False)
    is_verified       = Column(Boolean , default= False)
    created_at        = Column(DateTime(timezone= True) , server_default= func.now())
    profile_image_url = Column(Text , nullable= True)

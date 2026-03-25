from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime
from api.users.models import UserRole

class UserCreate(BaseModel):
    firstname_ls     : str
    lastname_lc      : str
    firstname        : str
    lastname         : str
    username         : str
    email            : EmailStr
    phone_number     : Optional[str] = None
    password         : str
    profile_image_url: Optional[str]
 
 
class UserUpdate(BaseModel):

    firstname_lc      : Optional[str] = None
    lastname_lc       : Optional[str] = None
    firstname         : Optional[str] = None
    lastname          : Optional[str] = None
    username          : Optional[str] = None
    phone_number      : Optional[str] = None
    profile_image_url : Optional[str] = None
 
 
class UserLogin(BaseModel):
    email   : EmailStr
    password: str
 
 
class UserResponse(BaseModel):

    id               : UUID
    firstname_lc     : str
    lastname_lc      : str
    firstname        : str
    lastname         : str
    username         : str
    email            : str
    phone_number     : Optional[str]
    role             : UserRole
    is_verified      : bool
    created_at       : datetime
    profile_image_url: Optional[str]
 
    class Config:
        orm_mode = True
 
 
class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse
 

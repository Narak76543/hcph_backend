from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

from api.role_request.models import RequestStatus


class RoleRequestCreate(BaseModel):
    shop_name   : str
    shop_address: str
    phone       : str
    reason      : Optional[str] = None


class RoleRequestReject(BaseModel):
    admin_note: Optional[str] = None   # admin can explain why


class RoleRequestResponse(BaseModel):
    id          : UUID
    user_id     : UUID
    shop_name   : str
    shop_address: str
    phone       : str
    reason      : Optional[str]
    status      : RequestStatus
    admin_note  : Optional[str]
    create_at   : datetime

    class Config:
        orm_mode = True

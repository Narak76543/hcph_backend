from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class CompatibilityRuleCreate(BaseModel):
    laptop_model_id: UUID
    part_id        : UUID
    is_compatible  : bool         = True
    notes          : Optional[str] = None


class CompatibilityRuleUpdate(BaseModel):
    is_compatible: Optional[bool] = None
    notes        : Optional[str]  = None


class CompatibilityRuleResponse(BaseModel):
    id             : UUID
    laptop_model_id: UUID
    part_id        : UUID
    is_compatible  : bool
    notes          : Optional[str]
    verify_by      : Optional[UUID]

    class Config:
        orm_mode = True
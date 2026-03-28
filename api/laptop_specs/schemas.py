from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class LaptopSpecCreate(BaseModel):
    model_id          : UUID
    ram_slots         : Optional[int]  = None
    ram_type          : Optional[str]  = None
    max_ram_gg        : Optional[int]  = None
    ram_base_gb       : Optional[int]  = None
    ssd_slots         : Optional[int]  = None
    ssd_interface     : Optional[str]  = None
    ssd_from_factor   : Optional[str]  = None
    has_hdd_bay       : Optional[bool] = False
    display_size      : Optional[str]  = None
    display_resolution: Optional[str]  = None


class LaptopSpecUpdate(BaseModel):
    ram_slots         : Optional[int]  = None
    ram_type          : Optional[str]  = None
    max_ram_gg        : Optional[int]  = None
    ram_base_gb       : Optional[int]  = None
    ssd_slots         : Optional[int]  = None
    ssd_interface     : Optional[str]  = None
    ssd_from_factor   : Optional[str]  = None
    has_hdd_bay       : Optional[bool] = None
    display_size      : Optional[str]  = None
    display_resolution: Optional[str]  = None


class LaptopSpecResponse(BaseModel):
    id                : UUID
    model_id          : UUID
    ram_slots         : Optional[int]
    ram_type          : Optional[str]
    max_ram_gg        : Optional[int]
    ram_base_gb       : Optional[int]
    ssd_slots         : Optional[int]
    ssd_interface     : Optional[str]
    ssd_from_factor   : Optional[str]
    has_hdd_bay       : Optional[bool]
    display_size      : Optional[str]
    display_resolution: Optional[str]

    class Config:
        orm_mode = True
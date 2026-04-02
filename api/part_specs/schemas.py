from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from api.part_specs.models import (
    RamType, RamFormFactor,
    SSDType, SSDFormFactor, SSDInterface,
    HDDFormFactor, BatteryType, PanelType,
    ChargerConnector, ChargerStandard,
    FanConnector, FanType, ThermalType
)


# ram schemas 
class RAMSpecCreate(BaseModel):
    part_id    : UUID
    ram_type   : RamType
    capacity_gb: int
    bus_mhz    : int
    form_factor: RamFormFactor
    latency    : Optional[str] = None

class RAMSpecResponse(RAMSpecCreate):
    id: UUID
    class Config:
        orm_mode = True

# ssd schemas
class SSDSpecCreate(BaseModel):
    part_id    : UUID
    ssd_type   : SSDType
    capacity_gb: int
    form_factor: SSDFormFactor
    interface  : SSDInterface
    read_speed : Optional[int] = None
    write_speed: Optional[int] = None

class SSDSpecResponse(SSDSpecCreate):
    id: UUID
    class Config:
        orm_mode = True


# hhd schemas
class HDDSpecCreate(BaseModel):
    part_id    : UUID
    capacity_gb: int
    rpm        : int
    form_factor: HDDFormFactor
    cache_mb   : Optional[int] = None

class HDDSpecResponse(HDDSpecCreate):
    id: UUID
    class Config:
        orm_mode = True

# battery schemas
class BatterySpecCreate(BaseModel):
    part_id       : UUID
    capacity_wh   : float
    capacity_mah  : Optional[int]   = None
    cells         : Optional[int]   = None
    voltage       : Optional[float] = None
    battery_type  : Optional[BatteryType] = None
    connector_type: Optional[str]   = None

class BatterySpecResponse(BatterySpecCreate):
    id: UUID
    class Config:
        orm_mode = True

# display schemas
class DisplaySpecCreate(BaseModel):
    part_id       : UUID
    size_inch     : float
    resolution    : str
    refresh_rate  : int
    panel_type    : PanelType
    connector_pin : Optional[str] = None
    brightness_nit: Optional[int] = None

class DisplaySpecResponse(DisplaySpecCreate):
    id: UUID
    class Config:
        orm_mode = True

# charger or power adapter schemas
class ChargerSpecCreate(BaseModel):
    part_id       : UUID
    wattage       : int
    voltage       : Optional[float] = None
    connector_type: ChargerConnector
    standard      : Optional[ChargerStandard] = None

class ChargerSpecResponse(ChargerSpecCreate):
    id: UUID
    class Config:
        orm_mode = True

# cooling fan schemas
class FanSpecCreate(BaseModel):
    part_id  : UUID
    size_mm  : int
    connector: FanConnector
    max_rpm  : Optional[int] = None
    fan_type : FanType

class FanSpecResponse(FanSpecCreate):
    id: UUID
    class Config:
        orm_mode = True

# thermal pase schemas
class ThermalSpecCreate(BaseModel):
    part_id         : UUID
    conductivity_wm : Optional[float] = None
    thermal_type    : Optional[ThermalType] = None
    weight_g        : Optional[float] = None

class ThermalSpecResponse(ThermalSpecCreate):
    id: UUID
    class Config:
        orm_mode = True

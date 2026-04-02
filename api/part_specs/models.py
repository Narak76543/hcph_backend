import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import Base
import enum

# ram
class RamType(str, enum.Enum):
    DDR4   = "DDR4"
    DDR5   = "DDR5"
    LPDDR5 = "LPDDR5"

class RamFormFactor(str, enum.Enum):
    DIMM    = "DIMM"
    SO_DIMM = "SO-DIMM"

class PartSpecRAM(Base):
    __tablename__ = "TBL_PART_SPEC_RAM"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id     = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"), unique=True, nullable=False)
    ram_type    = Column(Enum(RamType),        nullable=False)
    capacity_gb = Column(Integer,              nullable=False)   # 4 / 8 / 16 / 32 / 64
    bus_mhz     = Column(Integer,              nullable=False)   # 3200 / 3600 / 4800 / 5600 / 6000
    form_factor = Column(Enum(RamFormFactor),  nullable=False)
    latency     = Column(String(20),           nullable=True)    # CL16 / CL18 / CL32 / CL36

    part = relationship("Part", backref="spec_ram")

#  ssd 
class SSDType(str, enum.Enum):
    NVMe = "NVMe"
    SATA = "SATA"

class SSDFormFactor(str, enum.Enum):
    M2_2280 = "M.2 2280"
    M2_2242 = "M.2 2242"
    INCH_25 = '2.5"'

class SSDInterface(str, enum.Enum):
    PCIe_3 = "PCIe 3.0"
    PCIe_4 = "PCIe 4.0"
    PCIe_5 = "PCIe 5.0"
    SATA_3 = "SATA III"

class PartSpecSSD(Base):
    __tablename__ = "TBL_PART_SPEC_SSD"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id      = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"), unique=True, nullable=False)
    ssd_type     = Column(Enum(SSDType),        nullable=False)
    capacity_gb  = Column(Integer,              nullable=False)   # 256 / 512 / 1000 / 2000 / 4000
    form_factor  = Column(Enum(SSDFormFactor),  nullable=False)
    interface    = Column(Enum(SSDInterface),   nullable=False)
    read_speed   = Column(Integer,              nullable=True)    # MB/s
    write_speed  = Column(Integer,              nullable=True)    # MB/s

    part = relationship("Part", backref="spec_ssd")

# hhd
class HDDFormFactor(str, enum.Enum):
    INCH_25 = '2.5"'
    INCH_35 = '3.5"'

class PartSpecHDD(Base):
    __tablename__ = "TBL_PART_SPEC_HDD"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id     = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"), unique=True, nullable=False)
    capacity_gb = Column(Integer,             nullable=False)
    rpm         = Column(Integer,             nullable=False)    # 5400 / 7200
    form_factor = Column(Enum(HDDFormFactor), nullable=False)
    cache_mb    = Column(Integer,             nullable=True)     # 32 / 64 / 128 / 256

    part = relationship("Part", backref="spec_hdd")

# battery
class BatteryType(str, enum.Enum):
    Li_ion     = "Li-ion"
    Li_polymer = "Li-polymer"

class PartSpecBattery(Base):
    __tablename__ = "TBL_PART_SPEC_BATTERY"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id        = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"), unique=True, nullable=False)
    capacity_wh    = Column(Float,               nullable=False)
    capacity_mah   = Column(Integer,             nullable=True)
    cells          = Column(Integer,             nullable=True)    # 3 / 4 / 6
    voltage        = Column(Float,               nullable=True)    # 10.8 / 11.1 / 14.4 / 15.2
    battery_type   = Column(Enum(BatteryType),   nullable=True)
    connector_type = Column(String(100),         nullable=True)    # model specific

    part = relationship("Part", backref="spec_battery")

# display
class PanelType(str, enum.Enum):
    IPS  = "IPS"
    TN   = "TN"
    VA   = "VA"
    OLED = "OLED"

class PartSpecDisplay(Base):
    __tablename__ = "TBL_PART_SPEC_DISPLAY"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id        = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"), unique=True, nullable=False)
    size_inch      = Column(Float,             nullable=False)    # 13.6 / 14 / 15.6 / 16 / 17.3
    resolution     = Column(String(20),        nullable=False)    # 1920x1080 / 2560x1600
    refresh_rate   = Column(Integer,           nullable=False)    # 60 / 120 / 144 / 165 / 240
    panel_type     = Column(Enum(PanelType),   nullable=False)
    connector_pin  = Column(String(20),        nullable=True)     # eDP 30-pin / 40-pin
    brightness_nit = Column(Integer,           nullable=True)

    part = relationship("Part", backref="spec_display")

# charger or power adapter
class ChargerConnector(str, enum.Enum):
    USB_C       = "USB-C"
    Barrel      = "Barrel"
    Proprietary = "Proprietary"

class ChargerStandard(str, enum.Enum):
    GaN         = "GaN"
    Traditional = "Traditional"

class PartSpecCharger(Base):
    __tablename__ = "TBL_PART_SPEC_CHARGER"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id        = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"), unique=True, nullable=False)
    wattage        = Column(Integer,                  nullable=False)   # 45/65/90/120/180/240
    voltage        = Column(Float,                    nullable=True)    # 19V / 20V
    connector_type = Column(Enum(ChargerConnector),   nullable=False)
    standard       = Column(Enum(ChargerStandard),    nullable=True)

    part = relationship("Part", backref="spec_charger")

# cooling fan 
class FanConnector(str, enum.Enum):
    pin_3 = "3-pin"
    pin_4 = "4-pin"

class FanType(str, enum.Enum):
    CPU    = "CPU"
    GPU    = "GPU"
    Laptop = "Laptop"

class PartSpecFan(Base):
    __tablename__ = "TBL_PART_SPEC_FAN"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id    = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"), unique=True, nullable=False)
    size_mm    = Column(Integer,           nullable=False)   # 40 / 60 / 80 / laptop specific
    connector  = Column(Enum(FanConnector), nullable=False)
    max_rpm    = Column(Integer,           nullable=True)
    fan_type   = Column(Enum(FanType),     nullable=False)

    part = relationship("Part", backref="spec_fan")

# thermal pase
class ThermalType(str, enum.Enum):
    metal   = "Metal"
    ceramic = "Ceramic"
    carbon  = "Carbon"

class PartSpecThermal(Base):
    __tablename__ = "TBL_PART_SPEC_THERMAL"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id          = Column(UUID(as_uuid=True), ForeignKey("TBL_PART.id"), unique=True, nullable=False)
    conductivity_wm  = Column(Float,              nullable=True)    # W/mK
    thermal_type     = Column(Enum(ThermalType),  nullable=True)
    weight_g         = Column(Float,              nullable=True)    # 1 / 2 / 4

    part = relationship("Part", backref="spec_thermal")
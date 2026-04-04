import uuid
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from core.db import Base


class LaptopSpec(Base):
    __tablename__ = "TBL_LAPTOP_SPECE"   # keeping your exact table name

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id           = Column(UUID(as_uuid=True), ForeignKey("TBL_LAPTOP_MODELS.id"), unique=True, nullable=False)
    ram_slots          = Column(Integer,     nullable=True)
    ram_type           = Column(String(20),  nullable=True)   # e.g. DDR4, DDR5
    max_ram_gg         = Column(Integer,     nullable=True)   # max RAM in GB
    ram_base_gb        = Column(Integer,     nullable=True)   # factory RAM
    ssd_slots          = Column(Integer,     nullable=True)
    ssd_interface      = Column(String(50),  nullable=True)   # e.g. NVMe, SATA
    ssd_from_factor    = Column(String(50),  nullable=True)   # e.g. M.2, 2.5"
    has_hdd_bay        = Column(Boolean,     default=False)
    display_size       = Column(String(20),  nullable=True)   # e.g. 15.6"
    display_resolution = Column(String(50),  nullable=True)   # e.g. 1920x1080

    laptop_model = relationship("LaptopModel", back_populates="spec")
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from api.part.models import Part
from api.part_specs.models import PartSpecBattery, PartSpecCharger, PartSpecDisplay, PartSpecFan, PartSpecHDD, PartSpecRAM, PartSpecSSD, PartSpecThermal
from core.db import get_db
from core.security import require_technical, require_admin

from api.part_specs.schemas import (
    RAMSpecCreate, RAMSpecResponse,
    SSDSpecCreate, SSDSpecResponse,
    HDDSpecCreate, HDDSpecResponse,
    BatterySpecCreate, BatterySpecResponse,
    DisplaySpecCreate, DisplaySpecResponse,
    ChargerSpecCreate, ChargerSpecResponse,
    FanSpecCreate, FanSpecResponse,
    ThermalSpecCreate, ThermalSpecResponse,
)
# for query part 
def _get_part_or_404(db, part_id):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(404, "Part not found")
    return part


def _payload_to_dict(payload):
    return payload.dict() if hasattr(payload, "dict") else payload.model_dump()


# for create spec
def _create_spec(db, model, payload_dict):
    spec = model(**payload_dict)
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec

# register route function
def register_part_spec_routes(app):

    # in ram part 
    @app.post("/part-specs/ram/", response_model=RAMSpecResponse, status_code=201, tags=["Ram"])
    def add_ram_spec(
        payload: RAMSpecCreate,
        db     : Session = Depends(get_db),
        _ = Depends(require_technical)
    ):
        _get_part_or_404(db, payload.part_id)
        if db.query(PartSpecRAM).filter(PartSpecRAM.part_id == payload.part_id).first():
            raise HTTPException(400, "RAM spec already exists for this part")
        return _create_spec(db, PartSpecRAM, _payload_to_dict(payload))

    @app.get("/part-specs/ram/{part_id}", response_model=RAMSpecResponse, tags=["Ram"])
    def get_ram_spec(
        part_id: UUID,
        db     : Session = Depends(get_db)
    ):
        spec = db.query(PartSpecRAM).filter(PartSpecRAM.part_id == part_id).first()
        if not spec:
            raise HTTPException(404, "RAM spec not found")
        return spec

    @app.get("/part-specs/ram/", response_model=list[RAMSpecResponse], tags=["Ram"])
    def get_all_ram_specs(
        ram_type   : str  | None = None,
        capacity_gb: int  | None = None,
        bus_mhz    : int  | None = None,
        form_factor: str  | None = None,
        db: Session = Depends(get_db)
    ):
        query = db.query(PartSpecRAM)
        if ram_type:    query = query.filter(PartSpecRAM.ram_type    == ram_type.upper())
        if capacity_gb: query = query.filter(PartSpecRAM.capacity_gb == capacity_gb)
        if bus_mhz:     query = query.filter(PartSpecRAM.bus_mhz     == bus_mhz)
        if form_factor: query = query.filter(PartSpecRAM.form_factor  == form_factor)
        return query.all()

    # in ssd part
    @app.post("/part-specs/ssd/", response_model=SSDSpecResponse, status_code=201, tags=["SSD"])
    def add_ssd_spec(
        payload: SSDSpecCreate,
        db     : Session = Depends(get_db),
        _ = Depends(require_technical)
    ):
        _get_part_or_404(db, payload.part_id)
        if db.query(PartSpecSSD).filter(PartSpecSSD.part_id == payload.part_id).first():
            raise HTTPException(400, "SSD spec already exists for this part")
        return _create_spec(db, PartSpecSSD, _payload_to_dict(payload))

    @app.get("/part-specs/ssd/{part_id}", response_model=SSDSpecResponse, tags=["SSD"])
    def get_ssd_spec(
        part_id: UUID,
        db     : Session = Depends(get_db)
    ):
        spec = db.query(PartSpecSSD).filter(PartSpecSSD.part_id == part_id).first()
        if not spec:
            raise HTTPException(404, "SSD spec not found")
        return spec

    @app.get("/part-specs/ssd/", response_model=list[SSDSpecResponse], tags=["SSD"])
    def get_all_ssd_specs(
        ssd_type   : str  | None = None,
        capacity_gb: int  | None = None,
        interface  : str  | None = None,
        form_factor: str  | None = None,
        db: Session = Depends(get_db)
    ):
        query = db.query(PartSpecSSD)
        if ssd_type:    query = query.filter(PartSpecSSD.ssd_type    == ssd_type.upper())
        if capacity_gb: query = query.filter(PartSpecSSD.capacity_gb == capacity_gb)
        if interface:   query = query.filter(PartSpecSSD.interface    == interface)
        if form_factor: query = query.filter(PartSpecSSD.form_factor  == form_factor)
        return query.all()

    # in hhd part
    @app.post("/part-specs/hdd/", response_model=HDDSpecResponse, status_code=201, tags=["HDD"])
    def add_hdd_spec(
        payload: HDDSpecCreate,
        db     : Session = Depends(get_db),
        _ = Depends(require_technical)
    ):
        _get_part_or_404(db, payload.part_id)
        if db.query(PartSpecHDD).filter(PartSpecHDD.part_id == payload.part_id).first():
            raise HTTPException(400, "HDD spec already exists for this part")
        return _create_spec(db, PartSpecHDD, _payload_to_dict(payload))

    @app.get("/part-specs/hdd/{part_id}", response_model=HDDSpecResponse, tags=["HHD"])
    def get_hdd_spec(
        part_id: UUID,
        db     : Session = Depends(get_db)
    ):
        spec = db.query(PartSpecHDD).filter(PartSpecHDD.part_id == part_id).first()
        if not spec:
            raise HTTPException(404, "HDD spec not found")
        return spec

    
    # in battery part
    @app.post("/part-specs/battery/", response_model=BatterySpecResponse, status_code=201, tags=["HHD"])
    def add_battery_spec(
        payload: BatterySpecCreate,
        db     : Session = Depends(get_db),
        _=Depends(require_technical)
    ):
        _get_part_or_404(db, payload.part_id)
        if db.query(PartSpecBattery).filter(PartSpecBattery.part_id == payload.part_id).first():
            raise HTTPException(400, "Battery spec already exists for this part")
        return _create_spec(db, PartSpecBattery, _payload_to_dict(payload))

    @app.get("/part-specs/battery/{part_id}", response_model=BatterySpecResponse, tags=["HHD"])
    def get_battery_spec(part_id: UUID, db: Session = Depends(get_db)):
        spec = db.query(PartSpecBattery).filter(PartSpecBattery.part_id == part_id).first()
        if not spec:
            raise HTTPException(404, "Battery spec not found")
        return spec

    # in display part
    @app.post("/part-specs/display/", response_model=DisplaySpecResponse, status_code=201, tags=["Display"])
    def add_display_spec(
        payload: DisplaySpecCreate,
        db     : Session = Depends(get_db),
        _ = Depends(require_technical)
    ):
        _get_part_or_404(db, payload.part_id)
        if db.query(PartSpecDisplay).filter(PartSpecDisplay.part_id == payload.part_id).first():
            raise HTTPException(400, "Display spec already exists for this part")
        return _create_spec(db, PartSpecDisplay, _payload_to_dict(payload))

    @app.get("/part-specs/display/{part_id}", response_model=DisplaySpecResponse, tags=["Display"])
    def get_display_spec(
        part_id: UUID,
        db     : Session = Depends(get_db)
    ):
        spec = db.query(PartSpecDisplay).filter(PartSpecDisplay.part_id == part_id).first()
        if not spec:
            raise HTTPException(404, "Display spec not found")
        return spec

    @app.get("/part-specs/display/", response_model=list[DisplaySpecResponse], tags=["Display"])
    def get_all_display_specs(
        size_inch   : float | None = None,
        refresh_rate: int   | None = None,
        panel_type  : str   | None = None,
        db: Session = Depends(get_db)
    ):
        query = db.query(PartSpecDisplay)
        if size_inch:    query = query.filter(PartSpecDisplay.size_inch    == size_inch)
        if refresh_rate: query = query.filter(PartSpecDisplay.refresh_rate == refresh_rate)
        if panel_type:   query = query.filter(PartSpecDisplay.panel_type   == panel_type.upper())
        return query.all()

    # in charger part
    @app.post("/part-specs/charger/", response_model=ChargerSpecResponse, status_code=201, tags=["Charger"])
    def add_charger_spec(payload: ChargerSpecCreate, db: Session = Depends(get_db), _=Depends(require_technical)):
        _get_part_or_404(db, payload.part_id)
        if db.query(PartSpecCharger).filter(PartSpecCharger.part_id == payload.part_id).first():
            raise HTTPException(400, "Charger spec already exists for this part")
        return _create_spec(db, PartSpecCharger, _payload_to_dict(payload))

    @app.get("/part-specs/charger/{part_id}", response_model=ChargerSpecResponse, tags=["Charger"])
    def get_charger_spec(part_id: UUID, db: Session = Depends(get_db)):
        spec = db.query(PartSpecCharger).filter(PartSpecCharger.part_id == part_id).first()
        if not spec:
            raise HTTPException(404, "Charger spec not found")
        return spec

    # in cooling fan part 
    @app.post("/part-specs/fan/", response_model=FanSpecResponse, status_code=201, tags=["Cooling Fan"])
    def add_fan_spec(payload: FanSpecCreate, db: Session = Depends(get_db), _=Depends(require_technical)):
        _get_part_or_404(db, payload.part_id)
        if db.query(PartSpecFan).filter(PartSpecFan.part_id == payload.part_id).first():
            raise HTTPException(400, "Fan spec already exists for this part")
        return _create_spec(db, PartSpecFan, _payload_to_dict(payload))

    @app.get("/part-specs/fan/{part_id}", response_model=FanSpecResponse, tags=["Cooling Fan"])
    def get_fan_spec(part_id: UUID, db: Session = Depends(get_db)):
        spec = db.query(PartSpecFan).filter(PartSpecFan.part_id == part_id).first()
        if not spec:
            raise HTTPException(404, "Fan spec not found")
        return spec

    # in thermal pase part
    @app.post("/part-specs/thermal/", response_model=ThermalSpecResponse, status_code=201, tags=["Thermal"])
    def add_thermal_spec(payload: ThermalSpecCreate, db: Session = Depends(get_db), _=Depends(require_technical)):
        _get_part_or_404(db, payload.part_id)
        if db.query(PartSpecThermal).filter(PartSpecThermal.part_id == payload.part_id).first():
            raise HTTPException(400, "Thermal spec already exists for this part")
        return _create_spec(db, PartSpecThermal, _payload_to_dict(payload))

    @app.get("/part-specs/thermal/{part_id}", response_model=ThermalSpecResponse, tags=["Thermal"])
    def get_thermal_spec(part_id: UUID, db: Session = Depends(get_db)):
        spec = db.query(PartSpecThermal).filter(PartSpecThermal.part_id == part_id).first()
        if not spec:
            raise HTTPException(404, "Thermal spec not found")
        return spec

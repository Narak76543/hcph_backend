from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from core.db import get_db
from core.security import get_current_user, require_technical
from api.laptop_specs.models import LaptopSpec
from api.laptop_specs.schemas import LaptopSpecCreate, LaptopSpecUpdate, LaptopSpecResponse
from api.laptop_models.models import LaptopModel


def register_laptop_spec_routes(app):

    # ── CREATE (admin only) ────────────────────────────────────────────────

    @app.post("/laptop-specs/", response_model=LaptopSpecResponse, status_code=201, tags=["Laptop Specs"])
    def create_spec(
        payload: LaptopSpecCreate,
        db     : Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        # validate model exists
        if not db.query(LaptopModel).filter(LaptopModel.id == payload.model_id).first():
            raise HTTPException(404, "Laptop model not found")

        # one spec per model only
        if db.query(LaptopSpec).filter(LaptopSpec.model_id == payload.model_id).first():
            raise HTTPException(400, "Spec already exists for this laptop model")

        spec = LaptopSpec(**payload.dict())
        db.add(spec)
        db.commit()
        db.refresh(spec)
        return spec


    # ── GET ALL (public) ───────────────────────────────────────────────────

    @app.get("/laptop-specs/", response_model=list[LaptopSpecResponse], tags=["Laptop Specs"])
    def get_all_specs(
        skip : int     = 0,
        limit: int     = 20,
        db   : Session = Depends(get_db),
    ):
        return db.query(LaptopSpec).offset(skip).limit(limit).all()


    # ── GET BY MODEL ID (public) ⭐ most used ──────────────────────────────

    @app.get("/laptop-specs/model/{model_id}", response_model=LaptopSpecResponse, tags=["Laptop Specs"])
    def get_spec_by_model(
        model_id: UUID,
        db      : Session = Depends(get_db),
    ):
        spec = db.query(LaptopSpec).filter(LaptopSpec.model_id == model_id).first()
        if not spec:
            raise HTTPException(404, "No spec found for this laptop model")
        return spec


    # ── GET ONE BY SPEC ID (public) ────────────────────────────────────────

    @app.get("/laptop-specs/{spec_id}", response_model=LaptopSpecResponse, tags=["Laptop Specs"])
    def get_one_spec(
        spec_id: UUID,
        db     : Session = Depends(get_db),
    ):
        spec = db.query(LaptopSpec).filter(LaptopSpec.id == spec_id).first()
        if not spec:
            raise HTTPException(404, "Spec not found")
        return spec


    # ── UPDATE (admin only) ────────────────────────────────────────────────

    @app.patch("/laptop-specs/{spec_id}", response_model=LaptopSpecResponse, tags=["Laptop Specs"])
    def update_spec(
        spec_id: UUID,
        payload: LaptopSpecUpdate,
        db     : Session = Depends(get_db),
        _=Depends(require_technical),
    ):
        spec = db.query(LaptopSpec).filter(LaptopSpec.id == spec_id).first()
        if not spec:
            raise HTTPException(404, "Spec not found")
        for field, value in payload.dict(exclude_none=True).items():
            setattr(spec, field, value)
        db.commit()
        db.refresh(spec)
        return spec


    # ── DELETE (admin only) ────────────────────────────────────────────────

    @app.delete("/laptop-specs/{spec_id}", status_code=204, tags=["Laptop Specs"])
    def delete_spec(
        spec_id: UUID,
        db     : Session = Depends(get_db),
        _=Depends(require_technical),
    ):
        spec = db.query(LaptopSpec).filter(LaptopSpec.id == spec_id).first()
        if not spec:
            raise HTTPException(404, "Spec not found")
        db.delete(spec)
        db.commit()
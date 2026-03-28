from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from api.part.models import Part
from api.part.schemas import PartCreate, PartResponse, PartUpdate
from api.part_category.models import PartCategory
from core.app import app
from core.db import get_db
from core.security import require_admin, require_technical


# ── CREATE (technical + admin) ─────────────────────────────────────────

@app.post("/parts/", response_model=PartResponse, status_code=201, tags=["Parts"])
def create_part(
    payload: PartCreate,
    db: Session = Depends(get_db),
    _=Depends(require_technical),
):
    # validate category exists
    category = db.query(PartCategory).filter(PartCategory.id == payload.category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")

    part = Part(
        category_id   = payload.category_id,
        brand         = payload.brand,
        model_name    = payload.model_name,
        specification = payload.specification,
        img_url       = payload.img_url,
    )
    db.add(part)
    db.commit()
    db.refresh(part)
    return part


# ── GET ALL (public) ───────────────────────────────────────────────────

@app.get("/parts/", response_model=list[PartResponse], tags=["Parts"])
def get_all_parts(
    skip       : int         = 0,
    limit      : int         = 20,
    category_id: UUID | None = None,
    brand      : str | None  = None,
    db         : Session     = Depends(get_db),
):
    query = db.query(Part)
    if category_id:
        query = query.filter(Part.category_id == category_id)
    if brand:
        query = query.filter(Part.brand.ilike(f"%{brand}%"))
    return query.order_by(Part.create_at.desc()).offset(skip).limit(limit).all()


# ── GET ONE (public) ───────────────────────────────────────────────────

@app.get("/parts/{part_id}", response_model=PartResponse, tags=["Parts"])
def get_one_part(
    part_id: UUID,
    db     : Session = Depends(get_db),
):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(404, "Part not found")
    return part


# ── UPDATE (technical + admin) ─────────────────────────────────────────

@app.patch("/parts/{part_id}", response_model=PartResponse, tags=["Parts"])
def update_part(
    part_id: UUID,
    payload: PartUpdate,
    db     : Session = Depends(get_db),
    _=Depends(require_technical),
):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(404, "Part not found")

    if payload.category_id   is not None:
        category = db.query(PartCategory).filter(PartCategory.id == payload.category_id).first()
        if not category:
            raise HTTPException(404, "Category not found")
        part.category_id = payload.category_id
    if payload.brand         is not None: part.brand         = payload.brand
    if payload.model_name    is not None: part.model_name    = payload.model_name
    if payload.specification is not None: part.specification = payload.specification
    if payload.img_url       is not None: part.img_url       = payload.img_url

    db.commit()
    db.refresh(part)
    return part


# ── DELETE (admin only) ────────────────────────────────────────────────

@app.delete("/parts/{part_id}", status_code=204, tags=["Parts"])
def delete_part(
    part_id: UUID,
    db     : Session = Depends(get_db),
    _=Depends(require_admin),
):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(404, "Part not found")
    db.delete(part)
    db.commit()
    return None
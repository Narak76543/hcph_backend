from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from core.db import get_db
from core.security import get_current_user, require_technical, require_admin
from api.laptop_sub_brands.models import LaptopSubBrand
from api.laptop_sub_brands.schemas import (
    LaptopSubBrandCreate,
    LaptopSubBrandUpdate,
    LaptopSubBrandResponse,
)
from api.laptop_brands.models import LaptopBrand


def register_laptop_sub_brand_routes(app):

    # ── CREATE (admin only) ───────────────────────────────────────────────

    @app.post("/laptop-sub-brands/", response_model=LaptopSubBrandResponse, status_code=201, tags=["Laptop Sub-Brands"])
    def create_sub_brand(
        payload: LaptopSubBrandCreate,
        db: Session = Depends(get_db),
        _=Depends(require_admin),
    ):
        if not db.query(LaptopBrand).filter(LaptopBrand.id == payload.brand_id).first():
            raise HTTPException(404, "Brand not found")
        if db.query(LaptopSubBrand).filter(LaptopSubBrand.slug == payload.slug).first():
            raise HTTPException(400, "Slug already exists")

        sub_brand = LaptopSubBrand(**payload.dict())
        db.add(sub_brand)
        db.commit()
        db.refresh(sub_brand)
        return sub_brand

    # ── GET ALL (public, filterable by brand_id) ──────────────────────────

    @app.get("/laptop-sub-brands/", response_model=list[LaptopSubBrandResponse], tags=["Laptop Sub-Brands"])
    def get_all_sub_brands(
        brand_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
        db: Session = Depends(get_db),
    ):
        query = db.query(LaptopSubBrand)
        if brand_id:
            query = query.filter(LaptopSubBrand.brand_id == brand_id)
        return query.options(
            joinedload(LaptopSubBrand.brand)
        ).offset(skip).limit(limit).all()

    # ── GET ONE ───────────────────────────────────────────────────────────

    @app.get("/laptop-sub-brands/{sub_brand_id}", response_model=LaptopSubBrandResponse, tags=["Laptop Sub-Brands"])
    def get_one_sub_brand(sub_brand_id: UUID, db: Session = Depends(get_db)):
        sub_brand = db.query(LaptopSubBrand).filter(LaptopSubBrand.id == sub_brand_id).first()
        if not sub_brand:
            raise HTTPException(404, "Sub-brand not found")
        return sub_brand

    # ── UPDATE (admin only) ───────────────────────────────────────────────

    @app.patch("/laptop-sub-brands/{sub_brand_id}", response_model=LaptopSubBrandResponse, tags=["Laptop Sub-Brands"])
    def update_sub_brand(
        sub_brand_id: UUID,
        payload: LaptopSubBrandUpdate,
        db: Session = Depends(get_db),
        _=Depends(require_admin),
    ):
        sub_brand = db.query(LaptopSubBrand).filter(LaptopSubBrand.id == sub_brand_id).first()
        if not sub_brand:
            raise HTTPException(404, "Sub-brand not found")
        for field, value in payload.dict(exclude_none=True).items():
            setattr(sub_brand, field, value)
        db.commit()
        db.refresh(sub_brand)
        return sub_brand

    # ── DELETE (admin only) ───────────────────────────────────────────────

    @app.delete("/laptop-sub-brands/{sub_brand_id}", status_code=204, tags=["Laptop Sub-Brands"])
    def delete_sub_brand(
        sub_brand_id: UUID,
        db: Session = Depends(get_db),
        _=Depends(require_admin),
    ):
        sub_brand = db.query(LaptopSubBrand).filter(LaptopSubBrand.id == sub_brand_id).first()
        if not sub_brand:
            raise HTTPException(404, "Sub-brand not found")
        db.delete(sub_brand)
        db.commit()

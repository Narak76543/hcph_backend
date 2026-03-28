from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from api.part_category.models import PartCategory
from api.part_category.schemas import PartCategoryCreate, PartCategoryResponse, PartCategoryUpdate
from core.app import app
from core.db import get_db
from core.security import require_admin


# ── CREATE (admin only) ────────────────────────────────────────────────

@app.post("/part-categories/", response_model=PartCategoryResponse, status_code=201, tags=["Part Categories"])
def create_category(
    payload: PartCategoryCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    if db.query(PartCategory).filter(PartCategory.slug == payload.slug).first():
        raise HTTPException(400, "Slug already exists")
    if db.query(PartCategory).filter(PartCategory.name == payload.name).first():
        raise HTTPException(400, "Category name already exists")

    category = PartCategory(name=payload.name, slug=payload.slug)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# ── GET ALL (public) ───────────────────────────────────────────────────

@app.get("/part-categories/", response_model=list[PartCategoryResponse], tags=["Part Categories"])
def get_all_categories(
    skip : int     = 0,
    limit: int     = 20,
    db   : Session = Depends(get_db),
):
    return db.query(PartCategory).offset(skip).limit(limit).all()


# ── GET ONE (public) ───────────────────────────────────────────────────

@app.get("/part-categories/{category_id}", response_model=PartCategoryResponse, tags=["Part Categories"])
def get_one_category(
    category_id: UUID,
    db: Session = Depends(get_db),
):
    category = db.query(PartCategory).filter(PartCategory.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")
    return category


# ── UPDATE (admin only) ────────────────────────────────────────────────

@app.patch("/part-categories/{category_id}", response_model=PartCategoryResponse, tags=["Part Categories"])
def update_category(
    category_id: UUID,
    payload    : PartCategoryUpdate,
    db         : Session = Depends(get_db),
    _=Depends(require_admin),
):
    category = db.query(PartCategory).filter(PartCategory.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")

    if payload.name is not None: category.name = payload.name
    if payload.slug is not None: category.slug = payload.slug

    db.commit()
    db.refresh(category)
    return category


# ── DELETE (admin only) ────────────────────────────────────────────────

@app.delete("/part-categories/{category_id}", status_code=204, tags=["Part Categories"])
def delete_category(
    category_id: UUID,
    db         : Session = Depends(get_db),
    _=Depends(require_admin),
):
    category = db.query(PartCategory).filter(PartCategory.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")
    db.delete(category)
    db.commit()
    return None
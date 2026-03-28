from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from core.db import get_db
from core.security import require_admin
from api.laptop_models.models import LaptopModel
from api.laptop_models.schemas import LaptopModelCreate, LaptopModelUpdate, LaptopModelResponse
from api.laptop_brands.models import LaptopBrand


def register_laptop_model_routes(app):

    @app.post("/laptop-models/", response_model=LaptopModelResponse, status_code=201, tags=["Laptop Models"])
    def create_model(payload: LaptopModelCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
        if not db.query(LaptopBrand).filter(LaptopBrand.id == payload.brand_id).first():
            raise HTTPException(404, "Brand not found")
        if db.query(LaptopModel).filter(LaptopModel.slug == payload.slug).first():
            raise HTTPException(400, "Slug already exists")
        model = LaptopModel(**payload.model_dump())
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @app.get("/laptop-models/", response_model=list[LaptopModelResponse], tags=["Laptop Models"])
    def get_all_models(
        brand_id    : UUID | None = None,
        release_year: int  | None = None,
        skip        : int         = 0,
        limit       : int         = 20,
        db          : Session     = Depends(get_db),
    ):
        query = db.query(LaptopModel)
        if brand_id:
            query = query.filter(LaptopModel.brand_id == brand_id)
        if release_year:
            query = query.filter(LaptopModel.release_year == release_year)
        return query.offset(skip).limit(limit).all()

    @app.get("/laptop-models/{model_id}", response_model=LaptopModelResponse, tags=["Laptop Models"])
    def get_one_model(model_id: UUID, db: Session = Depends(get_db)):
        model = db.query(LaptopModel).filter(LaptopModel.id == model_id).first()
        if not model:
            raise HTTPException(404, "Laptop model not found")
        return model

    @app.get("/laptop-models/slug/{slug}", response_model=LaptopModelResponse, tags=["Laptop Models"])
    def get_by_slug(slug: str, db: Session = Depends(get_db)):
        model = db.query(LaptopModel).filter(LaptopModel.slug == slug).first()
        if not model:
            raise HTTPException(404, "Laptop model not found")
        return model

    @app.patch("/laptop-models/{model_id}", response_model=LaptopModelResponse, tags=["Laptop Models"])
    def update_model(model_id: UUID, payload: LaptopModelUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
        model = db.query(LaptopModel).filter(LaptopModel.id == model_id).first()
        if not model:
            raise HTTPException(404, "Laptop model not found")
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        db.commit()
        db.refresh(model)
        return model

    @app.delete("/laptop-models/{model_id}", status_code=204, tags=["Laptop Models"])
    def delete_model(model_id: UUID, db: Session = Depends(get_db), _=Depends(require_admin)):
        model = db.query(LaptopModel).filter(LaptopModel.id == model_id).first()
        if not model:
            raise HTTPException(404, "Laptop model not found")
        db.delete(model)
        db.commit()
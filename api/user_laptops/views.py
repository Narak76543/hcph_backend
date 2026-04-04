from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from uuid import UUID

from api.compatibility_rule.models import CompatibilityRule
from core.db import get_db
from core.security import get_current_user
from api.user_laptops.models import UserLaptop
from api.user_laptops.schemas import UserLaptopCreate, UserLaptopUpdate, UserLaptopResponse
from api.laptop_models.models import LaptopModel


def register_user_laptop_routes(app):

    # ── ADD LAPTOP TO MY PROFILE ───────────────────────────────────────────

    @app.post("/my-laptops/", response_model=UserLaptopResponse, status_code=201, tags=["My Laptops"])
    def add_my_laptop(
        payload     : UserLaptopCreate,
        db          : Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        # validate model exists
        if not db.query(LaptopModel).filter(LaptopModel.id == payload.laptop_model_id).first():
            raise HTTPException(404, "Laptop model not found")

        # prevent duplicate same model for same user
        existing = db.query(UserLaptop).filter(
            UserLaptop.user_id         == current_user.id,
            UserLaptop.laptop_model_id == payload.laptop_model_id,
        ).first()
        if existing:
            raise HTTPException(400, "You already added this laptop to your profile")

        laptop = UserLaptop(
            user_id         = current_user.id,
            laptop_model_id = payload.laptop_model_id,
            nickname        = payload.nickname,
        )
        db.add(laptop)
        db.commit()
        db.refresh(laptop)
        return laptop


    # ── GET MY LAPTOPS ─────────────────────────────────────────────────────

    @app.get("/my-laptops/", response_model=list[UserLaptopResponse], tags=["My Laptops"])
    def get_my_laptops(
        db          : Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        return db.query(UserLaptop).options(
            joinedload(UserLaptop.laptop_model).joinedload(LaptopModel.spec)
        ).filter(UserLaptop.user_id == current_user.id).all()


    # ── GET ONE OF MY LAPTOPS ──────────────────────────────────────────────

    @app.get("/my-laptops/{laptop_id}", response_model=UserLaptopResponse, tags=["My Laptops"])
    def get_one_my_laptop(
        laptop_id   : UUID,
        db          : Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        laptop = db.query(UserLaptop).filter(
            UserLaptop.id      == laptop_id,
            UserLaptop.user_id == current_user.id,
        ).first()
        if not laptop:
            raise HTTPException(404, "Laptop not found")
        return laptop


    # ── UPDATE NICKNAME ────────────────────────────────────────────────────

    @app.patch("/my-laptops/{laptop_id}", response_model=UserLaptopResponse, tags=["My Laptops"])
    def update_my_laptop(
        laptop_id   : UUID,
        payload     : UserLaptopUpdate,
        db          : Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        laptop = db.query(UserLaptop).filter(
            UserLaptop.id      == laptop_id,
            UserLaptop.user_id == current_user.id,
        ).first()
        if not laptop:
            raise HTTPException(404, "Laptop not found")

        if payload.nickname is not None:
            laptop.nickname = payload.nickname

        db.commit()
        db.refresh(laptop)
        return laptop


    # ── REMOVE LAPTOP FROM PROFILE ─────────────────────────────────────────

    @app.delete("/my-laptops/{laptop_id}", status_code=204, tags=["My Laptops"])
    def delete_my_laptop(
        laptop_id   : UUID,
        db          : Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        laptop = db.query(UserLaptop).filter(
            UserLaptop.id      == laptop_id,
            UserLaptop.user_id == current_user.id,
        ).first()
        if not laptop:
            raise HTTPException(404, "Laptop not found")
        db.delete(laptop)
        db.commit()


    # ── CHECK COMPATIBILITY FOR MY LAPTOP ⭐ ──────────────────────────────

    @app.get("/my-laptops/{laptop_id}/check-part/", tags=["My Laptops"])
    def check_part_for_my_laptop(
        laptop_id   : UUID,
        part_id     : UUID,
        db          : Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        # get user's saved laptop
        my_laptop = db.query(UserLaptop).filter(
            UserLaptop.id      == laptop_id,
            UserLaptop.user_id == current_user.id,
        ).first()
        if not my_laptop:
            raise HTTPException(404, "Laptop not found in your profile")

        # check compatibility
        rule = db.query(CompatibilityRule).filter(
            CompatibilityRule.laptop_model_id == my_laptop.laptop_model_id,
            CompatibilityRule.part_id         == part_id,
        ).first()

        if not rule:
            return {
                "compatible": None,
                "message"   : "No compatibility data found for this part",
                "notes"     : None,
            }

        return {
            "compatible": rule.is_compatible,
            "message"   : "Compatible ✓" if rule.is_compatible else "Not compatible ✗",
            "notes"     : rule.notes,
        }
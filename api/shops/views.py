from uuid import UUID

from fastapi import Depends, Form, HTTPException
from sqlalchemy.orm import Session

from api.shops.models import Shop, ShopStatus
from api.shops.schemas import ShopResponse
from core.app import app
from core.db import get_db
from core.security import require_admin, require_technical


@app.post("/shops/", response_model=ShopResponse, status_code=201, tags=["Shops"])
def create_shop(
    name            : str        = Form(...),
    address         : str        = Form(...),
    phone           : str        = Form(...),
    telegram_handle : str | None = Form(None),
    shop_pro_img_url: str | None = Form(None),
    db     : Session = Depends(get_db),
    current_user=Depends(require_technical),
):
    if db.query(Shop).filter(Shop.owner_id == current_user.id).first():
        raise HTTPException(400, "You already have a registered shop")

    shop = Shop(
        owner_id         = current_user.id,
        name             = name,
        address          = address,
        phone            = phone,
        telegram_handle  = telegram_handle,
        shop_pro_img_url = shop_pro_img_url,
        status           = ShopStatus.pending,
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop

@app.get("/shops/", response_model=list[ShopResponse], tags=["Shops"])
def get_all_shops(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Shop).offset(skip).limit(limit).all()

@app.get("/shops/my-shop", response_model=ShopResponse, tags=["Shops"])
def get_my_shop(
    db: Session = Depends(get_db),
    current_user=Depends(require_technical),
):
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(404, "You don't have a shop yet")
    return shop

@app.get("/shops/{shop_id}", response_model=ShopResponse, tags=["Shops"])
def get_one_shop(shop_id: UUID, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(404, "Shop not found")
    return shop

@app.patch("/shops/{shop_id}", response_model=ShopResponse, tags=["Shops"])
def update_shop(
    shop_id: UUID,
    name            : str | None = Form(None),
    address         : str | None = Form(None),
    phone           : str | None = Form(None),
    telegram_handle : str | None = Form(None),
    shop_pro_img_url: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_technical),
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(404, "Shop not found")
    if shop.owner_id != current_user.id:
        raise HTTPException(403, "You can only update your own shop")

    if name is not None:
        shop.name = name
    if address is not None:
        shop.address = address
    if phone is not None:
        shop.phone = phone
    if telegram_handle is not None:
        shop.telegram_handle = telegram_handle
    if shop_pro_img_url is not None:
        shop.shop_pro_img_url = shop_pro_img_url

    db.commit()
    db.refresh(shop)
    return shop


@app.patch("/shops/{shop_id}/verify", response_model=ShopResponse, tags=["Shops"])
def verify_shop(
    shop_id: UUID,
    db     : Session = Depends(get_db),
    _=Depends(require_admin),
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(404, "Shop not found")
    if shop.status == ShopStatus.active:
        raise HTTPException(400, "Shop is already verified")

    shop.status = ShopStatus.active

    from api.users.models import User

    owner = db.query(User).filter(User.id == shop.owner_id).first()
    if owner:
        owner.is_verified = True

    db.commit()
    db.refresh(shop)
    return shop


@app.delete("/shops/{shop_id}", status_code=204, tags=["Shops"])
def delete_shop(
    shop_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(404, "Shop not found")
    db.delete(shop)
    db.commit()
    return None

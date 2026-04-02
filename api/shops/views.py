from uuid import UUID, uuid4
import shutil
from pathlib import Path
from typing import Optional

from fastapi import Depends, Form, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from api.shops.models import Shop, ShopStatus
from api.shops.schemas import ShopResponse, ShopCreate, ShopUpdate
from core.app import app
from core.db import get_db
from core.security import require_admin, require_technical

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHOP_IMAGE_DIR = PROJECT_ROOT / "media" / "shop_images"
SHOP_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

def _save_shop_image(file: UploadFile | None, request: Request) -> str | None:
    if file is None:
        return None
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Shop image must be an image file")
    ext = Path(file.filename or "").suffix.lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    if ext and ext not in allowed_exts:
        raise HTTPException(400, "Unsupported image format")
    filename = f"{uuid4()}{ext or '.jpg'}"
    destination = SHOP_IMAGE_DIR / filename
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    return str(request.url_for("media", path=f"shop_images/{filename}"))


@app.post("/shops/", response_model=ShopResponse, status_code=201, tags=["Shops"])
def create_shop(
    request         : Request,
    name            : str               = Form(...),
    phone           : str               = Form(...),
    telegram_handle : Optional[str]     = Form(None),
    province        : Optional[str]     = Form(None),
    district        : Optional[str]     = Form(None),
    detail          : Optional[str]     = Form(None),
    google_maps_url : Optional[str]     = Form(None),
    address         : Optional[str]     = Form(None),
    shop_pro_img    : UploadFile | None = File(None),
    db              : Session           = Depends(get_db),
    current_user    = Depends(require_technical),
):
    if db.query(Shop).filter(Shop.owner_id == current_user.id).first():
        raise HTTPException(400, "You already have a registered shop")

    shop_pro_img_url = _save_shop_image(shop_pro_img, request)
    
    # Auto-generate address if not provided
    if not address:
        parts = [detail, district, province]
        address = ", ".join([p for p in parts if p])

    shop = Shop(
        owner_id         = current_user.id,
        name             = name,
        phone            = phone,
        telegram_handle  = telegram_handle,
        province         = province,
        district         = district,
        detail           = detail,
        google_maps_url  = google_maps_url,
        address          = address,
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

@app.patch("/shops/me", response_model=ShopResponse, tags=["Shops"])
def update_shop_me(
    request         : Request,
    name            : Optional[str]     = Form(None),
    phone           : Optional[str]     = Form(None),
    telegram_handle : Optional[str]     = Form(None),
    province        : Optional[str]     = Form(None),
    district        : Optional[str]     = Form(None),
    detail          : Optional[str]     = Form(None),
    google_maps_url : Optional[str]     = Form(None),
    address         : Optional[str]     = Form(None),
    shop_pro_img    : UploadFile | None = File(None),
    db              : Session           = Depends(get_db),
    current_user    = Depends(require_technical),
):
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(404, "Shop not found")

    if name is not None:
        shop.name = name
    if phone is not None:
        shop.phone = phone
    if telegram_handle is not None:
        shop.telegram_handle = telegram_handle
    if province is not None:
        shop.province = province
    if district is not None:
        shop.district = district
    if detail is not None:
        shop.detail = detail
    if google_maps_url is not None:
        shop.google_maps_url = google_maps_url
    
    if any(x is not None for x in [province, district, detail]):
        parts = [shop.detail, shop.district, shop.province]
        shop.address = ", ".join([p for p in parts if p])
    elif address is not None:
        shop.address = address

    if shop_pro_img is not None:
        # Better to delete old one here if needed
        shop.shop_pro_img_url = _save_shop_image(shop_pro_img, request)

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

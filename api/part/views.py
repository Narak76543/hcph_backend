import json
from decimal import Decimal
from uuid import UUID
from fastapi import Depends, HTTPException, Request, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.part.hardware_utils import (
    create_hardware_spec,
    delete_part_image_file,
    get_category,
    parse_part_specs,
    save_part_image,
)
from api.part.models import Part
from api.part.schemas import PartCreate, PartResponse, PartUpdate
from api.part_category.models import PartCategory
from api.shop_listing.models import PartCondition, ShopListing
from api.shops.models import Shop
from core.app import app
from core.db import get_db
from core.security import require_admin, require_technical


def _pick_value(source: dict, *keys):
    for key in keys:
        value = source.get(key)
        if value is not None and value != "":
            return value
    return None


def _parse_category_inputs(source: dict):
    category_id = _pick_value(source, "category_id", "categoryId")
    category_slug = _pick_value(source, "category_slug", "categorySlug", "category", "hardware_type", "hardwareType")

    if category_id:
        try:
            return UUID(str(category_id)), category_slug
        except ValueError:
            return None, str(category_id)
    return None, category_slug


def _parse_condition(value: str | None) -> PartCondition:
    if value is None or value == "":
        return PartCondition.new
    normalized = str(value).strip().upper()
    try:
        return PartCondition(normalized)
    except ValueError as exc:
        raise HTTPException(422, f"Invalid condition: {value}") from exc


def _parse_decimal(value, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise HTTPException(422, f"{field_name} must be a valid decimal number") from exc


def _extract_part_specs(source: dict):
    direct_value = _pick_value(source, "part_specs", "partSpecs", "spec_data", "specData")
    if direct_value is not None:
        return parse_part_specs(direct_value)

    nested_specs = {}
    for key, value in source.items():
        if key.startswith("part_specs[") and key.endswith("]"):
            nested_specs[key[len("part_specs["):-1]] = value
        elif key.startswith("partSpecs[") and key.endswith("]"):
            nested_specs[key[len("partSpecs["):-1]] = value
        elif key.startswith("part_specs."):
            nested_specs[key[len("part_specs."):]] = value
        elif key.startswith("partSpecs."):
            nested_specs[key[len("partSpecs."):]] = value

    return nested_specs or None


# ── CREATE (technical + admin) 
@app.post("/parts/", response_model=PartResponse, status_code=201, tags=["Parts"])
async def create_part(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_technical),
):
    content_type = (request.headers.get("content-type") or "").lower()
    raw_payload: dict = {}
    uploaded_image: UploadFile | None = None

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        print(f"📥 Multipart form received with keys: {list(form.keys())}")
        
        # 🔧 Check form object DIRECTLY for UploadFile before converting to dict
        # Starlette form objects preserve UploadFile, but dict(form) doesn't
        for field_name in ["product_image", "part_image", "image", "img", "photo", "file", "img_url", "image_url", "imageUrl", "imgUrl"]:
            value = form.get(field_name)
            print(f"  Checking form.get('{field_name}'): {type(value).__name__} - {value if not hasattr(value, 'filename') else f'<UploadFile: {value.filename}>'}")
            # Check if it has file-like attributes (more robust than isinstance)
            if hasattr(value, 'filename') and hasattr(value, 'file'):
                print(f"✅ Found UploadFile in field: {field_name}")
                uploaded_image = value
                break
        
        # Now convert form to dict for text fields
        raw_payload = dict(form)
        print(f"📋 Converted form to dict with keys: {list(raw_payload.keys())}")
        
        # Remove UploadFile objects from raw_payload since they're in uploaded_image
        for k in list(raw_payload.keys()):
            if hasattr(raw_payload.get(k), 'filename'):
                print(f"  Removing UploadFile from dict: {k}")
                raw_payload.pop(k, None)
    else:
        try:
            raw_payload = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(400, f"Request body must be valid JSON: {exc.msg}") from exc
        if not isinstance(raw_payload, dict):
            raise HTTPException(400, "Request body must be a JSON object")

    category_id, category_slug = _parse_category_inputs(raw_payload)
    category = get_category(db, category_id, category_slug)

    # Robust field picking logic (Scanner)
    def _scan(source: dict, keys, aliases):
        for k in keys + list(aliases):
            val = source.get(k)
            if val is not None and val != "" and isinstance(val, str): return val
        # Last resort: scan keys for anything containing a URL
        for k, v in source.items():
            if isinstance(v, str) and v.startswith(("http://", "https://")):
                return v
        return None

    try:
        part_payload = PartCreate.parse_obj({
            "category_id"  : category.id,
            "brand"        : _pick_value(raw_payload, "brand", "brandName", "part_brand", "partBrand"),
            "model_name"   : _pick_value(raw_payload, "model_name", "modelName", "part_model", "partModel"),
            "specification": _pick_value(raw_payload, "specification", "summary", "description", "details"),
            "img_url"      : _scan(raw_payload, ["img_url", "image_url", "imageUrl", "imgUrl", "product_image"], ["part_image", "product_img_url", "part_img_url", "image", "img", "photo", "file", "thumbnail", "image_link", "img_link", "link", "url"]),
        })
    except ValidationError as exc:
        raise HTTPException(422, exc.errors()) from exc

    raw_part_specs = _extract_part_specs(raw_payload)
    raw_price = _pick_value(raw_payload, "price")
    raw_stock_quantity = _pick_value(raw_payload, "stock_quantity", "stockQuantity")
    raw_condition = _pick_value(raw_payload, "condition")
    # Always create a listing when a technical posts a part; missing values default to 0/new.
    wants_listing = True

    print(f"📋 Payload keys: {list(raw_payload.keys())}")
    print(f"📁 Uploaded image detected: {uploaded_image is not None}")
    if uploaded_image is not None:
        print(f"📁 File info - name: {uploaded_image.filename}, type: {uploaded_image.content_type}")
    
    image_url = part_payload.img_url
    print(f"📸 Initial img_url from payload: {image_url}")
    
    if uploaded_image is not None:
        print(f"💾 Calling save_part_image...")
        image_url = save_part_image(uploaded_image, request)
        print(f"💾 After save_part_image, image_url: {image_url}")
    else:
        print(f"⚠️  No uploaded_image found in request")

    try:
        part = Part(
            category_id   = category.id,
            brand         = part_payload.brand,
            model_name    = part_payload.model_name,
            specification = part_payload.specification,
            img_url       = image_url,
        )
        db.add(part)
        db.flush()

        create_hardware_spec(db, category, part.id, raw_part_specs)

        if wants_listing:
            shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
            if not shop:
                raise HTTPException(404, "You don't have a shop yet")
            if shop.status != "ACTIVE":
                raise HTTPException(403, "Your shop is not verified yet")

            listing = ShopListing(
                shop_id        = shop.id,
                part_id        = part.id,
                price          = _parse_decimal(raw_price if raw_price is not None else 0, "price"),
                stock_quantity = int(raw_stock_quantity) if raw_stock_quantity is not None else 1,
                condition      = _parse_condition(raw_condition),
            )
            db.add(listing)

        db.commit()
        db.refresh(part)
        return part
    except ValueError as exc:
        db.rollback()
        if uploaded_image is not None:
            delete_part_image_file(image_url)
        raise HTTPException(422, str(exc)) from exc
    except HTTPException:
        db.rollback()
        if uploaded_image is not None:
            delete_part_image_file(image_url)
        raise
    except Exception:
        db.rollback()
        if uploaded_image is not None:
            delete_part_image_file(image_url)
        raise


# ── GET ALL (public)
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


# ── GET ONE (public)
@app.get("/parts/{part_id}", response_model=PartResponse, tags=["Parts"])
def get_one_part(
    part_id: UUID,
    db     : Session = Depends(get_db),
):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(404, "Part not found")
    return part


# ── UPDATE (technical + admin)
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

# ── DELETE (technical can delete their own posts, admin can delete any)
@app.delete("/parts/{part_id}", status_code=204, tags=["Parts"])
def delete_part(
    part_id: UUID,
    db     : Session = Depends(get_db),
    current_user=Depends(require_technical),
):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(404, "Part not found")
    
    # Admins can delete any part
    if current_user.role == "ADMIN":
        db.delete(part)
        db.commit()
        return None
    
    # Technicals can only delete their own parts
    user_shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not user_shop:
        raise HTTPException(403, "You don't have a shop yet")
    
    # Check if this part's listing belongs to the user's shop
    listing = db.query(ShopListing).filter(
        ShopListing.part_id == part_id,
        ShopListing.shop_id == user_shop.id
    ).first()
    
    if not listing:
        raise HTTPException(403, "You don't have permission to delete this part")
    
    # Delete the part and its listing
    db.delete(listing)
    db.delete(part)
    db.commit()
    return None

from decimal import Decimal
import json
from uuid import UUID

from fastapi import Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from api.part.models import Part
from api.part.hardware_utils import (
    create_hardware_spec,
    delete_part_image_file,
    get_category,
    resolve_hardware_type,
    save_part_image,
)
from api.part_specs.models import (
    PartSpecBattery,
    PartSpecCharger,
    PartSpecDisplay,
    PartSpecFan,
    PartSpecHDD,
    PartSpecRAM,
    PartSpecSSD,
    PartSpecThermal,
)
from api.shop_listing.models import PartCondition, ShopListing
from api.shop_listing.schemas import (
    HardwareListingResponse,
    ShopListingCreate,
    ShopListingResponse,
    ShopListingUpdate,
    ShopListingWithDetails,
    ShopListingCard,
)
from core.db import get_db
from core.security import get_current_user, require_technical, require_admin
from api.shops.models import Shop, ShopStatus
from api.shops.schemas import ShopResponse
from api.part.schemas import PartResponse
from api.users.models import User, UserRole


def _listing_with_details(db: Session, listing: ShopListing):
    part = db.query(Part).filter(Part.id == listing.part_id).first()
    shop = db.query(Shop).filter(Shop.id == listing.shop_id).first()
    return {
        "listing": listing,
        "part": part,
        "shop": shop,
    }


def _model_to_dict(model):
    if not model:
        return {}
    return {
        column.name: getattr(model, column.name)
        for column in model.__table__.columns
        if column.name not in {"id", "part_id"}
    }


def _part_specs(db: Session, part: Part | None, extra: dict | None = None):
    specs = dict(extra or {})
    if not part:
        return specs

    for model in (
        PartSpecRAM,
        PartSpecSSD,
        PartSpecHDD,
        PartSpecBattery,
        PartSpecDisplay,
        PartSpecCharger,
        PartSpecFan,
        PartSpecThermal,
    ):
        spec = db.query(model).filter(model.part_id == part.id).first()
        if spec:
            specs.update(_model_to_dict(spec))
            break
    return specs


def _synthetic_previous_price(price: Decimal | None):
    if not price:
        return None
    return (Decimal(price) * Decimal("1.12")).quantize(Decimal("0.01"))


def _listing_card(db: Session, listing: ShopListing) -> ShopListingCard:
    part = db.query(Part).filter(Part.id == listing.part_id).first()
    shop = db.query(Shop).filter(Shop.id == listing.shop_id).first()
    
    # Get owner info (username shown as "Posted by", full name for display)
    owner_username = None
    owner_full_name = None
    owner_profile_image_url = None
    owner_id = None
    owner_role = None
    if shop and shop.owner:
        owner_username = getattr(shop.owner, "username", None)
        owner_full_name = f"{getattr(shop.owner, 'firstname', '')} {getattr(shop.owner, 'lastname', '')}".strip()
        owner_profile_image_url = getattr(shop.owner, "profile_image_url", None)
        owner_id = shop.owner_id
        owner_role = getattr(getattr(shop.owner, "role", None), "value", None)
    
    # Fallback to shop image if part has no image
    part_image = getattr(part, "img_url", None) or getattr(shop, "shop_pro_img_url", None)
    
    return ShopListingCard(
        id              = listing.id,
        shop_id         = listing.shop_id,
        part_id         = listing.part_id,
        price           = listing.price,
        stock_quantity  = listing.stock_quantity,
        condition       = listing.condition,
        update_at       = listing.update_at,
        shop_name       = owner_username,
        shop_image      = getattr(shop, "shop_pro_img_url", None),
        part_image      = part_image,
        part_brand      = getattr(part, "brand", None),
        part_model      = getattr(part, "model_name", None),
        part_specs      = _part_specs(db, part),
        owner_id        = owner_id,
        owner_role      = owner_role,
        owner_full_name = owner_full_name,
        owner_profile_image_url = owner_profile_image_url,
        shop            = ShopResponse.from_orm(shop) if shop else None,
        part            = PartResponse.from_orm(part) if part else None,
    )


def register_shop_listing_routes(app):

    # ── CREATE LISTING (technical only — own shop)

    @app.post("/listings/", response_model=ShopListingResponse, status_code=201, tags=["Shop Listings"])
    def create_listing(
        payload     : ShopListingCreate,
        db          : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        # get owner's shop
        shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
        if not shop:
            raise HTTPException(404, "You don't have a shop yet")
        if shop.status != ShopStatus.ACTIVE:
            raise HTTPException(403, "Your shop is not verified yet")

        # validate part exists
        part = db.query(Part).filter(Part.id == payload.part_id).first()
        if not part:
            raise HTTPException(404, "Part not found")

        # prevent duplicate listing for same part in same shop
        existing = db.query(ShopListing).filter(
            ShopListing.shop_id == shop.id,
            ShopListing.part_id == payload.part_id,
        ).first()
        if existing:
            raise HTTPException(400, "This part is already listed in your shop")

        listing = ShopListing(
            shop_id        = shop.id,
            part_id        = payload.part_id,
            price          = payload.price,
            stock_quantity = payload.stock_quantity,
            condition      = payload.condition,
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        return listing


    @app.post(
        "/listings/hardware/",
        response_model=HardwareListingResponse,
        status_code=201,
        tags=["Shop Listings"],
    )
    async def create_hardware_listing(
        request      : Request,
        db           : Session           = Depends(get_db),
        current_user = Depends(require_technical),
    ):
        content_type = (request.headers.get("content-type") or "").lower()
        raw_payload: dict = {}
        uploaded_image: UploadFile | None = None

        if "multipart/form-data" in content_type:
            form = await request.form()
            raw_payload = dict(form)
            # Find image in common fields
            for k in ("product_image", "part_image", "image", "img", "img_url", "image_url", "imageUrl", "imgUrl"):
                v = form.get(k)
                if isinstance(v, UploadFile):
                    uploaded_image = v
                    break
            # Fallback for any UploadFile
            if not uploaded_image:
                for _, v in form.multi_items():
                    if isinstance(v, UploadFile):
                        uploaded_image = v
                        break
        else:
            try:
                raw_payload = await request.json()
            except:
                raise HTTPException(400, "Invalid JSON body")

        def _get(key, *aliases):
            val = raw_payload.get(key)
            if val is not None and val != "": return val
            for a in aliases:
                val = raw_payload.get(a)
                if val is not None and val != "": return val
            return None

        shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
        if not shop:
            raise HTTPException(404, "You don't have a shop yet")
        if shop.status != ShopStatus.ACTIVE:
            raise HTTPException(403, "Your shop is not verified yet")

        category_id = _get("category_id", "categoryId")
        category_slug = _get("category_slug", "categorySlug", "category", "hardware_type", "hardwareType")
        category = get_category(db, category_id, category_slug)
        hardware_type = resolve_hardware_type(category)

        brand = _get("brand", "brandName", "part_brand", "partBrand")
        if not brand: raise HTTPException(422, "brand is required")
        
        model_name = _get("model_name", "modelName", "part_model", "partModel")
        if not model_name: raise HTTPException(422, "model_name is required")

        price_raw = _get("price")
        if price_raw is None: raise HTTPException(422, "price is required")
        try:
            price = Decimal(str(price_raw))
        except:
            raise HTTPException(422, "price must be a decimal")

        stock_quantity = int(_get("stock_quantity", "stockQuantity", "quantity") or 1)
        
        condition_raw = _get("condition")
        condition = PartCondition.NEW
        if condition_raw:
            try:
                condition = PartCondition(str(condition_raw).lower())
            except:
                pass

        spec_data_raw = _get("spec_data", "specData", "part_specs", "partSpecs")
        if not spec_data_raw: raise HTTPException(422, "spec_data is required")
        if isinstance(spec_data_raw, str):
            try:
                spec_data = json.loads(spec_data_raw)
            except:
                raise HTTPException(422, "spec_data must be valid JSON")
        else:
            spec_data = spec_data_raw

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

        # Handle image URL from text fields if no file uploaded
        image_url = _scan(raw_payload, ["img_url", "image_url", "imageUrl", "imgUrl", "product_image"], ["part_image", "product_img_url", "part_img_url", "image", "img", "photo", "file", "thumbnail", "image_link", "img_link", "link", "url"])
        if uploaded_image:
            image_url = save_part_image(uploaded_image, request)

        try:
            part = Part(
                category_id   = category.id,
                brand         = brand,
                model_name    = model_name,
                specification = _get("specification", "summary", "description"),
                img_url       = image_url,
            )
            db.add(part)
            db.flush()

            create_hardware_spec(db, category, part.id, spec_data)

            listing = ShopListing(
                shop_id        = shop.id,
                part_id        = part.id,
                price          = price,
                stock_quantity = stock_quantity,
                condition      = condition,
            )
            db.add(listing)

            db.commit()
            db.refresh(part)
            db.refresh(listing)
        except HTTPException:
            db.rollback()
            if uploaded_image: delete_part_image_file(image_url)
            raise
        except Exception:
            db.rollback()
            if uploaded_image: delete_part_image_file(image_url)
            raise

        return {
            "listing"      : listing,
            "part"         : part,
            "category"     : category,
            "hardware_type": hardware_type,
            "spec"         : spec_data,
        }


    # ── GET ALL LISTINGS (public) — filter by shop or part

    @app.get("/listings/", response_model=list[ShopListingCard], tags=["Shop Listings"])
    def get_all_listings(
        shop_id  : UUID | None = None,
        part_id  : UUID | None = None,
        condition: str  | None = None,
        skip     : int         = 0,
        limit    : int         = 20,
        db       : Session     = Depends(get_db),
    ):
        query = db.query(ShopListing)
        if shop_id:
            query = query.filter(ShopListing.shop_id == shop_id)
        if part_id:
            query = query.filter(ShopListing.part_id == part_id)
        if condition:
            query = query.filter(ShopListing.condition == condition.lower())
        listings = query.order_by(ShopListing.price.asc()).offset(skip).limit(limit).all()
        return [_listing_card(db, l) for l in listings]


    @app.get("/listings/price-drops/", response_model=list[ShopListingCard], tags=["Shop Listings"])
    def get_price_drops(
        limit: int = 10,
        db   : Session = Depends(get_db),
    ):
        """Returns low-price listings with a computed previous price for alerts."""
        listings = (
            db.query(ShopListing)
            .filter(ShopListing.stock_quantity > 0)
            .order_by(ShopListing.price.asc(), ShopListing.update_at.desc())
            .limit(limit)
            .all()
        )

        cards = []
        for listing in listings:
            card = _listing_card(db, listing)
            part = db.query(Part).filter(Part.id == listing.part_id).first()
            previous_price = _synthetic_previous_price(listing.price)
            card.part_specs = _part_specs(
                db,
                part,
                {
                    "old_price": previous_price,
                    "previous_price": previous_price,
                },
            )
            cards.append(card)
        return cards


    @app.get("/listings/recently-added/", response_model=list[ShopListingCard], tags=["Shop Listings"])
    def get_recently_added_before_listing_id(
        limit      : int         = 10,
        category_id: UUID | None = None,
        db         : Session     = Depends(get_db),
    ):
        query = db.query(ShopListing).join(Part, ShopListing.part_id == Part.id)
        if category_id:
            query = query.filter(Part.category_id == category_id)
        listings = query.order_by(ShopListing.update_at.desc()).limit(limit).all()
        return [_listing_card(db, l) for l in listings]


    @app.get("/listings/my-listings/", response_model=list[ShopListingCard], tags=["Shop Listings"])
    def get_my_listings_before_listing_id(
        db          : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
        if not shop:
            raise HTTPException(404, "You don't have a shop yet")
        listings = db.query(ShopListing).filter(ShopListing.shop_id == shop.id).all()
        return [_listing_card(db, l) for l in listings]


    # ── GET ONE LISTING (public) 

    @app.get("/listings/{listing_id}", response_model=ShopListingResponse, tags=["Shop Listings"])
    def get_one_listing(
        listing_id: UUID,
        db        : Session = Depends(get_db),
    ):
        listing = db.query(ShopListing).filter(ShopListing.id == listing_id).first()
        if not listing:
            raise HTTPException(404, "Listing not found")
        return listing


    # ── GET MY SHOP LISTINGS (technical only)

    @app.get("/listings/my-listings/", response_model=list[ShopListingCard], tags=["Shop Listings"])
    def get_my_listings(
        db          : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
        if not shop:
            raise HTTPException(404, "You don't have a shop yet")
        listings = db.query(ShopListing).filter(ShopListing.shop_id == shop.id).all()
        return [_listing_card(db, l) for l in listings]


    # ── UPDATE LISTING (technical — own shop only)

    @app.patch("/listings/{listing_id}", response_model=ShopListingResponse, tags=["Shop Listings"])
    def update_listing(
        listing_id  : UUID,
        payload     : ShopListingUpdate,
        db          : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        listing = db.query(ShopListing).filter(ShopListing.id == listing_id).first()
        if not listing:
            raise HTTPException(404, "Listing not found")

        # ensure technical user owns this listing's shop
        shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
        if not shop or listing.shop_id != shop.id:
            raise HTTPException(403, "You can only update your own listings")

        if payload.price          is not None: listing.price          = payload.price
        if payload.stock_quantity is not None: listing.stock_quantity = payload.stock_quantity
        if payload.condition      is not None: listing.condition      = payload.condition

        db.commit()
        db.refresh(listing)
        return listing


    # ── DELETE LISTING (technical own shop + admin) 

    @app.delete("/listings/{listing_id}", status_code=204, tags=["Shop Listings"])
    def delete_listing(
        listing_id  : UUID,
        db          : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        listing = db.query(ShopListing).filter(ShopListing.id == listing_id).first()
        if not listing:
            raise HTTPException(404, "Listing not found")

        # admin can delete any, technical can only delete own
        if current_user.role == UserRole.ADMIN:
            db.delete(listing)
            db.commit()
            return

        shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
        if not shop or listing.shop_id != shop.id:
            raise HTTPException(403, "You can only delete your own listings")


        db.delete(listing)
        db.commit()


    # ── ADMIN: GET ALL LISTINGS (admin only)
    @app.get("/admin/listings/", response_model=list[ShopListingCard], tags=["Admin"])
    def admin_get_all_listings(
        skip : int     = 0,
        limit: int     = 50,
        db   : Session = Depends(get_db),
        _    : User    = Depends(require_admin),
    ):
        """Allows admin to see all listings in the system."""
        listings = db.query(ShopListing).offset(skip).limit(limit).all()
        return [_listing_card(db, l) for l in listings]


    # ── ADMIN: DELETE ANY LISTING (admin only)

    @app.delete("/admin/listings/{listing_id}", status_code=204, tags=["Admin"])
    def admin_delete_listing(
        listing_id: UUID,
        db        : Session = Depends(get_db),
        _         : User    = Depends(require_admin),
    ):
        """Allows admin to remove any user's post/listing."""
        listing = db.query(ShopListing).filter(ShopListing.id == listing_id).first()
        if not listing:
            raise HTTPException(404, "Listing not found")
        
        db.delete(listing)
        db.commit()
        return None

    # ── ADMIN: LISTINGS SUMMARY (admin only) 

    @app.get("/admin/listings/summary", tags=["Admin"])
    def admin_get_listings_summary(
        db: Session = Depends(get_db),
        _ : User    = Depends(require_admin),
    ):
        """Returns a summary of listings for the admin dashboard."""
        total_listings = db.query(ShopListing).count()
        # Count by condition
        new_count = db.query(ShopListing).filter(ShopListing.condition == PartCondition.NEW).count()
        used_count = db.query(ShopListing).filter(ShopListing.condition == PartCondition.USED).count()
        refurb_count = db.query(ShopListing).filter(ShopListing.condition == PartCondition.REFURBISHED).count()
        
        return {
            "total_listings": total_listings,
            "by_condition": {
                "NEW": new_count,
                "USED": used_count,
                "REFURBISHED": refurb_count
            }
        }

    # ── UPDATE LISTING (technical own shop + admin) 
    @app.patch("/listings/{listing_id}", response_model=ShopListingResponse, tags=["Shop Listings"])
    def update_listing(
        listing_id  : UUID,
        payload     : ShopListingUpdate,
        db          : Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        listing = db.query(ShopListing).filter(ShopListing.id == listing_id).first()
        if not listing:
            raise HTTPException(404, "Listing not found")

        # admin can update any, technical can only update own
        if current_user.role != UserRole.ADMIN:
            shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
            if not shop or listing.shop_id != shop.id:
                raise HTTPException(403, "You can only update your own listings")

        # Update fields that are provided
        if payload.price is not None:
            listing.price = payload.price
        if payload.stock_quantity is not None:
            listing.stock_quantity = payload.stock_quantity
        if payload.condition is not None:
            listing.condition = payload.condition

        db.commit()
        db.refresh(listing)
        return listing
    
    # get recently added ==================
    @app.get("/listings/recently-added/", response_model=list[ShopListingCard], tags=["Shop Listings"])
    def get_recently_added(
        limit      : int         = 10,
        category_id: UUID | None = None,
        db         : Session     = Depends(get_db),
    ):
        """Returns the most recently added listings sorted by newest first."""
        query = db.query(ShopListing).join(Part, ShopListing.part_id == Part.id)
 
        # optional filter by category
        if category_id:
            query = query.filter(Part.category_id == category_id)
 
        listings = (
            query
            .order_by(ShopListing.update_at.desc())
            .limit(limit)
            .all()
        )
        return [_listing_card(db, l) for l in listings]

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from api.part.models import Part
from api.shop_listing.models import ShopListing
from api.shop_listing.schemas import ShopListingCreate, ShopListingResponse, ShopListingUpdate
from core.db import get_db
from core.security import get_current_user, require_technical, require_admin
from api.shops.models import Shop



def register_shop_listing_routes(app):

    # ── CREATE LISTING (technical only — own shop) ─────────────────────────

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
        if shop.status != "ACTIVE":
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


    # ── GET ALL LISTINGS (public) — filter by shop or part ────────────────

    @app.get("/listings/", response_model=list[ShopListingResponse], tags=["Shop Listings"])
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
            query = query.filter(ShopListing.condition == condition.upper())
        return query.order_by(ShopListing.price.asc()).offset(skip).limit(limit).all()


    # ── GET ONE LISTING (public) ───────────────────────────────────────────

    @app.get("/listings/{listing_id}", response_model=ShopListingResponse, tags=["Shop Listings"])
    def get_one_listing(
        listing_id: UUID,
        db        : Session = Depends(get_db),
    ):
        listing = db.query(ShopListing).filter(ShopListing.id == listing_id).first()
        if not listing:
            raise HTTPException(404, "Listing not found")
        return listing


    # ── GET MY SHOP LISTINGS (technical only) ─────────────────────────────

    @app.get("/listings/my-listings/", response_model=list[ShopListingResponse], tags=["Shop Listings"])
    def get_my_listings(
        db          : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
        if not shop:
            raise HTTPException(404, "You don't have a shop yet")
        return db.query(ShopListing).filter(ShopListing.shop_id == shop.id).all()


    # ── UPDATE LISTING (technical — own shop only) ─────────────────────────

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


    # ── DELETE LISTING (technical own shop + admin) ────────────────────────

    @app.delete("/listings/{listing_id}", status_code=204, tags=["Shop Listings"])
    def delete_listing(
        listing_id  : UUID,
        db          : Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        listing = db.query(ShopListing).filter(ShopListing.id == listing_id).first()
        if not listing:
            raise HTTPException(404, "Listing not found")

        # admin can delete any, technical can only delete own
        if current_user.role == "ADMIN":
            db.delete(listing)
            db.commit()
            return

        shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
        if not shop or listing.shop_id != shop.id:
            raise HTTPException(403, "You can only delete your own listings")

        db.delete(listing)
        db.commit()
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from api.addresses.models import ShopAddress
from api.addresses.schemas import ShopAddressCreate, ShopAddressResponse, ShopAddressUpdate
from core.db import get_db
from core.security import require_admin, require_technical, get_current_user
from api.shops.models import Shop

def register_shop_address_routes(app):

    # ADD ADDRESS TO SHOP (technical — own shop only) 

    @app.post("/shops/{shop_id}/addresses/", response_model=ShopAddressResponse, status_code=201, tags=["Shop Addresses"])
    def add_address(
        shop_id     : UUID,
        payload     : ShopAddressCreate,
        db          : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(404, "Shop not found")
        if shop.owner_id != current_user.id:
            raise HTTPException(403, "You can only add addresses to your own shop")

        # if new address is_main → flip all others to False
        if payload.is_main:
            db.query(ShopAddress).filter(ShopAddress.shop_id == shop_id).update({"is_main": False})

        # if this is first address → auto set as main
        count = db.query(ShopAddress).filter(ShopAddress.shop_id == shop_id).count()
        is_main = True if count == 0 else payload.is_main

        address = ShopAddress(
            shop_id        = shop_id,
            province       = payload.province,
            district       = payload.district,
            detail         = payload.detail,
            google_maps_url= payload.google_maps_url,
            latitude       = payload.latitude,
            longitude      = payload.longitude,
            is_main        = is_main,
        )
        db.add(address)
        db.commit()
        db.refresh(address)
        return address

    # GET ALL ADDRESSES FOR A SHOP (public)

    @app.get("/shops/{shop_id}/addresses/", response_model=list[ShopAddressResponse], tags=["Shop Addresses"])
    def get_shop_addresses(
        shop_id: UUID,
        db     : Session = Depends(get_db),
    ):
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(404, "Shop not found")
        return (
            db.query(ShopAddress)
            .filter(ShopAddress.shop_id == shop_id)
            .order_by(ShopAddress.is_main.desc())  # main address first
            .all()
        )


    # ── GET ONE ADDRESS (public) ───────────────────────────────────────────

    @app.get("/shops/{shop_id}/addresses/{address_id}", response_model=ShopAddressResponse, tags=["Shop Addresses"])
    def get_one_address(
        shop_id   : UUID,
        address_id: UUID,
        db        : Session = Depends(get_db),
    ):
        address = db.query(ShopAddress).filter(
            ShopAddress.id      == address_id,
            ShopAddress.shop_id == shop_id,
        ).first()
        if not address:
            raise HTTPException(404, "Address not found")
        return address


    # ── UPDATE ADDRESS (technical — own shop only) ─────────────────────────

    @app.patch("/shops/{shop_id}/addresses/{address_id}", response_model=ShopAddressResponse, tags=["Shop Addresses"])
    def update_address(
        shop_id    : UUID,
        address_id : UUID,
        payload    : ShopAddressUpdate,
        db         : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(404, "Shop not found")
        if shop.owner_id != current_user.id:
            raise HTTPException(403, "You can only update your own shop addresses")

        address = db.query(ShopAddress).filter(
            ShopAddress.id      == address_id,
            ShopAddress.shop_id == shop_id,
        ).first()
        if not address:
            raise HTTPException(404, "Address not found")

        # if setting this as main → flip all others to False first
        if payload.is_main:
            db.query(ShopAddress).filter(
                ShopAddress.shop_id == shop_id,
                ShopAddress.id      != address_id,
            ).update({"is_main": False})

        if payload.province        is not None: address.province        = payload.province
        if payload.district        is not None: address.district        = payload.district
        if payload.detail          is not None: address.detail          = payload.detail
        if payload.google_maps_url is not None: address.google_maps_url = payload.google_maps_url
        if payload.latitude        is not None: address.latitude        = payload.latitude
        if payload.longitude       is not None: address.longitude       = payload.longitude
        if payload.is_main         is not None: address.is_main         = payload.is_main

        db.commit()
        db.refresh(address)
        return address

    # ── SET AS MAIN ADDRESS 

    @app.patch("/shops/{shop_id}/addresses/{address_id}/set-main", response_model=ShopAddressResponse, tags=["Shop Addresses"])
    def set_main_address(
        shop_id    : UUID,
        address_id : UUID,
        db         : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(404, "Shop not found")
        if shop.owner_id != current_user.id:
            raise HTTPException(403, "You can only update your own shop addresses")

        # flip all to False
        db.query(ShopAddress).filter(ShopAddress.shop_id == shop_id).update({"is_main": False})

        # set this one as main
        address = db.query(ShopAddress).filter(
            ShopAddress.id      == address_id,
            ShopAddress.shop_id == shop_id,
        ).first()
        if not address:
            raise HTTPException(404, "Address not found")

        address.is_main = True
        db.commit()
        db.refresh(address)
        return address


    # ── DELETE ADDRESS (technical — own shop only) ─────────────────────────

    @app.delete("/shops/{shop_id}/addresses/{address_id}", status_code=204, tags=["Shop Addresses"])
    def delete_address(
        shop_id    : UUID,
        address_id : UUID,
        db         : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(404, "Shop not found")
        if shop.owner_id != current_user.id:
            raise HTTPException(403, "You can only delete your own shop addresses")

        address = db.query(ShopAddress).filter(
            ShopAddress.id      == address_id,
            ShopAddress.shop_id == shop_id,
        ).first()
        if not address:
            raise HTTPException(404, "Address not found")

        # prevent deleting main address if others exist
        if address.is_main:
            count = db.query(ShopAddress).filter(ShopAddress.shop_id == shop_id).count()
            if count > 1:
                raise HTTPException(400, "Cannot delete main address. Set another address as main first")

        db.delete(address)
        db.commit()
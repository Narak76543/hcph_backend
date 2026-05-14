from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from api.alerts.models import ListingReaction, ListingShare, SavedListing
from api.alerts.schemas import (
    AlertResponse,
    ListingEngagementResponse,
    SavedListingCreate,
)
from api.shop_listing.models import ShopListing
from api.shop_listing.views import _listing_card
from api.users.models import User
from core.db import get_db
from core.security import decode_token, get_current_user


def _optional_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        payload = decode_token(token)
    except HTTPException:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def _alert_from_listing(db: Session, listing: ShopListing, index: int) -> AlertResponse:
    card = _listing_card(db, listing)
    part_name = " ".join(
        value for value in [card.part_brand, card.part_model] if value
    ).strip() or "Hardware part"
    shop_name = card.shop_name or "Verified shop"

    return AlertResponse(
        id=f"listing-{listing.id}",
        title=f"{part_name} is available now",
        subtitle=f"${card.price} • {shop_name}",
        type="shop" if index % 2 else "price_drop",
        created_at=listing.update_at,
        is_unread=index < 3,
        listing_id=listing.id,
    )


def _saved_listing_cards(db: Session, user_id: UUID):
    saved = (
        db.query(SavedListing)
        .filter(SavedListing.user_id == user_id)
        .order_by(SavedListing.created_at.desc())
        .all()
    )
    cards = []
    for item in saved:
        listing = (
            db.query(ShopListing)
            .filter(ShopListing.id == item.listing_id)
            .first()
        )
        if listing:
            cards.append(_listing_card(db, listing))
    return cards


def _listing_or_404(db: Session, listing_id: UUID) -> ShopListing:
    listing = db.query(ShopListing).filter(ShopListing.id == listing_id).first()
    if not listing:
        raise HTTPException(404, "Listing not found")
    return listing


def _listing_link(request: Request, listing_id: UUID) -> str:
    frontend_origin = request.headers.get("x-frontend-origin")
    if frontend_origin:
        return f"{frontend_origin.rstrip('/')}/parts/{listing_id}"
    return f"https://hcph.app/parts/{listing_id}"


def _engagement_response(
    db: Session,
    request: Request,
    listing_id: UUID,
    current_user: User | None = None,
) -> ListingEngagementResponse:
    reaction_query = db.query(ListingReaction).filter(
        ListingReaction.listing_id == listing_id,
        ListingReaction.reaction_type == "flame",
    )
    saved_query = db.query(SavedListing).filter(SavedListing.listing_id == listing_id)
    share_query = db.query(ListingShare).filter(ListingShare.listing_id == listing_id)

    reacted = False
    saved = False
    if current_user:
        reacted = (
            reaction_query.filter(ListingReaction.user_id == current_user.id).first()
            is not None
        )
        saved = (
            saved_query.filter(SavedListing.user_id == current_user.id).first()
            is not None
        )

    return ListingEngagementResponse(
        listing_id=listing_id,
        reaction_count=reaction_query.count(),
        save_count=saved_query.count(),
        share_count=share_query.count(),
        reacted=reacted,
        saved=saved,
        link_url=_listing_link(request, listing_id),
    )


def register_alert_routes(app):
    @app.get(
        "/listings/{listing_id}/engagement",
        response_model=ListingEngagementResponse,
        tags=["Listing Engagement"],
    )
    def get_listing_engagement(
        listing_id: UUID,
        request: Request,
        db: Session = Depends(get_db),
        current_user=Depends(_optional_user),
    ):
        _listing_or_404(db, listing_id)
        return _engagement_response(db, request, listing_id, current_user)

    @app.post(
        "/listings/{listing_id}/react",
        response_model=ListingEngagementResponse,
        tags=["Listing Engagement"],
    )
    def toggle_listing_reaction(
        listing_id: UUID,
        request: Request,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        _listing_or_404(db, listing_id)
        existing = (
            db.query(ListingReaction)
            .filter(
                ListingReaction.user_id == current_user.id,
                ListingReaction.listing_id == listing_id,
                ListingReaction.reaction_type == "flame",
            )
            .first()
        )
        if existing:
            db.delete(existing)
        else:
            db.add(
                ListingReaction(
                    user_id=current_user.id,
                    listing_id=listing_id,
                    reaction_type="flame",
                )
            )
        db.commit()
        return _engagement_response(db, request, listing_id, current_user)

    @app.post(
        "/listings/{listing_id}/save",
        response_model=ListingEngagementResponse,
        tags=["Listing Engagement"],
    )
    def toggle_listing_save(
        listing_id: UUID,
        request: Request,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        _listing_or_404(db, listing_id)
        existing = (
            db.query(SavedListing)
            .filter(
                SavedListing.user_id == current_user.id,
                SavedListing.listing_id == listing_id,
            )
            .first()
        )
        if existing:
            db.delete(existing)
        else:
            db.add(SavedListing(user_id=current_user.id, listing_id=listing_id))
        db.commit()
        return _engagement_response(db, request, listing_id, current_user)

    @app.post(
        "/listings/{listing_id}/share",
        response_model=ListingEngagementResponse,
        tags=["Listing Engagement"],
    )
    def count_listing_share(
        listing_id: UUID,
        request: Request,
        db: Session = Depends(get_db),
        current_user=Depends(_optional_user),
    ):
        _listing_or_404(db, listing_id)
        db.add(
            ListingShare(
                user_id=current_user.id if current_user else None,
                listing_id=listing_id,
                channel="copy_link",
            )
        )
        db.commit()
        return _engagement_response(db, request, listing_id, current_user)

    @app.get("/alerts/", response_model=list[AlertResponse], tags=["Alerts"])
    def get_alerts(
        limit: int = 10,
        db: Session = Depends(get_db),
    ):
        listings = (
            db.query(ShopListing)
            .order_by(ShopListing.update_at.desc())
            .limit(limit)
            .all()
        )
        return [_alert_from_listing(db, listing, index) for index, listing in enumerate(listings)]

    @app.get("/notifications/", response_model=list[AlertResponse], tags=["Alerts"])
    def get_notifications(
        limit: int = 10,
        db: Session = Depends(get_db),
    ):
        listings = (
            db.query(ShopListing)
            .order_by(ShopListing.update_at.desc())
            .limit(limit)
            .all()
        )
        return [_alert_from_listing(db, listing, index) for index, listing in enumerate(listings)]

    @app.get("/saved-parts/", tags=["Saved Listings"])
    def get_saved_parts(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        return _saved_listing_cards(db, current_user.id)

    @app.get("/saved-listings/", tags=["Saved Listings"])
    def get_saved_listings(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        return _saved_listing_cards(db, current_user.id)

    @app.get("/bookmarks/", tags=["Saved Listings"])
    def get_bookmarks(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        return _saved_listing_cards(db, current_user.id)

    @app.post("/saved-listings/", status_code=201, tags=["Saved Listings"])
    def save_listing(
        payload: SavedListingCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        listing = (
            db.query(ShopListing)
            .filter(ShopListing.id == payload.listing_id)
            .first()
        )
        if not listing:
            raise HTTPException(404, "Listing not found")

        existing = (
            db.query(SavedListing)
            .filter(
                SavedListing.user_id == current_user.id,
                SavedListing.listing_id == payload.listing_id,
            )
            .first()
        )
        if existing:
            return {"message": "Listing already saved", "listing": _listing_card(db, listing)}

        saved = SavedListing(user_id=current_user.id, listing_id=payload.listing_id)
        db.add(saved)
        db.commit()
        db.refresh(saved)
        return {"message": "Listing saved", "listing": _listing_card(db, listing)}

    @app.delete("/saved-listings/{listing_id}", status_code=204, tags=["Saved Listings"])
    def unsave_listing(
        listing_id: UUID,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        saved = (
            db.query(SavedListing)
            .filter(
                SavedListing.user_id == current_user.id,
                SavedListing.listing_id == listing_id,
            )
            .first()
        )
        if not saved:
            raise HTTPException(404, "Saved listing not found")
        db.delete(saved)
        db.commit()
        return None

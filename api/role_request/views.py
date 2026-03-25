from uuid import UUID
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from api.role_request.models import RequestStatus, RoleRequest
from api.role_request.schemas import (
    RoleRequestCreate,
    RoleRequestReject,
    RoleRequestResponse,
)
from api.users.models import User, UserRole
from core.app import app
from core.db import get_db
from core.security import get_current_user, require_admin


@app.post("/requests/", response_model=RoleRequestResponse, status_code=201, tags=["Role Requests"])
def submit_request(
    payload: RoleRequestCreate,
    db     : Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role in (UserRole.technical, UserRole.admin):
        raise HTTPException(400, "You are already a Technical or Admin user")

    existing = db.query(RoleRequest).filter(
        RoleRequest.user_id == current_user.id,
        RoleRequest.status == RequestStatus.pending,
    ).first()
    if existing:
        raise HTTPException(400, "You already have a pending request")

    req = RoleRequest(
        user_id      = current_user.id,
        shop_name    = payload.shop_name,
        shop_address = payload.shop_address,
        phone        = payload.phone,
        reason       = payload.reason,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

@app.get("/requests/my-request", response_model=RoleRequestResponse, tags=["Role Requests"])
def get_my_request(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    req = db.query(RoleRequest).filter(
        RoleRequest.user_id == current_user.id
    ).order_by(RoleRequest.create_at.desc()).first()
    if not req:
        raise HTTPException(404, "No request found")
    return req

@app.get("/requests/", response_model=list[RoleRequestResponse], tags=["Role Requests"])
def get_all_requests(
    status : str | None = None,
    skip   : int        = 0,
    limit  : int        = 20,
    db     : Session    = Depends(get_db),
    _=Depends(require_admin),
):
    query = db.query(RoleRequest)
    if status:
        query = query.filter(RoleRequest.status == status.upper())
    return query.order_by(RoleRequest.create_at.desc()).offset(skip).limit(limit).all()

@app.get("/requests/{request_id}", response_model=RoleRequestResponse, tags=["Role Requests"])
def get_one_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    req = db.query(RoleRequest).filter(RoleRequest.id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")
    return req

@app.patch("/requests/{request_id}/approve", response_model=RoleRequestResponse, tags=["Role Requests"])
def approve_request(
    request_id: UUID,
    db        : Session = Depends(get_db),
    _=Depends(require_admin),
):
    req = db.query(RoleRequest).filter(RoleRequest.id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")
    if req.status != RequestStatus.pending:
        raise HTTPException(400, f"Request is already {req.status}")

    req.status = RequestStatus.approved

    user = db.query(User).filter(User.id == req.user_id).first()
    if user:
        user.role = UserRole.technical

    db.commit()
    db.refresh(req)
    return req

@app.patch("/requests/{request_id}/reject", response_model=RoleRequestResponse, tags=["Role Requests"])
def reject_request(
    request_id: UUID,
    payload   : RoleRequestReject,
    db        : Session = Depends(get_db),
    _=Depends(require_admin),
):
    req = db.query(RoleRequest).filter(RoleRequest.id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")
    
    if req.status != RequestStatus.pending:
        raise HTTPException(400, f"Request is already {req.status}")

    req.status = RequestStatus.rejected
    req.admin_note = payload.admin_note

    db.commit()
    db.refresh(req)
    return req

@app.get("/requests/summary", tags=["Admin Reviews"])
def get_requests_summary(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Quick count of all request statuses — useful for admin dashboard."""
    pending  = db.query(RoleRequest).filter(RoleRequest.status == RequestStatus.pending).count()
    approved = db.query(RoleRequest).filter(RoleRequest.status == RequestStatus.approved).count()
    rejected = db.query(RoleRequest).filter(RoleRequest.status == RequestStatus.rejected).count()
 
    return {
        "pending" : pending,
        "approved": approved,
        "rejected": rejected,
        "total"   : pending + approved + rejected,
    }
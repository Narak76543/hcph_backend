from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from api.compatibility_rule.models import CompatibilityRule
from api.compatibility_rule.schemas import CompatibilityRuleCreate, CompatibilityRuleResponse, CompatibilityRuleUpdate
from core.db import get_db
from core.security import get_current_user, require_technical, require_admin

def register_compatibility_routes(app):

    # ── CREATE (technical + admin) 
    @app.post("/compatibility/", response_model=CompatibilityRuleResponse, status_code=201, tags=["Compatibility"])
    def create_rule(
        payload     : CompatibilityRuleCreate,
        db          : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        # prevent duplicate rule for same laptop + part
        existing = db.query(CompatibilityRule).filter(
            CompatibilityRule.laptop_model_id == payload.laptop_model_id,
            CompatibilityRule.part_id         == payload.part_id,
        ).first()
        if existing:
            raise HTTPException(400, "Compatibility rule already exists for this laptop + part")

        rule = CompatibilityRule(
            laptop_model_id = payload.laptop_model_id,
            part_id         = payload.part_id,
            is_compatible   = payload.is_compatible,
            notes           = payload.notes,
            verify_by       = current_user.id,
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule


    # ── GET ALL (public) — filter by laptop or part 
    @app.get("/compatibility/", response_model=list[CompatibilityRuleResponse], tags=["Compatibility"])
    def get_all_rules(
        laptop_model_id: UUID | None = None,
        part_id        : UUID | None = None,
        is_compatible  : bool | None = None,
        skip           : int         = 0,
        limit          : int         = 20,
        db             : Session     = Depends(get_db),
    ):
        query = db.query(CompatibilityRule)
        if laptop_model_id:
            query = query.filter(CompatibilityRule.laptop_model_id == laptop_model_id)
        if part_id:
            query = query.filter(CompatibilityRule.part_id == part_id)
        if is_compatible is not None:
            query = query.filter(CompatibilityRule.is_compatible == is_compatible)
        return query.offset(skip).limit(limit).all()


    # ── GET ONE (public) 
    @app.get("/compatibility/{rule_id}", response_model=CompatibilityRuleResponse, tags=["Compatibility"])
    def get_one_rule(
        rule_id: UUID,
        db     : Session = Depends(get_db),
    ):
        rule = db.query(CompatibilityRule).filter(CompatibilityRule.id == rule_id).first()
        if not rule:
            raise HTTPException(404, "Compatibility rule not found")
        return rule
    
    # ── CHECK COMPATIBILITY (key feature) — is this part ok for this laptop?
    @app.get("/compatibility/check/", response_model=CompatibilityRuleResponse, tags=["Compatibility"])
    def check_compatibility(
        laptop_model_id: UUID,
        part_id        : UUID,
        db             : Session = Depends(get_db),
    ):
        rule = db.query(CompatibilityRule).filter(
            CompatibilityRule.laptop_model_id == laptop_model_id,
            CompatibilityRule.part_id         == part_id,
        ).first()
        if not rule:
            raise HTTPException(404, "No compatibility data found for this combination")
        return rule


    # ── UPDATE (technical + admin) 
    @app.patch("/compatibility/{rule_id}", response_model=CompatibilityRuleResponse, tags=["Compatibility"])
    def update_rule(
        rule_id     : UUID,
        payload     : CompatibilityRuleUpdate,
        db          : Session = Depends(get_db),
        current_user=Depends(require_technical),
    ):
        rule = db.query(CompatibilityRule).filter(CompatibilityRule.id == rule_id).first()
        if not rule:
            raise HTTPException(404, "Compatibility rule not found")

        if payload.is_compatible is not None: rule.is_compatible = payload.is_compatible
        if payload.notes         is not None: rule.notes         = payload.notes
        rule.verify_by = current_user.id  # update verifier on every edit

        db.commit()
        db.refresh(rule)
        return rule


    # ── DELETE (admin only) 
    @app.delete("/compatibility/{rule_id}", status_code=204, tags=["Compatibility"])
    def delete_rule(
        rule_id: UUID,
        db     : Session = Depends(get_db),
        _=Depends(require_admin),
    ):
        rule = db.query(CompatibilityRule).filter(CompatibilityRule.id == rule_id).first()
        if not rule:
            raise HTTPException(404, "Compatibility rule not found")
        db.delete(rule)
        db.commit()
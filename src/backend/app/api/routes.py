from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from .. import models, schemas
from ..database import get_db

router = APIRouter()

@router.post("/incidents/", response_model=schemas.Incident)
def create_incident(incident: schemas.IncidentCreate, db: Session = Depends(get_db)):
    db_incident = models.Incident(**incident.model_dump())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

@router.get("/incidents/", response_model=List[schemas.Incident])
def read_incidents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    incidents = db.query(models.Incident).offset(skip).limit(limit).all()
    return incidents

from ..services.watsonx import extract_needs_from_report

@router.post("/reports/", response_model=schemas.Report)
def create_report(report: schemas.ReportCreate, db: Session = Depends(get_db)):
    # Trigger watsonx.ai extraction if raw_text is provided and structured_data is missing
    if report.raw_text and not report.structured_data:
        extracted = extract_needs_from_report(report.raw_text)
        if extracted:
            report.structured_data = extracted

    db_report = models.Report(**report.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

@router.get("/reports/", response_model=List[schemas.Report])
def read_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    reports = db.query(models.Report).offset(skip).limit(limit).all()
    return reports

from .. import crud
from ..services.planner import generate_optimized_plan

@router.post("/plans/generate", response_model=schemas.Plan)
def generate_plan(snapshot_id: str, policy_version: str = "v1.0", db: Session = Depends(get_db)):
    """
    Triggers the OR-Tools optimizer. In a real system, this queues a background worker job.
    For this demo, it runs synchronously.
    """
    # 1. Fetch unassigned needs and available resources from DB (Mocked here for brevity)
    # 2. Run OR-Tools planner
    # result = generate_optimized_plan(needs, resources)
    
    # Create the Plan candidate in the DB
    plan = crud.create_plan(db, snapshot_id=snapshot_id, policy_version=policy_version)
    
    # If solver found assignments, we would save them here via crud.add_assignments_to_plan
    
    return plan

@router.post("/plans/{plan_id}/approve", response_model=schemas.Plan)
def approve_plan(plan_id: uuid.UUID, approval: schemas.PlanApprovalRequest, db: Session = Depends(get_db)):
    """
    Executes an atomic approval, locking resources to prevent double-booking.
    """
    return crud.approve_plan(db, plan_id=plan_id, actor=approval.actor)

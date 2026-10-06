from .. import auth
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import uuid
import json

from .. import models, schemas
from ..database import get_db

router = APIRouter()

# WebSocket Manager for Real-Time Updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/incidents/", response_model=schemas.Incident)
def create_incident(incident: schemas.IncidentCreate, db: Session = Depends(get_db), current_user = Depends(auth.require_role(['admin']))):
    db_incident = models.Incident(**incident.model_dump())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

@router.get("/incidents/", response_model=List[schemas.Incident])
def read_incidents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(auth.get_current_active_user)):
    incidents = db.query(models.Incident).offset(skip).limit(limit).all()
    return incidents

from ..services.watsonx import extract_needs_from_report

@router.post("/reports/", response_model=schemas.Report)
def create_report(report: schemas.ReportCreate, db: Session = Depends(get_db), current_user = Depends(auth.get_current_active_user)):
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
    Triggers the OR-Tools optimizer.
    """
    # 1. Fetch needs and resources from DB
    needs = db.query(models.Need).all()
    resources = db.query(models.Resource).all()
    
    needs_data = [{"id": str(n.id), "urgency": n.urgency, "category": n.category} for n in needs]
    resources_data = [{"id": str(r.id), "capabilities": r.capabilities} for r in resources]
    
    # Create the Plan candidate in the DB
    plan = crud.create_plan(db, snapshot_id=snapshot_id, policy_version=policy_version)
    
    # 2. Run OR-Tools planner
    if needs_data and resources_data:
        result = generate_optimized_plan(needs_data, resources_data)
        plan.solver_status = result["status"]
        
        # Save assignments to plan
        if result["assignments"]:
            crud.add_assignments_to_plan(db, plan_id=plan.id, assignments_data=result["assignments"])
    else:
        plan.solver_status = "NO_DATA"
    
    db.commit()
    db.refresh(plan)
    return plan

@router.post("/plans/{plan_id}/approve", response_model=schemas.Plan)
def approve_plan(plan_id: uuid.UUID, approval: schemas.PlanApprovalRequest, db: Session = Depends(get_db), current_user = Depends(auth.require_role(['admin']))):
    """
    Executes an atomic approval, locking resources to prevent double-booking.
    """
    return crud.approve_plan(
        db, 
        plan_id=plan_id, 
        actor=approval.actor,
        expected_version=approval.expected_version,
        idempotency_key=approval.idempotency_key
    )

import json
from sqlalchemy import func

@router.get("/map-data")
def get_map_data(db: Session = Depends(get_db)):
    # Fetch Zones with GeoJSON
    zones_query = db.query(models.Zone.id, models.Zone.name, func.ST_AsGeoJSON(models.Zone.geometry).label("geojson")).all()
    zones = []
    for z in zones_query:
        if z.geojson:
            zones.append({"id": str(z.id), "name": z.name, "geojson": json.loads(z.geojson)})
            
    # Fetch Resources with GeoJSON
    res_query = db.query(models.Resource.id, models.Resource.name, models.Resource.mode, func.ST_AsGeoJSON(models.Resource.location).label("geojson")).all()
    resources = []
    for r in res_query:
        if r.geojson:
            resources.append({"id": str(r.id), "name": r.name, "mode": r.mode, "geojson": json.loads(r.geojson)})
            
    return {"zones": zones, "resources": resources}

from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/export/assignments")
def export_assignments(db: Session = Depends(get_db), current_user = Depends(auth.require_role(['admin', 'planner']))):
    """
    Exports all assignments (deployments) to a CSV file for compliance auditing.
    """
    assignments = db.query(models.Assignment).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Plan ID", "Need ID", "Resource ID", "Status", "Version"])
    
    for a in assignments:
        writer.writerow([a.id, a.plan_id, a.need_id, a.resource_id, a.status, a.version])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=deployment_audit.csv"}
    )

from fastapi import Form
from datetime import datetime

@router.post("/webhooks/sms")
async def twilio_sms_webhook(From: str = Form(...), Body: str = Form(...), MessageSid: str = Form(None), db: Session = Depends(get_db)):
    """
    Webhook for Twilio to ingest SMS messages from victims without internet.
    Automatically parses the SMS using IBM watsonx.ai.
    """
    if MessageSid:
        existing = db.query(models.Report).filter(models.Report.external_id == MessageSid).first()
        if existing:
            return {"message": "Duplicate SMS ignored", "report_id": existing.id}

    # 1. AI Parsing via Watsonx
    extracted_data = extract_needs_from_report(Body)
    
    # 2. Create the Field Report in DB
    db_report = models.Report(
        source=f"SMS ({From})",
        external_id=MessageSid,
        raw_text=Body,
        structured_data=extracted_data,
        observed_at=datetime.utcnow()
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # 3. Create or update an Operational Need based on the report
    if extracted_data and "category" in extracted_data:
        # For simplicity, assign to the first zone if location matching isn't implemented
        zone = db.query(models.Zone).first()
        if zone:
            new_need = models.Need(
                zone_id=zone.id,
                category=extracted_data.get("category", "rescue"),
                amount=extracted_data.get("amount", 1),
                unit=extracted_data.get("unit", "unknown"),
                urgency=extracted_data.get("urgency", 3)
            )
            db.add(new_need)
            db.commit()
    
    # 4. Broadcast to all connected React Dashboards
    await manager.broadcast(json.dumps({
        "event": "new_sms_report",
        "report_id": str(db_report.id),
        "from": From,
        "body": Body,
        "ai_analysis": extracted_data
    }))
    
    return {"message": "SMS received and processed by IBM Watsonx", "report_id": db_report.id}

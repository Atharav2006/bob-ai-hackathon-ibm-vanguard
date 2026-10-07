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
        self.active_connections = {}
        self.connection_incidents = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def register(self, websocket: WebSocket, incident_id: str):
        if incident_id not in self.active_connections:
            self.active_connections[incident_id] = []
        self.active_connections[incident_id].append(websocket)
        self.connection_incidents[websocket] = incident_id

    def disconnect(self, websocket: WebSocket):
        incident_id = self.connection_incidents.get(websocket)
        if incident_id and incident_id in self.active_connections:
            if websocket in self.active_connections[incident_id]:
                self.active_connections[incident_id].remove(websocket)
            del self.connection_incidents[websocket]

    async def broadcast(self, message: str):
        pass

    async def broadcast_to_incident(self, message: str, incident_id: str):
        if incident_id in self.active_connections:
            for connection in self.active_connections[incident_id]:
                await connection.send_text(message)

manager = ConnectionManager()

from jose import jwt, JWTError

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    authenticated = False
    incident_id = None
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                data = json.loads(data_text)
            except:
                continue
            
            if not authenticated and data.get("type") == "authenticate":
                token = data.get("token")
                inc_id = data.get("incident_id")
                
                try:
                    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
                    username: str = payload.get("sub")
                    user = db.query(models.User).filter(models.User.username == username).first()
                    if not user or not user.is_active: raise Exception()
                    
                    incident = db.query(models.Incident).filter_by(id=inc_id).first()
                    if not incident: raise Exception()
                    
                    if user.role != models.UserRole.ADMIN:
                        membership = db.query(models.IncidentMembership).filter_by(user_id=user.id, incident_id=inc_id).first()
                        if not membership: raise Exception()
                        
                    authenticated = True
                    incident_id = str(inc_id)
                    manager.register(websocket, incident_id)
                    await websocket.send_text(json.dumps({"type": "authenticated", "status": "success"}))
                except Exception:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Authentication failed"}))
                    await websocket.close(code=1008)
                    return
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
    reports = db.query(models.Report).filter(models.Report.incident_id == current_incident.id).offset(skip).limit(limit).all()
    return reports

from .. import crud
from ..services.planner import generate_optimized_plan

@router.post("/plans/generate", response_model=schemas.Plan)
def generate_plan(snapshot_id: str, policy_version: str = "v1.0", db: Session = Depends(get_db), current_user = Depends(auth.require_role(["admin", "planner"])), current_incident: models.Incident = Depends(auth.get_current_incident)):
    """
    Triggers the OR-Tools optimizer.
    """
    # 1. Fetch needs and resources from DB
    needs = db.query(models.Need).join(models.Zone).filter(models.Zone.incident_id == current_incident.id).all()
    resources = db.query(models.Resource).filter(
        models.Resource.status == "available", 
        models.Resource.incident_id == current_incident.id
    ).all()
    
    needs_data = [{"id": str(n.id), "urgency": n.urgency, "category": n.category, "amount": n.amount} for n in needs]
    resources_data = [{"id": str(r.id), "capabilities": r.capabilities, "version": r.version} for r in resources]
    
    # Create the Plan candidate in the DB
    plan = crud.create_plan(db, incident_id=current_incident.id, snapshot_id=snapshot_id, policy_version=policy_version, incident_revision=current_incident.revision)
    
    # 2. Run OR-Tools planner
    if needs_data and resources_data:
        result = generate_optimized_plan(needs_data, resources_data)
        plan.solver_status = result["status"]
        
        # Map back resources to their versions
        resource_version_map = {str(r.id): r.version for r in resources}
        for assignment in result.get("assignments", []):
            assignment["resource_version"] = resource_version_map.get(str(assignment["resource_id"]), 1)
            
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
    payload_hash = __import__("hashlib").sha256(approval.model_dump_json().encode("utf-8")).hexdigest()
    return crud.approve_plan(
        db, 
        plan_id=plan_id, 
        actor=current_user.username,
        expected_version=approval.expected_version,
        idempotency_key=approval.idempotency_key,
        payload_hash=payload_hash
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
    from sqlalchemy.exc import IntegrityError
    try:
        db.commit()
        db.refresh(db_report)
    except IntegrityError:
        db.rollback()
        existing = db.query(models.Report).filter(models.Report.external_id == MessageSid).first()
        return {"message": "Duplicate SMS ignored (IntegrityError)", "report_id": existing.id}
    
    # No automatic Need creation. Let human planners review it in the UI.
    db_report.status = "pending"
    db.commit()
    
    # 4. Broadcast to connected React Dashboards for the first operational incident
    incident = db.query(models.Incident).filter_by(mode="OPERATIONAL").first()
    if incident:
        db_report.incident_id = incident.id
        db.commit()
        await manager.broadcast_to_incident(json.dumps({
        "event": "new_sms_report",
        "report_id": str(db_report.id),
        "from": From,
        "body": Body,
        "ai_analysis": extracted_data
    }), str(incident.id))
    
    return {"message": "SMS received and processed by IBM Watsonx", "report_id": db_report.id}


@router.post("/reports/{report_id}/review", response_model=schemas.Report)
def review_report(report_id: uuid.UUID, review: schemas.ReportReviewRequest, db: Session = Depends(get_db), current_user = Depends(auth.require_role(["admin", "planner"])), current_incident: models.Incident = Depends(auth.get_current_incident)):
    report = db.query(models.Report).filter(models.Report.id == report_id, models.Report.incident_id == current_incident.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if review.action == "reject":
        report.status = "rejected"
    elif review.action == "approve":
        report.status = "verified"
        if review.zone_id and review.need_category:
            new_need = models.Need(
                zone_id=review.zone_id,
                category=review.need_category,
                amount=review.need_amount,
                urgency=review.need_urgency or 3,
                unit="unknown"
            )
            db.add(new_need)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    db.commit()
    db.refresh(report)
    return report


from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Dict, Any
import uuid

from . import models, schemas

def create_plan(db: Session, incident_id: uuid.UUID, snapshot_id: str, policy_version: str, incident_revision: int) -> models.Plan:
    plan = models.Plan(
        incident_id=incident_id,
        snapshot_id=snapshot_id,
        status="candidate",
        policy_version=policy_version,
        incident_revision=incident_revision,
        version=1
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

def add_assignments_to_plan(db: Session, plan_id: uuid.UUID, assignments_data: List[Dict[str, Any]]):
    assignments = []
    for data in assignments_data:
        assignment = models.Assignment(
            plan_id=plan_id,
            need_id=data["need_id"],
            resource_id=data["resource_id"],
            resource_version=data.get("resource_version", 1),
            status="proposed"
        )
        db.add(assignment)
        assignments.append(assignment)
    db.commit()
    return assignments

def approve_plan(db: Session, plan_id: uuid.UUID, actor: str, expected_version: int = None, idempotency_key: str = None, payload_hash: str = None):
    """
    Executes the atomic approval transaction with explicit row locks.
    Prevents double-booking of resources.
    """
    # 1. Fetch the plan
    plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Idempotency check: check records
    if idempotency_key:
        existing_record = db.query(models.IdempotencyRecord).filter_by(key=idempotency_key).first()
        if existing_record:
            if existing_record.payload_hash != payload_hash or existing_record.target_id != str(plan_id) or existing_record.operation != "APPROVE_PLAN":
                raise HTTPException(status_code=409, detail="Idempotency key reused with different payload or target")
            return existing_record.response
    
    if expected_version is not None and plan.version != expected_version:
        raise HTTPException(status_code=409, detail=f"Plan version mismatch (Expected {expected_version}, got {plan.version})")
    
    if plan.status != "candidate":
        raise HTTPException(status_code=400, detail=f"Cannot approve plan in status: {plan.status}")

    # 2. Fetch proposed assignments
    assignments = db.query(models.Assignment).filter(models.Assignment.plan_id == plan_id).all()
    if not assignments:
        raise HTTPException(status_code=400, detail="Plan has no assignments")

    resource_ids = [a.resource_id for a in assignments]

    # 3. Lock the resources (SELECT FOR UPDATE)
    # Sorting IDs prevents deadlocks if multiple transactions lock the same resources
    resource_ids_sorted = sorted(list(set(resource_ids)))
    
    locked_resources = db.query(models.Resource).filter(
        models.Resource.id.in_(resource_ids_sorted)
    ).with_for_update().all()
    
    if len(locked_resources) != len(resource_ids_sorted):
        raise HTTPException(status_code=400, detail="Some resources are missing or invalid.")

    # 3a. Check resource versions for freshness
    locked_resources_dict = {r.id: r for r in locked_resources}
    for assignment in assignments:
        locked_resource = locked_resources_dict.get(assignment.resource_id)
        if locked_resource and assignment.resource_version != locked_resource.version:
            raise HTTPException(status_code=409, detail=f"Resource {assignment.resource_id} version changed (Expected {assignment.resource_version}, got {locked_resource.version})")

    # 3b. Lock Incident to ensure freshness
    if locked_resources:
        incident_id = locked_resources[0].incident_id
        locked_incident = db.query(models.Incident).filter_by(id=incident_id).with_for_update().first()
        if locked_incident:
            if plan.incident_revision != locked_incident.revision:
                raise HTTPException(status_code=409, detail=f"Incident revision changed (Expected {plan.incident_revision}, got {locked_incident.revision})")
            locked_incident.revision += 1

    # 4. Recheck for overlapping commitments
    # Find any active assignments (assigned, acknowledged, en_route, on_site) for these resources
    active_statuses = ["assigned", "acknowledged", "en_route", "on_site", "committed"]
    conflicts = db.query(models.Assignment).filter(
        models.Assignment.resource_id.in_(resource_ids_sorted),
        models.Assignment.status.in_(active_statuses)
    ).all()
    
    if conflicts:
        db.rollback() # Release locks
        conflict_r_ids = [str(c.resource_id) for c in conflicts]
        raise HTTPException(
            status_code=409, 
            detail=f"Reservation conflict. Resources already committed: {conflict_r_ids}"
        )

    # 5. Commit the approval
    try:
        plan.status = "approved"
        plan.version += 1
        
        for assignment in assignments:
            assignment.status = "assigned"

        for resource in locked_resources:
            resource.status = "committed"
            resource.version += 1 # Update resource version for freshness guarantee


        # 6. Audit Trail
        audit = models.AuditLog(
            actor=actor,
            operation_id=str(plan_id),
            action="APPROVE_PLAN",
            delta={"plan_id": str(plan_id), "assignments_count": len(assignments)}
        )
        db.add(audit)
        
        # 7. Idempotency Record
        if idempotency_key:
            # Need to serialize the plan fully as response. We can convert to dict.
            # Using schemas.Plan.from_orm to dump to dict
            plan_response = schemas.Plan.from_orm(plan).model_dump(mode='json')
            record = models.IdempotencyRecord(
                key=idempotency_key,
                operation="APPROVE_PLAN",
                target_id=str(plan.id),
                payload_hash=payload_hash,
                response=plan_response,
                status_code=200
            )
            db.add(record)
            
        db.commit()
        db.refresh(plan)
        return plan

    except IntegrityError as e:
        db.rollback()
        # This occurs if two simultaneous transactions try to insert the same idempotency key
        existing_record = db.query(models.IdempotencyRecord).filter_by(key=idempotency_key).first()
        if existing_record:
            if existing_record.payload_hash != payload_hash or existing_record.target_id != str(plan_id) or existing_record.operation != "APPROVE_PLAN":
                raise HTTPException(status_code=409, detail="Idempotency key reused with different payload or target")
            return existing_record.response
        raise HTTPException(status_code=500, detail="Transaction failed during approval commit.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed during approval commit.")

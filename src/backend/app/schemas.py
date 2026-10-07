import uuid
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID

class IncidentBase(BaseModel):
    name: str
    mode: str = "simulation"
    timezone: str = "UTC"

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "responder"

class UserOut(BaseModel):
    id: UUID
    username: str
    role: str
    is_active: int

    class Config:
        from_attributes = True

class IncidentCreate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: UUID
    revision: int
    policy_version: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReportBase(BaseModel):
    source: str
    observed_at: datetime
    raw_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: UUID
    received_at: datetime
    status: Optional[str] = None

    class Config:
        from_attributes = True

class AssignmentBase(BaseModel):
    need_id: UUID
    resource_id: UUID

class Assignment(AssignmentBase):
    id: UUID
    plan_id: UUID
    amount_assigned: int
    resource_version: int
    status: str
    version: int

    class Config:
        from_attributes = True

class PlanBase(BaseModel):
    snapshot_id: str
    policy_version: str

class Plan(PlanBase):
    id: UUID
    status: str
    version: int
    solver_status: Optional[str] = None
    created_at: datetime
    assignments: List[Assignment] = []

    class Config:
        from_attributes = True

class PlanApprovalRequest(BaseModel):
    expected_version: Optional[int] = None
    idempotency_key: Optional[str] = None


class ReportReviewRequest(BaseModel):
    action: str # "approve" or "reject"
    need_category: Optional[str] = None
    need_amount: Optional[int] = None
    need_urgency: Optional[int] = None
    zone_id: Optional[uuid.UUID] = None


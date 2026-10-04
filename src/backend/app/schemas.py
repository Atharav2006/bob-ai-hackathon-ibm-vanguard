from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID

class IncidentBase(BaseModel):
    name: str
    mode: str = "simulation"
    timezone: str = "UTC"

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

    class Config:
        from_attributes = True

# We will expand on schemas as we build the CRUD operations.

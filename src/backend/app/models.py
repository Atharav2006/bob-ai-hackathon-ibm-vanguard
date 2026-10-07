import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
import datetime
from .database import Base

import enum

class IncidentMode(str, enum.Enum):
    SIMULATION = "simulation"
    OPERATIONAL = "operational"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PLANNER = "planner"
    RESPONDER = "responder"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.RESPONDER)
    is_active = Column(Integer, default=1)
    
    memberships = relationship("IncidentMembership", back_populates="user")

class IncidentMembership(Base):
    __tablename__ = "incident_memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    role = Column(Enum(UserRole), nullable=True) # Override role for this specific incident
    
    user = relationship("User", back_populates="memberships")
    incident = relationship("Incident", back_populates="memberships")

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    mode = Column(Enum(IncidentMode), default=IncidentMode.SIMULATION)
    timezone = Column(String, default="UTC")
    revision = Column(Integer, default=1)
    policy_version = Column(String, default="v1.0")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    zones = relationship("Zone", back_populates="incident")
    resources = relationship("Resource", back_populates="incident")
    memberships = relationship("IncidentMembership", back_populates="incident")

class Zone(Base):
    __tablename__ = "zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    name = Column(String, nullable=False)
    geometry = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=True)

    incident = relationship("Incident", back_populates="zones")
    needs = relationship("Need", back_populates="zone")

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    key = Column(String, primary_key=True)
    operation = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)
    response = Column(JSON, nullable=False)
    status_code = Column(Integer, nullable=False, default=200)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String, nullable=True) # Used for deduplication
    external_id = Column(String, unique=True, nullable=True) # E.g. Twilio MessageSid
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True)
    source = Column(String, nullable=False)
    observed_at = Column(DateTime, nullable=False)
    received_at = Column(DateTime, default=datetime.datetime.utcnow)
    raw_text = Column(String, nullable=True) # Unstructured data for Watsonx
    structured_data = Column(JSON, nullable=True) # Extracted data
    status = Column(String, default="pending") # pending, reviewed, rejected

class NeedCategory(str, enum.Enum):
    RESCUE = "rescue"
    MEDICAL = "medical"
    SUPPLY = "supply"

class Need(Base):
    __tablename__ = "needs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=False)
    category = Column(Enum(NeedCategory), nullable=False)
    amount = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    period = Column(String, nullable=True)
    urgency = Column(Integer, default=1) # 1 to 5, 5 being most urgent
    
    zone = relationship("Zone", back_populates="needs")

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    name = Column(String, nullable=False)
    mode = Column(String, nullable=False) # e.g., 'road', 'boat'
    capabilities = Column(JSON, nullable=True)
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    status = Column(String, default="available") # available, committed, maintenance
    version = Column(Integer, default=1)
    
    incident = relationship("Incident", back_populates="resources")

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    snapshot_id = Column(String, nullable=False)
    status = Column(String, default="candidate") # candidate, approved, rejected, stale
    solver_status = Column(String, nullable=True) # OPTIMAL, FEASIBLE, etc.
    policy_version = Column(String, nullable=False)
    incident_revision = Column(Integer, nullable=False, default=1)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    assignments = relationship("Assignment", backref="plan")

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    need_id = Column(UUID(as_uuid=True), ForeignKey("needs.id"), nullable=False)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False)
    amount_assigned = Column(Integer, nullable=False, default=1)
    resource_version = Column(Integer, nullable=False, default=1)
    status = Column(String, default="proposed") # proposed, assigned, acknowledged, en_route, on_site, completed
    version = Column(Integer, default=1)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor = Column(String, nullable=False)
    operation_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    delta = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

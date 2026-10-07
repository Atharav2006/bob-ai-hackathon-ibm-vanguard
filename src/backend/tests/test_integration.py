import os
import asyncio
import threading
import uuid
import pytest
import concurrent.futures
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app import models, auth
from app.database import Base

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.skip("TEST_DATABASE_URL is not set, skipping DB integration tests", allow_module_level=True)
if "test.db" in TEST_DATABASE_URL or "sqlite" in TEST_DATABASE_URL:
    pytest.skip("Requires PostgreSQL for concurrency and constraints", allow_module_level=True)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup DB after suite
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_db):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

def get_auth_headers(db_session, role="admin"):
    # Generate mock token
    from app.auth import create_access_token
    token = create_access_token(data={"sub": "admin", "role": role})
    
    # ensure an incident exists
    inc = db_session.query(models.Incident).first()
    if not inc:
        inc = models.Incident(name="Test", mode="simulation")
        db_session.add(inc)
        db_session.commit()
    
    return {"Authorization": f"Bearer {token}", "X-Incident-ID": str(inc.id)}


def test_public_registration_role(db_session):
    res = client.post("/api/users/", json={"username": f"user_{uuid.uuid4()}", "password": "abc", "role": "admin"})
    assert res.status_code == 200
    assert res.json()["role"] == "responder"

def test_unauthorized_access(db_session):
    res = client.get("/api/incidents/")
    assert res.status_code == 401

def test_report_review_flow(db_session):
    headers = get_auth_headers(db_session)
    # create report
    res = client.post("/api/reports/", json={"source": "test", "observed_at": "2026-01-01T00:00:00Z", "raw_text": "Need 5 kits"}, headers=headers)
    assert res.status_code == 200
    report_id = res.json()["id"]

    # approve without zone -> 400
    res = client.post(f"/api/reports/{report_id}/review", json={"action": "approve", "need_category": "medical"}, headers=headers)
    assert res.status_code == 400
    
    # create zone
    inc_id = headers["X-Incident-ID"]
    zone = models.Zone(incident_id=uuid.UUID(inc_id), name="Test Zone")
    db_session.add(zone)
    db_session.commit()

    # approve with zone -> 200
    res = client.post(f"/api/reports/{report_id}/review", json={"action": "approve", "need_category": "medical", "zone_id": str(zone.id)}, headers=headers)
    assert res.status_code == 200

    report = db_session.query(models.Report).get(report_id)
    assert report.status == "verified"
    needs = db_session.query(models.Need).filter_by(zone_id=zone.id).all()
    assert len(needs) == 1

def test_plan_approval_concurrency(db_session):
    headers = get_auth_headers(db_session)
    inc_id = headers["X-Incident-ID"]
    
    # seed plan
    plan = models.Plan(incident_id=uuid.UUID(inc_id), snapshot_id="snap1", policy_version="v1", incident_revision=1, status="candidate")
    db_session.add(plan)
    db_session.commit()
    
    idempotency_key = f"approve_{plan.id}_{uuid.uuid4()}"
    
    def approve_plan():
        return client.post(f"/api/plans/{plan.id}/approve", json={"expected_version": 1, "idempotency_key": idempotency_key}, headers=headers)
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(approve_plan) for _ in range(3)]
        results = [f.result() for f in futures]
        
    statuses = [r.status_code for r in results]
    # One succeeds, or if all are same idempotency key, they might all return 200 (idempotent replay)
    # The requirement: "Concurrent identical approval retries: one mutation and consistent response replay."
    assert 200 in statuses
    # Ensure plan was approved exactly once (status = approved, version = 2)
    db_session.refresh(plan)
    assert plan.status == "approved"
    assert plan.version == 2
    
    # Different idempotency key should conflict
    res = client.post(f"/api/plans/{plan.id}/approve", json={"expected_version": 1, "idempotency_key": "different_key"}, headers=headers)
    assert res.status_code == 409


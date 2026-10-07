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
from app import models, auth, schemas
from app.database import Base
from app.services.planner import generate_optimized_plan

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
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_db):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

def create_dummy_need_and_resource(db_session, inc):
    zone = models.Zone(incident_id=inc.id, name="Test Zone")
    db_session.add(zone)
    db_session.commit()
    need = models.Need(zone_id=zone.id, category="medical", amount=5.0, unit="units", urgency=3)
    res = models.Resource(incident_id=inc.id, name="Test Res", mode="simulation", capabilities={"medical": 10}, version=1)
    db_session.add_all([need, res])
    db_session.commit()
    return need, res

def get_auth_headers(db_session, role="admin"):
    from app.auth import create_access_token
    token = create_access_token(data={"sub": "admin", "role": role})
    inc = db_session.query(models.Incident).first()
    if not inc:
        inc = models.Incident(name="Test Incident", mode="simulation", revision=1)
        db_session.add(inc)
        db_session.commit()
    return {"Authorization": f"Bearer {token}", "X-Incident-ID": str(inc.id)}


# 1. Zero Demand Test
def test_planner_zero_demand():
    needs = [{"id": str(uuid.uuid4()), "category": "MEDICAL", "amount": 0, "urgency": 5}]
    resources = [{"id": str(uuid.uuid4()), "capabilities": {"medical": 10}, "version": 1}]
    plan = generate_optimized_plan(needs, resources)
    assert len(plan["assignments"]) == 0

# 2. Fractional Quantity Test (ensure rejection)
def test_planner_fractional_quantity_rejection():
    needs = [{"id": str(uuid.uuid4()), "category": "MEDICAL", "amount": 2.5, "urgency": 5}]
    resources = [{"id": str(uuid.uuid4()), "capabilities": {"medical": 10}, "version": 1}]
    try:
        plan = generate_optimized_plan(needs, resources)
        # Should raise ValueError
        assert False, "Should have raised ValueError on fraction"
    except ValueError as e:
        assert "Fractional quantities are not supported" in str(e)

# 3. Category Capacity Total Verification
def test_planner_aggregate_capacity_bug():
    # medical=2, rescue=10. Need: 3 needs of 2 medical. Max allowed across all is 2!
    r_id = str(uuid.uuid4())
    n1 = {"id": str(uuid.uuid4()), "category": "MEDICAL", "amount": 2, "urgency": 5}
    n2 = {"id": str(uuid.uuid4()), "category": "MEDICAL", "amount": 2, "urgency": 5}
    n3 = {"id": str(uuid.uuid4()), "category": "MEDICAL", "amount": 2, "urgency": 5}
    resources = [{"id": r_id, "capabilities": {"medical": 2, "rescue": 10}, "version": 1}]
    
    plan = generate_optimized_plan([n1, n2, n3], resources)
    total_assigned = sum(a["amount_assigned"] for a in plan["assignments"])
    assert total_assigned <= 2


def test_public_registration_role(db_session):
    res = client.post("/api/users/", json={"username": f"user_{uuid.uuid4()}", "password": "abc", "role": "admin"})
    assert res.status_code == 200
    assert res.json()["role"] == "responder"

def test_unauthorized_access(db_session):
    res = client.get("/api/incidents/")
    assert res.status_code == 401

def test_report_review_flow(db_session):
    headers = get_auth_headers(db_session)
    res = client.post("/api/reports/", json={"source": "test", "observed_at": "2026-01-01T00:00:00Z", "raw_text": "Need 5 kits"}, headers=headers)
    report_id = res.json()["id"]

    res = client.post(f"/api/reports/{report_id}/review", json={"action": "approve", "need_category": "medical"}, headers=headers)
    assert res.status_code == 400
    
    inc_id = headers["X-Incident-ID"]
    zone = models.Zone(incident_id=uuid.UUID(inc_id), name="Test Zone")
    db_session.add(zone)
    db_session.commit()

    res = client.post(f"/api/reports/{report_id}/review", json={"action": "approve", "need_category": "medical", "zone_id": str(zone.id)}, headers=headers)
    assert res.status_code == 200

    report = db_session.query(models.Report).get(report_id)
    assert report.status == "verified"
    needs = db_session.query(models.Need).filter_by(zone_id=zone.id).all()
    assert len(needs) == 1


# 4. Concurrency Test A: Same plan, same payload, same key
def test_concurrency_same_plan_same_key(db_session):
    headers = get_auth_headers(db_session)
    inc_id = headers["X-Incident-ID"]
    
    inc = db_session.query(models.Incident).get(uuid.UUID(inc_id))
    need, res = create_dummy_need_and_resource(db_session, inc)
    plan = models.Plan(incident_id=inc.id, snapshot_id="snap_A", policy_version="v1", incident_revision=1, status="candidate", version=1)
    db_session.add(plan)
    db_session.commit()
    
    assign = models.Assignment(plan_id=plan.id, need_id=need.id, resource_id=res.id, amount_assigned=1, resource_version=1, status="candidate")
    db_session.add(assign)
    db_session.commit()
    
    idempotency_key = f"approve_A_{plan.id}"
    payload = {"expected_version": 1, "idempotency_key": idempotency_key}
    
    def approve_plan():
        return client.post(f"/api/plans/{plan.id}/approve", json=payload, headers=headers)
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(approve_plan) for _ in range(3)]
        results = [f.result() for f in futures]
        
    statuses = [r.status_code for r in results]
    assert set(statuses) == {200}
    
    db_session.refresh(plan)
    db_session.refresh(res)
    db_session.refresh(assign)
    
    assert plan.status == "approved"
    assert plan.version == 2
    assert res.status == "committed"
    assert assign.status == "assigned"
    
    audits = db_session.query(models.AuditLog).filter_by(operation_id=str(plan.id)).all()
    assert len(audits) == 1
    
    idem_records = db_session.query(models.IdempotencyRecord).filter_by(key=idempotency_key).all()
    assert len(idem_records) == 1

# Concurrency Test B: Different plans competing for same resource
def test_concurrency_competing_plans(db_session):
    headers = get_auth_headers(db_session)
    inc_id = headers["X-Incident-ID"]
    inc = db_session.query(models.Incident).get(uuid.UUID(inc_id))
    inc.revision = 5
    db_session.commit()
    
    need, res = create_dummy_need_and_resource(db_session, inc)
    
    plan1 = models.Plan(incident_id=uuid.UUID(inc_id), snapshot_id="snap_B1", policy_version="v1", incident_revision=inc.revision, status="candidate", version=1)
    plan2 = models.Plan(incident_id=uuid.UUID(inc_id), snapshot_id="snap_B2", policy_version="v1", incident_revision=inc.revision, status="candidate", version=1)
    db_session.add_all([plan1, plan2])
    db_session.commit()
    
    assign1 = models.Assignment(plan_id=plan1.id, need_id=need.id, resource_id=res.id, amount_assigned=1, resource_version=1, status="candidate")
    assign2 = models.Assignment(plan_id=plan2.id, need_id=need.id, resource_id=res.id, amount_assigned=1, resource_version=1, status="candidate")
    db_session.add_all([assign1, assign2])
    db_session.commit()
    
    def approve_p1():
        return client.post(f"/api/plans/{plan1.id}/approve", json={"expected_version": 1, "idempotency_key": f"p1_{uuid.uuid4()}"}, headers=headers)
        
    def approve_p2():
        return client.post(f"/api/plans/{plan2.id}/approve", json={"expected_version": 1, "idempotency_key": f"p2_{uuid.uuid4()}"}, headers=headers)
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(approve_p1)
        f2 = executor.submit(approve_p2)
        r1, r2 = f1.result(), f2.result()
        
    statuses = [r1.status_code, r2.status_code]
    assert 200 in statuses
    assert 409 in statuses

# Concurrency Test C: Same key, different target/payload
def test_concurrency_same_key_different_payload(db_session):
    headers = get_auth_headers(db_session)
    inc_id = headers["X-Incident-ID"]
    
    inc = db_session.query(models.Incident).get(uuid.UUID(inc_id))
    need, res = create_dummy_need_and_resource(db_session, inc)
    
    plan = models.Plan(incident_id=inc.id, snapshot_id="snap_C", policy_version="v1", incident_revision=1, status="candidate", version=1)
    db_session.add(plan)
    db_session.commit()
    
    assign = models.Assignment(plan_id=plan.id, need_id=need.id, resource_id=res.id, amount_assigned=1, resource_version=1, status="candidate")
    db_session.add(assign)
    db_session.commit()
    
    key = f"idem_{uuid.uuid4()}"
    
    # 1. Success with payload A
    res1 = client.post(f"/api/plans/{plan.id}/approve", json={"expected_version": 1, "idempotency_key": key}, headers=headers)
    assert res1.status_code == 200
    
    # 2. Conflict with payload B (no expected version)
    res2 = client.post(f"/api/plans/{plan.id}/approve", json={"idempotency_key": key}, headers=headers)
    assert res2.status_code == 409

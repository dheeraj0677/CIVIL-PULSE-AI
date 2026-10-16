"""Tests for the CivicPulse AI Web Suite (Classifier, Database, and REST API)."""

import pytest
from fastapi.testclient import TestClient

from web.classifier import ComplaintClassifier
from web.database import (
    approve_complaint,
    authenticate_user,
    get_all_workers,
    get_complaint,
    get_officer_queue,
    get_worker_tasks,
    init_database,
    insert_complaint,
    update_worker_status,
)
from web.server import app

client = TestClient(app)


def test_classifier_nlp():
    """Verify complaint text classification and severity inference."""
    clf = ComplaintClassifier()

    # Category classification
    cat1, _ = clf.classify_text("Massive 2-foot pothole on main road")
    assert cat1 == "Road damage"

    cat2, _ = clf.classify_text("Stormwater drain overflowing with sewage after rain")
    assert cat2 == "Drainage"

    cat3, _ = clf.classify_text("Traffic signal flashing red at intersection")
    assert cat3 == "Traffic"

    # Severity inference with hospital corridor context
    loc_meta = {
        "near_hospital": 1,
        "near_school": 0,
        "road_condition": "Poor",
        "pedestrian_activity": "High",
        "zone": "ZONE_01",
        "road_type": "Local",
        "population_density_per_km2": 8000,
    }
    assessment = clf.assess_complaint(
        description="Hazardous pothole blocking ambulances",
        location_id="L0002",
        location_meta=loc_meta,
        user_urgency="Urgent",
    )
    assert assessment["inferred_severity"] in ["High", "Critical"]
    assert assessment["priority_score"] >= 75.0
    assert assessment["priority_tier"] in ["HIGH", "CRITICAL"]
    assert assessment["estimated_resolution_hours"] > 0


def test_database_crud():
    """Verify database insertion, retrieval, and status workflow."""
    init_database()

    # Authenticate officer
    user = authenticate_user("officer@smartcity.gov", "password123")
    assert user is not None
    assert user["role"] == "officer"

    # Insert complaint
    ticket_data = {
        "description": "Clogged storm drain on arterial road",
        "location_id": "L0001",
        "category": "Drainage",
        "severity": "High",
        "priority_score": 88.5,
        "priority_tier": "HIGH",
        "department": "Drainage Division",
        "estimated_resolution_hours": 12.0,
        "citizen_contact": "test@test.com",
        "citizen_urgency": "Urgent",
        "image_url": "",
        "rationale": "High priority test",
    }
    ticket_id = insert_complaint(ticket_data)
    assert ticket_id.startswith("CP-2026-")

    # Retrieve complaint
    ticket = get_complaint(ticket_id)
    assert ticket is not None
    assert ticket["status"] == "Pending Approval"
    assert ticket["priority_score"] == 88.5

    # Officer queue should be sorted descending by priority_score
    queue = get_officer_queue()
    assert len(queue) > 0
    scores = [q["priority_score"] for q in queue]
    assert scores == sorted(scores, reverse=True)

    # Approve and assign to worker
    workers = get_all_workers()
    assert len(workers) > 0
    target_worker_id = workers[0]["id"]

    success = approve_complaint(
        ticket_id=ticket_id,
        officer_id="USR-001",
        worker_id=target_worker_id,
        department="Drainage Division",
    )
    assert success is True

    # Verify status changed to Approved
    updated_ticket = get_complaint(ticket_id)
    assert updated_ticket["status"] == "Approved"
    assert updated_ticket["assigned_worker_id"] == target_worker_id

    # Worker views task
    tasks = get_worker_tasks(target_worker_id)
    task_ids = [t["ticket_id"] for t in tasks]
    assert ticket_id in task_ids

    # Worker marks in progress
    update_worker_status(ticket_id, target_worker_id, "In Progress", "Crew on site")
    in_prog_ticket = get_complaint(ticket_id)
    assert in_prog_ticket["status"] == "In Progress"

    # Worker marks resolved
    update_worker_status(ticket_id, target_worker_id, "Resolved", "Drain unblocked", actual_hours=3.5)
    resolved_ticket = get_complaint(ticket_id)
    assert resolved_ticket["status"] == "Resolved"
    assert resolved_ticket["actual_resolution_hours"] == 3.5


def test_api_endpoints():
    """Verify end-to-end REST API workflows."""
    # 1. GET / serves index.html
    res = client.get("/")
    assert res.status_code == 200
    assert "CivicPulse AI" in res.text

    # 2. POST /api/complaints/analyze
    res = client.post(
        "/api/complaints/analyze",
        json={
            "description": "Streetlight outage dark road",
            "location_id": "L0001",
            "user_urgency": "Standard",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["assessment"]["predicted_category"] == "Lighting"

    # 3. POST /api/complaints/submit (Citizen, no login)
    res = client.post(
        "/api/complaints/submit",
        json={
            "description": "Deep pothole damaging vehicles",
            "location_id": "L0002",
            "user_urgency": "Urgent",
            "citizen_contact": "citizen@test.com",
        },
    )
    assert res.status_code == 200
    sub_data = res.json()
    assert sub_data["status"] == "success"
    ticket_id = sub_data["ticket_id"]

    # 4. GET /api/complaints/track/{ticket_id} (Citizen tracker)
    res = client.get(f"/api/complaints/track/{ticket_id}")
    assert res.status_code == 200
    track_data = res.json()
    assert track_data["ticket"]["ticket_id"] == ticket_id
    assert track_data["ticket"]["status"] == "Pending Approval"

    # 5. POST /api/auth/login (Officer Login)
    res = client.post(
        "/api/auth/login",
        json={"email": "officer@smartcity.gov", "password": "password123"},
    )
    assert res.status_code == 200
    auth_data = res.json()
    assert auth_data["user"]["role"] == "officer"

    # 6. GET /api/officer/queue
    res = client.get("/api/officer/queue")
    assert res.status_code == 200
    q_data = res.json()
    assert len(q_data["queue"]) > 0

    # 7. POST /api/officer/approve/{ticket_id}
    res = client.post(
        f"/api/officer/approve/{ticket_id}",
        json={
            "officer_id": "USR-001",
            "worker_id": "USR-002",
            "department": "Road Maintenance",
        },
    )
    assert res.status_code == 200

    # 8. GET /api/worker/tasks/USR-002
    res = client.get("/api/worker/tasks/USR-002")
    assert res.status_code == 200
    w_data = res.json()
    w_ticket_ids = [t["ticket_id"] for t in w_data["tasks"]]
    assert ticket_id in w_ticket_ids

    # 9. POST /api/worker/update/{ticket_id}
    res = client.post(
        f"/api/worker/update/{ticket_id}",
        json={
            "worker_id": "USR-002",
            "new_status": "Resolved",
            "worker_notes": "Filled with asphalt patch.",
            "actual_hours": 1.5,
        },
    )
    assert res.status_code == 200

    # Verify tracking reflects Resolved
    res = client.get(f"/api/complaints/track/{ticket_id}")
    assert res.json()["ticket"]["status"] == "Resolved"

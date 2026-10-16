"""FastAPI Web Server for CivicPulse AI.

Provides the REST API and serves the single-page application for Citizens,
Government Officers, and Field Crew Workers.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.data_loader import load_locations
from web.classifier import ComplaintClassifier
from web.database import (
    approve_complaint,
    authenticate_user,
    get_all_workers,
    get_complaint,
    get_officer_queue,
    get_public_feed,
    get_system_kpis,
    get_worker_history,
    get_worker_tasks,
    init_database,
    insert_complaint,
    update_worker_status,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="CivicPulse AI Smart City Portal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
init_database()

# Cache location dictionary for quick lookup
locations_df = load_locations()
LOCATIONS_DICT = {
    row["location_id"]: {
        "location_id": row["location_id"],
        "zone": row["zone"],
        "road_type": row["road_type"],
        "road_condition": row["road_condition"],
        "pedestrian_activity": row["pedestrian_activity"],
        "population_density_per_km2": int(row["population_density_per_km2"]),
        "near_school": int(row["near_school"]),
        "near_hospital": int(row["near_hospital"]),
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
    }
    for _, row in locations_df.iterrows()
}

classifier = ComplaintClassifier()

# Mount static folder
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Pydantic Request Models
class AnalyzeRequest(BaseModel):
    description: str
    location_id: str
    user_urgency: Optional[str] = "Standard"
    user_category: Optional[str] = None


class SubmitComplaintRequest(BaseModel):
    description: str
    location_id: str
    user_urgency: Optional[str] = "Standard"
    user_category: Optional[str] = None
    citizen_contact: Optional[str] = ""
    image_url: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class OfficerApproveRequest(BaseModel):
    officer_id: str
    worker_id: str
    department: str
    adjusted_severity: Optional[str] = None
    adjusted_priority_score: Optional[float] = None


class WorkerUpdateRequest(BaseModel):
    worker_id: str
    new_status: str
    worker_notes: str
    actual_hours: Optional[float] = None


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main Single Page Application."""
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html template not found")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/locations")
async def list_locations():
    """Return list of monitored city locations with physical context."""
    return list(LOCATIONS_DICT.values())


@app.post("/api/complaints/analyze")
async def analyze_complaint(req: AnalyzeRequest):
    """Run real-time NLP classification and MCDA priority assessment."""
    loc_meta = LOCATIONS_DICT.get(req.location_id, {})
    assessment = classifier.assess_complaint(
        description=req.description,
        location_id=req.location_id,
        location_meta=loc_meta,
        user_urgency=req.user_urgency or "Standard",
        user_category=req.user_category,
    )
    return {
        "status": "success",
        "assessment": assessment,
        "location": loc_meta,
    }


@app.post("/api/complaints/submit")
async def submit_complaint(req: SubmitComplaintRequest):
    """Public citizen complaint submission without login."""
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty.")
    if req.location_id not in LOCATIONS_DICT:
        raise HTTPException(status_code=400, detail=f"Invalid location_id: {req.location_id}")

    loc_meta = LOCATIONS_DICT[req.location_id]

    # Perform automated NLP & MCDA assessment
    assessment = classifier.assess_complaint(
        description=req.description,
        location_id=req.location_id,
        location_meta=loc_meta,
        user_urgency=req.user_urgency or "Standard",
        user_category=req.user_category,
    )

    complaint_data = {
        "description": req.description,
        "location_id": req.location_id,
        "category": assessment["predicted_category"],
        "severity": assessment["inferred_severity"],
        "priority_score": assessment["priority_score"],
        "priority_tier": assessment["priority_tier"],
        "department": f"{assessment['predicted_category']} Division",
        "estimated_resolution_hours": assessment["estimated_resolution_hours"],
        "citizen_contact": req.citizen_contact or "",
        "citizen_urgency": req.user_urgency or "Standard",
        "image_url": req.image_url or "",
        "rationale": assessment["rationale"],
    }

    ticket_id = insert_complaint(complaint_data)

    return {
        "status": "success",
        "ticket_id": ticket_id,
        "assessment": assessment,
        "message": "Complaint successfully registered and prioritized for civil officer review.",
    }


@app.get("/api/complaints/track/{ticket_id}")
async def track_complaint(ticket_id: str):
    """Public complaint tracking for citizens using their ticket ID."""
    ticket = get_complaint(ticket_id.strip().upper())
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    loc = LOCATIONS_DICT.get(ticket["location_id"], {})
    return {
        "status": "success",
        "ticket": ticket,
        "location": loc,
    }


@app.get("/api/complaints/public")
async def public_feed(limit: int = 25):
    """Public live hazard feed for civic transparency."""
    feed = get_public_feed(limit)
    return {"status": "success", "feed": feed}


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """Authenticate officer or worker credentials."""
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials. Use provided demo logins.")
    return {"status": "success", "user": user}


@app.get("/api/officer/queue")
async def officer_queue(status: Optional[str] = None):
    """Retrieve all complaints strictly sorted by priority_score DESC."""
    queue = get_officer_queue(status_filter=status)
    # Augment with location metadata
    for item in queue:
        item["location_meta"] = LOCATIONS_DICT.get(item["location_id"], {})
    return {"status": "success", "queue": queue}


@app.get("/api/officer/workers")
async def list_workers():
    """Retrieve available field workers for dispatch assignment."""
    workers = get_all_workers()
    return {"status": "success", "workers": workers}


@app.post("/api/officer/approve/{ticket_id}")
async def officer_approve(ticket_id: str, req: OfficerApproveRequest):
    """Government officer approves and assigns a complaint to a field worker."""
    success = approve_complaint(
        ticket_id=ticket_id,
        officer_id=req.officer_id,
        worker_id=req.worker_id,
        department=req.department,
        adjusted_severity=req.adjusted_severity,
        adjusted_priority_score=req.adjusted_priority_score,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Complaint not found or update failed.")
    return {"status": "success", "message": f"Ticket {ticket_id} approved and dispatched."}


@app.get("/api/worker/tasks/{worker_id}")
async def worker_tasks(worker_id: str):
    """Retrieve field worker's assigned tasks sorted by priority."""
    tasks = get_worker_tasks(worker_id)
    history = get_worker_history(worker_id)
    for t in tasks:
        t["location_meta"] = LOCATIONS_DICT.get(t["location_id"], {})
    return {
        "status": "success",
        "tasks": tasks,
        "completed": history,
    }


@app.post("/api/worker/update/{ticket_id}")
async def worker_update(ticket_id: str, req: WorkerUpdateRequest):
    """Field worker updates task status (In Progress or Resolved)."""
    success = update_worker_status(
        ticket_id=ticket_id,
        worker_id=req.worker_id,
        new_status=req.new_status,
        worker_notes=req.worker_notes,
        actual_hours=req.actual_hours,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found or authorization error.")
    return {"status": "success", "message": f"Ticket {ticket_id} marked as {req.new_status}."}


@app.get("/api/kpis")
async def system_kpis():
    """Real-time operational metrics across all city tickets."""
    kpis = get_system_kpis()
    return {"status": "success", "kpis": kpis}

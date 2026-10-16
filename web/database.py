"""SQLite Database and State Persistence Module for CivicPulse AI Web Suite.

Manages complaints, role-based users, dispatch assignments, and audit trails.
"""

from datetime import datetime
import json
from pathlib import Path
import random
import sqlite3
from typing import Any, Dict, List, Optional
import pandas as pd

from src.config import ARTIFACTS_DIR, COMPLAINTS_PATH, LOCATIONS_PATH

DB_PATH = ARTIFACTS_DIR / "civicpulse.db"

DEMO_USERS = [
    {
        "id": "USR-001",
        "username": "officer_sharma",
        "email": "officer@smartcity.gov",
        "password": "password123",
        "role": "officer",
        "full_name": "Chief Eng. Rajesh Sharma",
        "department": "Municipal Works & Civil Infrastructure",
    },
    {
        "id": "USR-002",
        "username": "worker_vikram",
        "email": "worker@smartcity.gov",
        "password": "password123",
        "role": "worker",
        "full_name": "Vikram Singh (Crew Lead)",
        "department": "Road Maintenance & Pothole Squad",
    },
    {
        "id": "USR-003",
        "username": "worker_anil",
        "email": "electrical@smartcity.gov",
        "password": "password123",
        "role": "worker",
        "full_name": "Anil Kumar (Specialist)",
        "department": "Traffic Signals & Streetlight Unit",
    },
    {
        "id": "USR-004",
        "username": "worker_priya",
        "email": "sanitation@smartcity.gov",
        "password": "password123",
        "role": "worker",
        "full_name": "Priya Patel (Field Inspector)",
        "department": "Drainage & Water Safety Division",
    },
]


def get_db_connection() -> sqlite3.Connection:
    """Return a connection with row factory configured."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Create tables and seed initial data if database does not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            full_name TEXT,
            department TEXT
        )
        """
    )

    # Complaints table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS complaints (
            ticket_id TEXT PRIMARY KEY,
            description TEXT,
            location_id TEXT,
            category TEXT,
            severity TEXT,
            priority_score REAL,
            priority_tier TEXT,
            status TEXT,
            assigned_officer_id TEXT,
            assigned_worker_id TEXT,
            assigned_department TEXT,
            estimated_resolution_hours REAL,
            actual_resolution_hours REAL,
            citizen_contact TEXT,
            citizen_urgency TEXT,
            image_url TEXT,
            rationale TEXT,
            worker_notes TEXT,
            created_at TEXT,
            updated_at TEXT,
            resolved_at TEXT
        )
        """
    )

    # Insert demo users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        for u in DEMO_USERS:
            cursor.execute(
                """
                INSERT INTO users (id, username, email, password, role, full_name, department)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (u["id"], u["username"], u["email"], u["password"], u["role"], u["full_name"], u["department"]),
            )

    # Seed sample complaints if empty
    cursor.execute("SELECT COUNT(*) FROM complaints")
    if cursor.fetchone()[0] == 0:
        seed_sample_complaints(cursor)

    conn.commit()
    conn.close()


def seed_sample_complaints(cursor: sqlite3.Cursor):
    """Seed realistic initial complaints from dataset and rich scenarios."""
    initial_samples = [
        {
            "ticket_id": "CP-2026-1001",
            "description": "Massive deep pothole right outside school entrance causing severe vehicle damage and near collisions during student dismissal.",
            "location_id": "L0002",
            "category": "Road damage",
            "severity": "Critical",
            "priority_score": 96.5,
            "priority_tier": "CRITICAL",
            "status": "Pending Approval",
            "assigned_officer_id": None,
            "assigned_worker_id": None,
            "assigned_department": "Road Maintenance & Pothole Squad",
            "estimated_resolution_hours": 14.5,
            "actual_resolution_hours": None,
            "citizen_contact": "citizen99@example.com",
            "citizen_urgency": "Life Hazard",
            "image_url": "https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600&auto=format&fit=crop&q=80",
            "rationale": "High hazard risk: Adjacent to hospital corridor and school zone with Poor road condition.",
            "worker_notes": None,
            "created_at": "2026-10-16 08:30:00",
            "updated_at": "2026-10-16 08:30:00",
            "resolved_at": None,
        },
        {
            "ticket_id": "CP-2026-1002",
            "description": "Storm drain clogged with heavy debris; black wastewater overflowing across three lanes after early morning rainfall.",
            "location_id": "L0116",
            "category": "Drainage",
            "severity": "High",
            "priority_score": 88.0,
            "priority_tier": "HIGH",
            "status": "Pending Approval",
            "assigned_officer_id": None,
            "assigned_worker_id": None,
            "assigned_department": "Drainage & Water Safety Division",
            "estimated_resolution_hours": 18.0,
            "actual_resolution_hours": None,
            "citizen_contact": "9876543210",
            "citizen_urgency": "Urgent",
            "image_url": "https://images.unsplash.com/photo-1541888946425-d0fbb1861593?w=600&auto=format&fit=crop&q=80",
            "rationale": "Waterlogging on high-density collector corridor.",
            "worker_notes": None,
            "created_at": "2026-10-16 09:15:00",
            "updated_at": "2026-10-16 09:15:00",
            "resolved_at": None,
        },
        {
            "ticket_id": "CP-2026-1003",
            "description": "Traffic signal malfunctioning at junction - flashing irregular red and green simultaneously, causing gridlock.",
            "location_id": "L0428",
            "category": "Traffic",
            "severity": "High",
            "priority_score": 84.5,
            "priority_tier": "HIGH",
            "status": "Approved",
            "assigned_officer_id": "USR-001",
            "assigned_worker_id": "USR-003",
            "assigned_department": "Traffic Signals & Streetlight Unit",
            "estimated_resolution_hours": 8.0,
            "actual_resolution_hours": None,
            "citizen_contact": "traffic_watcher@gmail.com",
            "citizen_urgency": "Urgent",
            "image_url": "https://images.unsplash.com/photo-1508873696983-2df5293cb32b?w=600&auto=format&fit=crop&q=80",
            "rationale": "Officer approved: Dispatched to electrical squad for immediate relay box inspection.",
            "worker_notes": "Crew dispatched with diagnostic scanner.",
            "created_at": "2026-10-16 07:10:00",
            "updated_at": "2026-10-16 09:45:00",
            "resolved_at": None,
        },
        {
            "ticket_id": "CP-2026-1004",
            "description": "Five streetlights completely dead along pedestrian stretch behind municipal park. Pitch black at night.",
            "location_id": "L0802",
            "category": "Lighting",
            "severity": "Medium",
            "priority_score": 62.0,
            "priority_tier": "MEDIUM",
            "status": "In Progress",
            "assigned_officer_id": "USR-001",
            "assigned_worker_id": "USR-003",
            "assigned_department": "Traffic Signals & Streetlight Unit",
            "estimated_resolution_hours": 24.0,
            "actual_resolution_hours": None,
            "citizen_contact": "nightwalker@city.org",
            "citizen_urgency": "Standard",
            "image_url": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=600&auto=format&fit=crop&q=80",
            "rationale": "Lighting failure on residential collector road.",
            "worker_notes": "Bucket truck on site replacing blown LED drivers.",
            "created_at": "2026-10-15 20:00:00",
            "updated_at": "2026-10-16 10:30:00",
            "resolved_at": None,
        },
        {
            "ticket_id": "CP-2026-1005",
            "description": "Large trash pile and rotting organic waste discarded on sidewalk near food market, blocking walkway.",
            "location_id": "L0957",
            "category": "Waste",
            "severity": "Medium",
            "priority_score": 55.0,
            "priority_tier": "MEDIUM",
            "status": "Resolved",
            "assigned_officer_id": "USR-001",
            "assigned_worker_id": "USR-004",
            "assigned_department": "Drainage & Water Safety Division",
            "estimated_resolution_hours": 12.0,
            "actual_resolution_hours": 4.5,
            "citizen_contact": "shopowner@market.in",
            "citizen_urgency": "Standard",
            "image_url": "https://images.unsplash.com/photo-1605600659908-0ef719419d41?w=600&auto=format&fit=crop&q=80",
            "rationale": "Sidewalk obstruction cleared by sanitation compactors.",
            "worker_notes": "Waste cleared with mechanical backhoe. Sidewalk sanitized.",
            "created_at": "2026-10-15 11:20:00",
            "updated_at": "2026-10-15 16:00:00",
            "resolved_at": "2026-10-15 16:00:00",
        },
    ]

    for item in initial_samples:
        cursor.execute(
            """
            INSERT INTO complaints (
                ticket_id, description, location_id, category, severity,
                priority_score, priority_tier, status, assigned_officer_id,
                assigned_worker_id, assigned_department, estimated_resolution_hours,
                actual_resolution_hours, citizen_contact, citizen_urgency,
                image_url, rationale, worker_notes, created_at, updated_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["ticket_id"], item["description"], item["location_id"],
                item["category"], item["severity"], item["priority_score"],
                item["priority_tier"], item["status"], item["assigned_officer_id"],
                item["assigned_worker_id"], item["assigned_department"],
                item["estimated_resolution_hours"], item["actual_resolution_hours"],
                item["citizen_contact"], item["citizen_urgency"], item["image_url"],
                item["rationale"], item["worker_notes"], item["created_at"],
                item["updated_at"], item["resolved_at"],
            ),
        )


def insert_complaint(complaint_data: Dict[str, Any]) -> str:
    """Insert a new citizen complaint and return the generated ticket_id."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate ticket ID: CP-2026-XXXX
    rand_num = random.randint(1100, 9999)
    ticket_id = f"CP-2026-{rand_num}"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO complaints (
            ticket_id, description, location_id, category, severity,
            priority_score, priority_tier, status, assigned_officer_id,
            assigned_worker_id, assigned_department, estimated_resolution_hours,
            actual_resolution_hours, citizen_contact, citizen_urgency,
            image_url, rationale, worker_notes, created_at, updated_at, resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            complaint_data["description"],
            complaint_data["location_id"],
            complaint_data["category"],
            complaint_data["severity"],
            complaint_data["priority_score"],
            complaint_data["priority_tier"],
            "Pending Approval",
            None,
            None,
            complaint_data.get("department", "Municipal Works & Civil Infrastructure"),
            complaint_data.get("estimated_resolution_hours", 24.0),
            None,
            complaint_data.get("citizen_contact", ""),
            complaint_data.get("citizen_urgency", "Standard"),
            complaint_data.get("image_url", ""),
            complaint_data.get("rationale", ""),
            None,
            now,
            now,
            None,
        ),
    )
    conn.commit()
    conn.close()
    return ticket_id


def get_complaint(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve single complaint by ticket ID."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM complaints WHERE ticket_id = ?", (ticket_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_officer_queue(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all complaints for Officer review, strictly ordered by priority_score DESC."""
    conn = get_db_connection()
    if status_filter:
        rows = conn.execute(
            """
            SELECT * FROM complaints 
            WHERE status = ? 
            ORDER BY priority_score DESC, created_at DESC
            """,
            (status_filter,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT * FROM complaints 
            ORDER BY priority_score DESC, created_at DESC
            """
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_worker_tasks(worker_id: str) -> List[Dict[str, Any]]:
    """Return tasks assigned to a specific field worker, ordered by priority_score DESC."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT * FROM complaints 
        WHERE assigned_worker_id = ? AND status IN ('Approved', 'In Progress')
        ORDER BY priority_score DESC, created_at DESC
        """,
        (worker_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_worker_history(worker_id: str) -> List[Dict[str, Any]]:
    """Return completed tasks for a worker."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT * FROM complaints 
        WHERE assigned_worker_id = ? AND status = 'Resolved'
        ORDER BY resolved_at DESC
        """,
        (worker_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def approve_complaint(
    ticket_id: str,
    officer_id: str,
    worker_id: str,
    department: str,
    adjusted_severity: Optional[str] = None,
    adjusted_priority_score: Optional[float] = None,
) -> bool:
    """Officer approves a complaint and assigns it to a field worker."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        UPDATE complaints
        SET status = 'Approved',
            assigned_officer_id = ?,
            assigned_worker_id = ?,
            assigned_department = ?,
            severity = COALESCE(?, severity),
            priority_score = COALESCE(?, priority_score),
            updated_at = ?
        WHERE ticket_id = ?
        """,
        (officer_id, worker_id, department, adjusted_severity, adjusted_priority_score, now, ticket_id),
    )
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def update_worker_status(
    ticket_id: str,
    worker_id: str,
    new_status: str,
    worker_notes: str,
    actual_hours: Optional[float] = None,
) -> bool:
    """Worker updates ticket status (In Progress or Resolved)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resolved_at = now if new_status == "Resolved" else None

    cursor.execute(
        """
        UPDATE complaints
        SET status = ?,
            worker_notes = ?,
            actual_resolution_hours = COALESCE(?, actual_resolution_hours),
            updated_at = ?,
            resolved_at = COALESCE(?, resolved_at)
        WHERE ticket_id = ? AND assigned_worker_id = ?
        """,
        (new_status, worker_notes, actual_hours, now, resolved_at, ticket_id, worker_id),
    )
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def get_public_feed(limit: int = 25) -> List[Dict[str, Any]]:
    """Return recent public complaints for the public citizen live feed."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT ticket_id, location_id, category, severity, status, priority_tier,
               created_at, resolved_at, description
        FROM complaints
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_system_kpis() -> Dict[str, Any]:
    """Return real-time operational counts across all tickets."""
    conn = get_db_connection()
    cursor = conn.cursor()

    total = cursor.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Pending Approval'").fetchone()[0]
    approved = cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Approved'").fetchone()[0]
    in_progress = cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'").fetchone()[0]
    resolved = cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'").fetchone()[0]
    critical = cursor.execute("SELECT COUNT(*) FROM complaints WHERE priority_tier = 'CRITICAL'").fetchone()[0]

    avg_hrs_row = cursor.execute("SELECT AVG(actual_resolution_hours) FROM complaints WHERE actual_resolution_hours IS NOT NULL").fetchone()
    avg_hrs = round(avg_hrs_row[0], 1) if avg_hrs_row and avg_hrs_row[0] else 16.5

    conn.close()
    return {
        "total_tickets": total,
        "pending_approval": pending,
        "approved": approved,
        "in_progress": in_progress,
        "resolved": resolved,
        "critical_count": critical,
        "avg_resolution_hours": avg_hrs,
    }


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify user credentials."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT id, username, email, role, full_name, department FROM users WHERE email = ? AND password = ?",
        (email.strip(), password.strip()),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_workers() -> List[Dict[str, Any]]:
    """Retrieve list of field workers for assignment dropdown."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, username, full_name, department FROM users WHERE role = 'worker'"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

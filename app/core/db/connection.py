"""
Database Connection & Schema Management for LabLink Platform
Provides:
- Resilient database path resolution (Vercel / Lambda ephemeral /tmp fallback)
- Safe SQLite connection with WAL journal mode (and DELETE fallback)
- Table DDL schemas with indexes matching all test fixtures
- Initial seed data population
"""

import os
import sqlite3
import json
import time
import tempfile
from typing import Optional
from app.core.seed_data import SEED_EQUIPMENT


def get_db_path() -> str:
    """
    Determines database path with robust fallback for serverless environments
    (Vercel, AWS Lambda, read-only containers).
    """
    if os.environ.get("DATABASE_PATH"):
        return os.environ["DATABASE_PATH"]

    tmp_dir = os.environ.get("TMPDIR") or tempfile.gettempdir() or "/tmp"
    fallback_path = os.path.join(tmp_dir, "lablink.db")

    serverless_indicators = (
        "VERCEL",
        "VERCEL_ENV",
        "VERCEL_URL",
        "VERCEL_REGION",
        "AWS_LAMBDA_FUNCTION_NAME",
        "LAMBDA_TASK_ROOT",
        "NOW_REGION"
    )
    if any(os.environ.get(k) for k in serverless_indicators):
        return fallback_path

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        test_file = os.path.join(data_dir, ".write_test")
        with open(test_file, "w") as f:
            f.write("ok")
        if os.path.exists(test_file):
            os.remove(test_file)
        return os.path.join(data_dir, "lablink.db")
    except Exception:
        return fallback_path


def create_connection(db_path: str) -> sqlite3.Connection:
    """Creates a configured SQLite connection with safe pragmas."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        try:
            conn.execute("PRAGMA journal_mode = DELETE;")
        except Exception:
            pass
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
    except Exception:
        pass
    return conn


def init_schema(conn: sqlite3.Connection):
    """Initializes all database tables and indexes."""
    cursor = conn.cursor()

    # 1. Equipment Inventory
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT NOT NULL,
        specifications_json TEXT,
        safety_level TEXT DEFAULT 'Standard',
        tier TEXT DEFAULT 'MID_RANGE',
        hourly_cost_estimate TEXT DEFAULT '$2.00/hr',
        hourly_rate REAL DEFAULT 2.00,
        status TEXT DEFAULT 'OPERATIONAL',
        tags_json TEXT
    );
    """)

    # 2. Date-Partitioned Bitmask Availability (equipment_id, booking_date)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS date_slot_availability (
        equipment_id TEXT NOT NULL,
        booking_date TEXT NOT NULL,
        bitmask INTEGER DEFAULT 0,
        updated_at REAL NOT NULL,
        PRIMARY KEY (equipment_id, booking_date)
    );
    """)

    # 3. Bookings with Leased Hold and Cryptographic Signatures
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id TEXT PRIMARY KEY,
        equipment_id TEXT NOT NULL,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        project_id TEXT,
        project_title TEXT,
        booking_date TEXT NOT NULL,
        slot_index INTEGER NOT NULL,
        duration_slots INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT NOT NULL,
        lease_expires_at REAL NOT NULL,
        state_signature TEXT NOT NULL,
        purpose_abstract TEXT,
        created_at REAL NOT NULL
    );
    """)

    # 4. Project Proposals (Faculty Approvals)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_proposals (
        id TEXT PRIMARY KEY,
        project_title TEXT NOT NULL,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        faculty_advisor TEXT NOT NULL,
        target_equipment_id TEXT NOT NULL,
        submission_deadline_days INTEGER NOT NULL,
        academic_tier TEXT NOT NULL,
        abstract TEXT,
        status TEXT DEFAULT 'PENDING',
        faculty_notes TEXT,
        ai_evaluation_json TEXT,
        created_at REAL NOT NULL
    );
    """)

    # 5. Server-Verified Student Profiles (Anti-Spoofing)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_profiles (
        student_id TEXT PRIMARY KEY,
        student_name TEXT NOT NULL,
        department TEXT NOT NULL,
        academic_tier TEXT DEFAULT 'capstone',
        historical_hours_used REAL DEFAULT 4.0,
        current_deadline_days REAL DEFAULT 3.0,
        has_safety_cert INTEGER DEFAULT 1
    );
    """)

    # 6. IRCTC Waiting List (WL-1 Queue)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS waiting_list (
        id TEXT PRIMARY KEY,
        equipment_id TEXT NOT NULL,
        booking_date TEXT NOT NULL,
        slot_index INTEGER NOT NULL,
        duration_slots INTEGER NOT NULL,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        project_title TEXT,
        priority_score REAL NOT NULL,
        created_at REAL NOT NULL
    );
    """)

    # 7. GenAI Copilot Response Cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS copilot_cache (
        query_hash TEXT PRIMARY KEY,
        prompt_text TEXT NOT NULL,
        response_json TEXT NOT NULL,
        created_at REAL NOT NULL
    );
    """)

    # 8. Rate Limit Hits
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rate_limit_hits (
        client_key TEXT NOT NULL,
        hit_timestamp REAL NOT NULL
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_slots_eq_date ON date_slot_availability(equipment_id, booking_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_date_slot ON bookings(equipment_id, booking_date, slot_index);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_lease ON bookings(status, lease_expires_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_status ON project_proposals(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_key ON rate_limit_hits(client_key, hit_timestamp);")
    conn.commit()


def seed_initial_data(conn: sqlite3.Connection):
    """Seeds initial inventory, students, and proposals if tables are empty."""
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM equipment;")
    if cursor.fetchone()["cnt"] == 0:
        for it in SEED_EQUIPMENT:
            rate = 2.0
            try:
                rate = float(it.get("hourly_cost_estimate", "$2.00").replace("$", "").replace("/hr", "").strip())
            except Exception:
                pass

            cursor.execute("""
            INSERT OR IGNORE INTO equipment (
                id, name, department, category, location, specifications_json,
                safety_level, tier, hourly_cost_estimate, hourly_rate, status, tags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                it["id"],
                it["name"],
                it["department"],
                it["category"],
                it["location"],
                json.dumps(it.get("specifications", {})),
                it.get("safety_level", "Standard"),
                it.get("tier", "MID_RANGE"),
                it.get("hourly_cost_estimate", f"${rate:.2f}/hr"),
                rate,
                it.get("status", "OPERATIONAL"),
                json.dumps(it.get("tags", []))
            ))

    cursor.execute("SELECT COUNT(*) as cnt FROM student_profiles;")
    if cursor.fetchone()["cnt"] == 0:
        initial_students = [
            ("stu_maya_01", "Maya Lin", "Computer Science & Engineering", "capstone", 2.0, 0.25, 1),
            ("stu_arjun_01", "Arjun Sharma", "Electronics & Communication", "capstone", 6.5, 2.5, 1),
            ("stu_priya_02", "Priya Patel", "Computer Science", "capstone", 28.0, 5.0, 1),
            ("stu_rohit_03", "Rohit Verma", "Mechanical & Robotics", "coursework", 3.0, 8.0, 1),
            ("stu_ananya_04", "Ananya Deshmukh", "Biotechnology", "funded_research", 12.0, 1.5, 1),
            ("stu_karan_05", "Karan Malhotra", "Computer Science", "independent", 42.0, 14.0, 0),
            ("stu_kian_02", "Kian Patel", "Electronics & Communication", "coursework", 28.0, 14.0, 1)
        ]
        cursor.executemany("""
        INSERT OR IGNORE INTO student_profiles (
            student_id, student_name, department, academic_tier,
            historical_hours_used, current_deadline_days, has_safety_cert
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, initial_students)

    cursor.execute("SELECT COUNT(*) as cnt FROM project_proposals;")
    if cursor.fetchone()["cnt"] == 0:
        sample_proposals = [
            (
                "prop_maya_01",
                "CS-492 · Autonomous Vision & NeRF SLAM",
                "stu_maya_01",
                "Maya Lin",
                "Dr. Aris Thorne (Faculty, AI Lab)",
                "equip_rtx_01",
                2,
                "capstone",
                "High-throughput visual transformer training and spatial NeRF rendering for autonomous campus delivery robot.",
                "PENDING",
                None,
                time.time() - 7200
            ),
            (
                "prop_kian_02",
                "EE-310 · Sim2Real Edge Rover Navigation",
                "stu_kian_02",
                "Kian Patel",
                "Dr. Aris Thorne (Faculty, AI Lab)",
                "equip_jetson_01",
                5,
                "capstone",
                "Edge reinforcement learning policy deployment on Jetson AGX Orin for off-road rover obstacle traversal.",
                "PENDING",
                None,
                time.time() - 5400
            ),
            (
                "prop_slam_01",
                "Autonomous Campus Drone SLAM Navigation",
                "stu_arjun_01",
                "Arjun Sharma",
                "Dr. K. Ramanathan (Professor, ECE)",
                "equip_rpi_01",
                3,
                "capstone",
                "Deploying lightweight YOLOv8 on Hailo-8L NPU for GPS-denied indoor quadcopter localization.",
                "APPROVED",
                "Approved for capstone testing. Bench CS-C08 assigned.",
                time.time() - 3600
            )
        ]
        cursor.executemany("""
        INSERT OR IGNORE INTO project_proposals (
            id, project_title, student_id, student_name, faculty_advisor,
            target_equipment_id, submission_deadline_days, academic_tier,
            abstract, status, faculty_notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, sample_proposals)

    conn.commit()

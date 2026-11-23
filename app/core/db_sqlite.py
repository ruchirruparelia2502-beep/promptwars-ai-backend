"""
Persistent SQLite Database Engine for LabLink Platform
Provides:
- Date-partitioned 32-bit slot availability: (equipment_id, booking_date) -> bitmask
- 10-Minute BookMyShow Leased Hold auto-expiration and slot release
- Server-side student profiles for anti-spoofing in priority arbitration
- Proposals, Bookings, Equipment, and GenAI Copilot query caching
- Thread-safe SQLite access with WAL mode and Vercel serverless /tmp fallback
"""

import os
import sqlite3
import json
import time
import datetime
import threading
from typing import Dict, List, Optional, Any, Tuple
from app.core.bitmask import (
    TOTAL_SLOTS,
    create_interval_mask,
    is_interval_available,
    apply_reservation,
    cancel_reservation,
    slot_index_to_time
)


def get_db_path() -> str:
    """Determines database path with fallback for Vercel serverless environments."""
    if os.environ.get("VERCEL"):
        return "/tmp/lablink.db"
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "lablink.db")


class SQLiteLabDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_connection()
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

            conn.commit()
            conn.close()

            # Seed equipment and student profiles if empty
            self._seed_initial_data()

    def _seed_initial_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM equipment;")
        if cursor.fetchone()["cnt"] == 0:
            from app.core.database import db as in_memory_db
            items = in_memory_db.get_all_equipment()
            for it in items:
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
                ("stu_arjun_01", "Arjun Sharma", "Electronics & Communication", "capstone", 6.5, 2.5, 1),
                ("stu_priya_02", "Priya Patel", "Computer Science", "capstone", 28.0, 5.0, 1),
                ("stu_rohit_03", "Rohit Verma", "Mechanical & Robotics", "coursework", 3.0, 8.0, 1),
                ("stu_ananya_04", "Ananya Deshmukh", "Biotechnology", "funded_research", 12.0, 1.5, 1),
                ("stu_karan_05", "Karan Malhotra", "Computer Science", "independent", 42.0, 14.0, 0)
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
        conn.close()

    # =========================================================================
    # EQUIPMENT METHODS
    # =========================================================================

    def get_all_equipment(self, booking_date: Optional[str] = None) -> List[Dict[str, Any]]:
        date_str = booking_date or datetime.date.today().isoformat()
        self.sweep_expired_holds(date_str)

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT e.*, COALESCE(d.bitmask, 0) as daily_bitmask
        FROM equipment e
        LEFT JOIN date_slot_availability d
          ON e.id = d.equipment_id AND d.booking_date = ?
        ORDER BY e.hourly_rate ASC;
        """, (date_str,))
        rows = cursor.fetchall()
        conn.close()

        result = []
        for r in rows:
            result.append({
                "id": r["id"],
                "name": r["name"],
                "department": r["department"],
                "category": r["category"],
                "location": r["location"],
                "specifications": json.loads(r["specifications_json"] or "{}"),
                "safety_level": r["safety_level"],
                "tier": r["tier"],
                "hourly_cost_estimate": r["hourly_cost_estimate"],
                "hourly_rate": r["hourly_rate"],
                "daily_bitmask": r["daily_bitmask"],
                "status": r["status"],
                "tags": json.loads(r["tags_json"] or "[]")
            })
        return result

    def get_equipment_by_id(self, equip_id: str, booking_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        date_str = booking_date or datetime.date.today().isoformat()
        self.sweep_expired_holds(date_str)

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT e.*, COALESCE(d.bitmask, 0) as daily_bitmask
        FROM equipment e
        LEFT JOIN date_slot_availability d
          ON e.id = d.equipment_id AND d.booking_date = ?
        WHERE e.id = ?;
        """, (date_str, equip_id))
        r = cursor.fetchone()
        conn.close()
        if not r:
            return None

        return {
            "id": r["id"],
            "name": r["name"],
            "department": r["department"],
            "category": r["category"],
            "location": r["location"],
            "specifications": json.loads(r["specifications_json"] or "{}"),
            "safety_level": r["safety_level"],
            "tier": r["tier"],
            "hourly_cost_estimate": r["hourly_cost_estimate"],
            "hourly_rate": r["hourly_rate"],
            "daily_bitmask": r["daily_bitmask"],
            "status": r["status"],
            "tags": json.loads(r["tags_json"] or "[]")
        }

    def search_by_tag_or_keyword(self, query: str, booking_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fast SQL search across name, category, department, and tags."""
        date_str = booking_date or datetime.date.today().isoformat()
        q_pattern = f"%{query.strip().lower()}%"
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT e.*, COALESCE(d.bitmask, 0) as daily_bitmask
        FROM equipment e
        LEFT JOIN date_slot_availability d
          ON e.id = d.equipment_id AND d.booking_date = ?
        WHERE LOWER(e.name) LIKE ?
           OR LOWER(e.category) LIKE ?
           OR LOWER(e.department) LIKE ?
           OR LOWER(e.tags_json) LIKE ?
        ORDER BY e.hourly_rate ASC;
        """, (date_str, q_pattern, q_pattern, q_pattern, q_pattern))
        rows = cursor.fetchall()
        conn.close()

        result = []
        for r in rows:
            result.append({
                "id": r["id"],
                "name": r["name"],
                "department": r["department"],
                "category": r["category"],
                "location": r["location"],
                "specifications": json.loads(r["specifications_json"] or "{}"),
                "safety_level": r["safety_level"],
                "tier": r["tier"],
                "hourly_cost_estimate": r["hourly_cost_estimate"],
                "hourly_rate": r["hourly_rate"],
                "daily_bitmask": r["daily_bitmask"],
                "status": r["status"],
                "tags": json.loads(r["tags_json"] or "[]")
            })
        return result

    # =========================================================================
    # DATE-PARTITIONED BITMASK & HOLD EXPIRATION METHODS
    # =========================================================================

    def get_availability_mask(self, equipment_id: str, booking_date: str) -> int:
        self.sweep_expired_holds(booking_date)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT bitmask FROM date_slot_availability
        WHERE equipment_id = ? AND booking_date = ?;
        """, (equipment_id, booking_date))
        row = cursor.fetchone()
        conn.close()
        return row["bitmask"] if row else 0

    def reserve_slot_atomic(
        self,
        equipment_id: str,
        slot_index: int,
        duration_slots: int,
        booking_date: Optional[str] = None
    ) -> Tuple[bool, int, str]:
        """
        Atomically allocates interval on (equipment_id, booking_date).
        Returns (success: bool, new_bitmask: int, reason: str).
        """
        date_str = booking_date or datetime.date.today().isoformat()
        req_mask = create_interval_mask(slot_index, duration_slots)

        with self._lock:
            self.sweep_expired_holds(date_str)
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            SELECT bitmask FROM date_slot_availability
            WHERE equipment_id = ? AND booking_date = ?;
            """, (equipment_id, date_str))
            row = cursor.fetchone()
            current_mask = row["bitmask"] if row else 0

            if not is_interval_available(current_mask, req_mask):
                conn.close()
                return False, current_mask, "SLOT_CONFLICT_ALREADY_RESERVED"

            new_mask = apply_reservation(current_mask, req_mask)
            now = time.time()

            cursor.execute("""
            INSERT INTO date_slot_availability (equipment_id, booking_date, bitmask, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(equipment_id, booking_date)
            DO UPDATE SET bitmask = excluded.bitmask, updated_at = excluded.updated_at;
            """, (equipment_id, date_str, new_mask, now))

            conn.commit()
            conn.close()
            return True, new_mask, "SUCCESS"

    def release_slot_atomic(
        self,
        equipment_id: str,
        slot_index: int,
        duration_slots: int,
        booking_date: Optional[str] = None
    ) -> int:
        """Clears slot bits for (equipment_id, booking_date)."""
        date_str = booking_date or datetime.date.today().isoformat()

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            SELECT bitmask FROM date_slot_availability
            WHERE equipment_id = ? AND booking_date = ?;
            """, (equipment_id, date_str))
            row = cursor.fetchone()
            current_mask = row["bitmask"] if row else 0

            new_mask = cancel_reservation(current_mask, req_mask)
            cursor.execute("""
            UPDATE date_slot_availability
            SET bitmask = ?, updated_at = ?
            WHERE equipment_id = ? AND booking_date = ?;
            """, (new_mask, time.time(), equipment_id, date_str))

            conn.commit()
            conn.close()
            return new_mask

    def sweep_expired_holds(self, booking_date: Optional[str] = None) -> int:
        """
        Sweeps and cancels expired BookMyShow 10-minute leased holds.
        Releases the corresponding bitmask bits in date_slot_availability.
        Promotes waiting list candidates if available.
        Returns count of swept leases.
        """
        now = time.time()
        date_str = booking_date or datetime.date.today().isoformat()

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            SELECT id, equipment_id, booking_date, slot_index, duration_slots
            FROM bookings
            WHERE status = 'HOLD_LEASE' AND lease_expires_at < ?;
            """, (now,))
            expired_bookings = cursor.fetchall()

            count = len(expired_bookings)
            for b in expired_bookings:
                # 1. Mark booking expired
                cursor.execute("""
                UPDATE bookings SET status = 'EXPIRED' WHERE id = ?;
                """, (b["id"],))

                # 2. Clear bits in date availability
                cursor.execute("""
                SELECT bitmask FROM date_slot_availability
                WHERE equipment_id = ? AND booking_date = ?;
                """, (b["equipment_id"], b["booking_date"]))
                r = cursor.fetchone()
                if r:
                    b_mask = create_interval_mask(b["slot_index"], b["duration_slots"])
                    new_mask = cancel_reservation(r["bitmask"], b_mask)
                    cursor.execute("""
                    UPDATE date_slot_availability
                    SET bitmask = ?, updated_at = ?
                    WHERE equipment_id = ? AND booking_date = ?;
                    """, (new_mask, now, b["equipment_id"], b["booking_date"]))

                # 3. Auto-promote from IRCTC Waiting List if exists
                cursor.execute("""
                SELECT * FROM waiting_list
                WHERE equipment_id = ? AND booking_date = ? AND slot_index = ?
                ORDER BY priority_score DESC
                LIMIT 1;
                """, (b["equipment_id"], b["booking_date"], b["slot_index"]))
                waiter = cursor.fetchone()
                if waiter:
                    # Promote waiter to hold lease
                    new_lease = now + 600  # 10 minutes
                    new_start, new_end = slot_index_to_time(waiter["slot_index"])
                    cursor.execute("""
                    INSERT INTO bookings (
                        id, equipment_id, student_id, student_name, project_id,
                        project_title, booking_date, slot_index, duration_slots,
                        start_time, end_time, status, lease_expires_at,
                        state_signature, purpose_abstract, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'HOLD_LEASE', ?, 'PROMOTED_FROM_WL', ?, ?);
                    """, (
                        f"prom_{waiter['id']}",
                        waiter["equipment_id"],
                        waiter["student_id"],
                        waiter["student_name"],
                        "proj_promoted",
                        waiter["project_title"],
                        waiter["booking_date"],
                        waiter["slot_index"],
                        waiter["duration_slots"],
                        new_start,
                        new_end,
                        new_lease,
                        "Promoted automatically from IRCTC WL-1 queue upon hold expiration",
                        now
                    ))
                    # Re-apply bitmask for promoted candidate
                    cursor.execute("""
                    SELECT bitmask FROM date_slot_availability
                    WHERE equipment_id = ? AND booking_date = ?;
                    """, (waiter["equipment_id"], waiter["booking_date"]))
                    curr_r = cursor.fetchone()
                    if curr_r:
                        waiter_mask = create_interval_mask(waiter["slot_index"], waiter["duration_slots"])
                        promoted_mask = apply_reservation(curr_r["bitmask"], waiter_mask)
                        cursor.execute("""
                        UPDATE date_slot_availability
                        SET bitmask = ?, updated_at = ?
                        WHERE equipment_id = ? AND booking_date = ?;
                        """, (promoted_mask, now, waiter["equipment_id"], waiter["booking_date"]))

                    # Delete from waiting list
                    cursor.execute("DELETE FROM waiting_list WHERE id = ?;", (waiter["id"],))

            conn.commit()
            conn.close()
            return count

    # =========================================================================
    # BOOKINGS CRUD
    # =========================================================================

    def add_booking(self, booking_dict: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO bookings (
            id, equipment_id, student_id, student_name, project_id, project_title,
            booking_date, slot_index, duration_slots, start_time, end_time, status,
            lease_expires_at, state_signature, purpose_abstract, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            booking_dict["id"],
            booking_dict["equipment_id"],
            booking_dict["student_id"],
            booking_dict["student_name"],
            booking_dict.get("project_id"),
            booking_dict.get("project_title"),
            booking_dict.get("booking_date", datetime.date.today().isoformat()),
            booking_dict["slot_index"],
            booking_dict["duration_slots"],
            booking_dict["start_time"],
            booking_dict["end_time"],
            booking_dict.get("status", "HOLD_LEASE"),
            booking_dict.get("lease_expires_at", time.time() + 600),
            booking_dict.get("state_signature", ""),
            booking_dict.get("purpose_abstract", ""),
            booking_dict.get("created_at", time.time())
        ))
        conn.commit()
        conn.close()

    def get_booking_by_id(self, booking_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE id = ?;", (booking_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_bookings(self, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self.sweep_expired_holds()
        conn = self._get_connection()
        cursor = conn.cursor()
        if student_id:
            cursor.execute("SELECT * FROM bookings WHERE student_id = ? ORDER BY created_at DESC;", (student_id,))
        else:
            cursor.execute("SELECT * FROM bookings ORDER BY created_at DESC;")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_proposal_by_id(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM project_proposals WHERE id = ?;", (proposal_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def confirm_booking(self, booking_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE bookings SET status = 'CONFIRMED'
            WHERE id = ? AND status = 'HOLD_LEASE';
            """, (booking_id,))
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return updated

    # =========================================================================
    # PROPOSALS CRUD (FACULTY WORKFLOW)
    # =========================================================================

    def add_proposal(self, proposal_dict: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO project_proposals (
            id, project_title, student_id, student_name, faculty_advisor,
            target_equipment_id, submission_deadline_days, academic_tier,
            abstract, status, faculty_notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            proposal_dict["id"],
            proposal_dict["project_title"],
            proposal_dict["student_id"],
            proposal_dict["student_name"],
            proposal_dict["faculty_advisor"],
            proposal_dict["target_equipment_id"],
            proposal_dict["submission_deadline_days"],
            proposal_dict["academic_tier"],
            proposal_dict.get("abstract", ""),
            proposal_dict.get("status", "PENDING"),
            proposal_dict.get("faculty_notes"),
            proposal_dict.get("created_at", time.time())
        ))
        conn.commit()
        conn.close()

    def get_all_proposals(self, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if student_id:
            cursor.execute("SELECT * FROM project_proposals WHERE student_id = ? ORDER BY created_at DESC;", (student_id,))
        else:
            cursor.execute("SELECT * FROM project_proposals ORDER BY created_at DESC;")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_proposal_by_id(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM project_proposals WHERE id = ?;", (proposal_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_proposal_status(self, proposal_id: str, new_status: str, notes: Optional[str] = None) -> bool:
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE project_proposals
            SET status = ?, faculty_notes = ?
            WHERE id = ?;
            """, (new_status, notes, proposal_id))
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return updated

    # =========================================================================
    # STUDENT PROFILES (ANTI-SPOOFING SERVER STATE)
    # =========================================================================

    def get_student_profile(self, student_id: str) -> Dict[str, Any]:
        """Returns verified student records so client cannot spoof hours or deadlines."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student_profiles WHERE student_id = ?;", (student_id,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

        # Baseline auto-enrollment for new student IDs
        default_profile = {
            "student_id": student_id,
            "student_name": student_id.replace("stu_", "").replace("_", " ").title(),
            "department": "Engineering",
            "academic_tier": "capstone",
            "historical_hours_used": 4.0,
            "current_deadline_days": 3.0,
            "has_safety_cert": 1
        }
        cursor.execute("""
        INSERT INTO student_profiles (
            student_id, student_name, department, academic_tier,
            historical_hours_used, current_deadline_days, has_safety_cert
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            default_profile["student_id"],
            default_profile["student_name"],
            default_profile["department"],
            default_profile["academic_tier"],
            default_profile["historical_hours_used"],
            default_profile["current_deadline_days"],
            default_profile["has_safety_cert"]
        ))
        conn.commit()
        conn.close()
        return default_profile

    # =========================================================================
    # COPILOT CACHING
    # =========================================================================

    def get_copilot_cache(self, query_hash: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT response_json FROM copilot_cache WHERE query_hash = ?;", (query_hash,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row["response_json"])
        return None

    def set_copilot_cache(self, query_hash: str, prompt_text: str, response_data: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO copilot_cache (query_hash, prompt_text, response_json, created_at)
        VALUES (?, ?, ?, ?);
        """, (query_hash, prompt_text, json.dumps(response_data), time.time()))
        conn.commit()
        conn.close()


# Global Singleton Database Instance
db = SQLiteLabDatabase()

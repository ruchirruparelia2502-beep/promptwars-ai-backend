"""
Persistent SQLite Database Engine for LabLink Platform
Modular Facade delegating to specialized repositories in app.core.db:
- connection: Safe path resolution, WAL mode, table DDL, seeding
- equipment_repo: Inventory discovery, filtering, semantic search
- booking_repo: Date-partitioned 32-bit slot reservations, 10-min hold release
- proposal_repo: Project proposals, faculty review
- student_repo: Verified student profiles (anti-spoofing)
- cache_repo: Copilot response cache with TTL, persistent sliding-window rate limit
"""

import threading
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from app.core.db.connection import get_db_path, create_connection, init_schema, seed_initial_data
from app.core.db import (
    equipment_repo,
    booking_repo,
    proposal_repo,
    student_repo,
    cache_repo
)


class SQLiteLabDatabase:
    """Thread-safe SQLite Database Facade for LabLink platform."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = create_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipment'")
            if not cursor.fetchone():
                with self._lock:
                    init_schema(conn)
                    seed_initial_data(conn)
        except Exception:
            pass
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_connection()
            init_schema(conn)
            seed_initial_data(conn)
            conn.close()

    def _seed_initial_data(self):
        with self._lock:
            conn = self._get_connection()
            seed_initial_data(conn)
            conn.close()

    # --- Equipment Inventory ---
    def get_all_equipment(
        self,
        department: Optional[str] = None,
        category: Optional[str] = None,
        booking_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            return equipment_repo.get_all_equipment(conn, department, category, booking_date)
        finally:
            conn.close()

    def get_equipment_by_id(
        self,
        equipment_id: str,
        booking_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            return equipment_repo.get_equipment_by_id(conn, equipment_id, booking_date)
        finally:
            conn.close()

    def search_equipment_semantic(
        self,
        query: str,
        department: Optional[str] = None,
        booking_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            return equipment_repo.search_equipment_semantic(conn, query, department, booking_date)
        finally:
            conn.close()

    def search_by_tag_or_keyword(self, query: str, booking_date: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.search_equipment_semantic(query, booking_date=booking_date)

    # --- Bookings & Bitmask Slots ---
    def get_availability_mask(self, equipment_id: str, booking_date: str) -> int:
        conn = self._get_connection()
        try:
            return booking_repo.get_availability_mask(conn, equipment_id, booking_date)
        finally:
            conn.close()

    def reserve_slot_atomic(
        self,
        equipment_id: str,
        slot_index: int,
        duration_slots: int,
        booking_date: Optional[str] = None
    ) -> Tuple[bool, int, str]:
        with self._lock:
            conn = self._get_connection()
            try:
                return booking_repo.reserve_slot_atomic(conn, equipment_id, slot_index, duration_slots, booking_date)
            finally:
                conn.close()

    def release_slot_atomic(
        self,
        equipment_id: str,
        slot_index: int,
        duration_slots: int,
        booking_date: Optional[str] = None
    ) -> int:
        with self._lock:
            conn = self._get_connection()
            try:
                return booking_repo.release_slot_atomic(conn, equipment_id, slot_index, duration_slots, booking_date)
            finally:
                conn.close()

    def sweep_expired_holds(self, booking_date: Optional[str] = None) -> int:
        with self._lock:
            conn = self._get_connection()
            try:
                return booking_repo.sweep_expired_holds(conn, booking_date)
            finally:
                conn.close()

    def check_and_expire_holds(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                return booking_repo.check_and_expire_holds(conn)
            finally:
                conn.close()

    def add_booking(self, booking_dict: Dict[str, Any]):
        with self._lock:
            conn = self._get_connection()
            try:
                booking_repo.add_booking(conn, booking_dict)
            finally:
                conn.close()

    def get_booking_by_id(self, booking_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            return booking_repo.get_booking_by_id(conn, booking_id)
        finally:
            conn.close()

    def get_all_bookings(
        self,
        student_id: Optional[str] = None,
        equipment_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            return booking_repo.get_all_bookings(conn, student_id, equipment_id)
        finally:
            conn.close()

    def update_booking_status(self, booking_id: str, new_status: str):
        with self._lock:
            conn = self._get_connection()
            try:
                booking_repo.update_booking_status(conn, booking_id, new_status)
            finally:
                conn.close()

    def confirm_booking(self, booking_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                return booking_repo.confirm_booking(conn, booking_id)
            finally:
                conn.close()

    # --- Project Proposals & Approvals ---
    def add_proposal(self, proposal_dict: Dict[str, Any]):
        with self._lock:
            conn = self._get_connection()
            try:
                proposal_repo.add_proposal(conn, proposal_dict)
            finally:
                conn.close()

    def get_all_proposals(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            return proposal_repo.get_all_proposals(conn)
        finally:
            conn.close()

    def get_proposal_by_id(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            return proposal_repo.get_proposal_by_id(conn, proposal_id)
        finally:
            conn.close()

    def update_proposal_status(self, proposal_id: str, new_status: str, notes: Optional[str] = None):
        with self._lock:
            conn = self._get_connection()
            try:
                proposal_repo.update_proposal_status(conn, proposal_id, new_status, notes)
            finally:
                conn.close()

    # --- Student Profiles (Anti-Spoofing) ---
    def get_student_profile(self, student_id: str) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            return student_repo.get_student_profile(conn, student_id)
        finally:
            conn.close()

    def update_student_profile(self, student_id: str, **kwargs):
        with self._lock:
            conn = self._get_connection()
            try:
                student_repo.update_student_profile(conn, student_id, **kwargs)
            finally:
                conn.close()

    # --- Copilot Cache & Persistent Rate Limiting ---
    def get_copilot_cache(self, query_hash: str, max_age_seconds: int = 86400) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            return cache_repo.get_copilot_cache(conn, query_hash, max_age_seconds)
        finally:
            conn.close()

    def set_copilot_cache(self, query_hash: str, prompt_text: str, response_data: Dict[str, Any]):
        with self._lock:
            conn = self._get_connection()
            try:
                cache_repo.set_copilot_cache(conn, query_hash, prompt_text, response_data)
            finally:
                conn.close()

    def check_rate_limit(self, client_key: str, max_requests: int = 60, window_seconds: int = 60) -> Tuple[bool, int]:
        with self._lock:
            conn = self._get_connection()
            try:
                return cache_repo.check_rate_limit(conn, client_key, max_requests, window_seconds)
            finally:
                conn.close()


# Global Singleton Database Instance
db = SQLiteLabDatabase()

"""
Booking & Bitmask Reservation repository queries for LabLink platform.
Implements:
- Date-partitioned 32-bit slot reservations (date_slot_availability)
- BookMyShow 10-Minute Hold expiration and atomic slot release
- IRCTC Waiting List (WL-1) auto-promotion
- Booking records lifecycle
"""

import time
import datetime
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from app.core.bitmask import (
    TOTAL_SLOTS,
    create_interval_mask,
    is_interval_available,
    apply_reservation,
    cancel_reservation,
    slot_index_to_time
)


def get_availability_mask(conn: sqlite3.Connection, equipment_id: str, booking_date: str) -> int:
    cursor = conn.cursor()
    cursor.execute("""
    SELECT bitmask FROM date_slot_availability
    WHERE equipment_id = ? AND booking_date = ?;
    """, (equipment_id, booking_date))
    row = cursor.fetchone()
    if row:
        return int(row["bitmask"])
    return 0


def reserve_slot_atomic(
    conn: sqlite3.Connection,
    equipment_id: str,
    slot_index: int,
    duration_slots: int,
    booking_date: Optional[str] = None
) -> Tuple[bool, int, str]:
    target_date = booking_date or datetime.date.today().isoformat()
    cursor = conn.cursor()

    current_mask = get_availability_mask(conn, equipment_id, target_date)
    request_mask = create_interval_mask(slot_index, duration_slots)

    if not is_interval_available(current_mask, request_mask):
        return False, current_mask, "SLOT_CONFLICT_ALREADY_RESERVED"

    new_mask = apply_reservation(current_mask, request_mask)
    now = time.time()

    cursor.execute("""
    INSERT INTO date_slot_availability (equipment_id, booking_date, bitmask, updated_at)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(equipment_id, booking_date)
    DO UPDATE SET bitmask = excluded.bitmask, updated_at = excluded.updated_at;
    """, (equipment_id, target_date, new_mask, now))
    conn.commit()

    return True, new_mask, "SUCCESS"


def release_slot_atomic(
    conn: sqlite3.Connection,
    equipment_id: str,
    slot_index: int,
    duration_slots: int,
    booking_date: Optional[str] = None
) -> int:
    target_date = booking_date or datetime.date.today().isoformat()
    cursor = conn.cursor()

    current_mask = get_availability_mask(conn, equipment_id, target_date)
    request_mask = create_interval_mask(slot_index, duration_slots)
    new_mask = cancel_reservation(current_mask, request_mask)

    cursor.execute("""
    UPDATE date_slot_availability
    SET bitmask = ?, updated_at = ?
    WHERE equipment_id = ? AND booking_date = ?;
    """, (new_mask, time.time(), equipment_id, target_date))
    conn.commit()

    return new_mask


def sweep_expired_holds(conn: sqlite3.Connection, booking_date: Optional[str] = None) -> int:
    """
    Sweeps expired BookMyShow 10-minute leased holds and releases bitmask bits.
    Auto-promotes IRCTC Waiting List candidates if queued.
    """
    now = time.time()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, equipment_id, booking_date, slot_index, duration_slots
    FROM bookings
    WHERE status = 'HOLD_LEASE' AND lease_expires_at IS NOT NULL AND lease_expires_at < ?;
    """, (now,))
    expired = cursor.fetchall()
    count = len(expired)

    for b in expired:
        cursor.execute("UPDATE bookings SET status = 'EXPIRED' WHERE id = ?;", (b["id"],))

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

        # Promote from waiting list
        cursor.execute("""
        SELECT * FROM waiting_list
        WHERE equipment_id = ? AND booking_date = ? AND slot_index = ?
        ORDER BY priority_score DESC LIMIT 1;
        """, (b["equipment_id"], b["booking_date"], b["slot_index"]))
        waiter = cursor.fetchone()
        if waiter:
            new_lease = now + 600
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
            cursor.execute("DELETE FROM waiting_list WHERE id = ?;", (waiter["id"],))

    conn.commit()
    return count


def add_booking(conn: sqlite3.Connection, booking_dict: Dict[str, Any]):
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


def get_booking_by_id(conn: sqlite3.Connection, booking_id: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id = ?;", (booking_id,))
    row = cursor.fetchone()
    if row:
        item = dict(row)
        item["booking_id"] = item["id"]
        return item
    return None


def get_all_bookings(
    conn: sqlite3.Connection,
    student_id: Optional[str] = None,
    equipment_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    sweep_expired_holds(conn)
    cursor = conn.cursor()
    query = "SELECT * FROM bookings WHERE 1=1"
    params = []
    if student_id:
        query += " AND student_id = ?"
        params.append(student_id)
    if equipment_id:
        query += " AND equipment_id = ?"
        params.append(equipment_id)
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        b = dict(r)
        b["booking_id"] = b["id"]
        results.append(b)
    return results


def update_booking_status(conn: sqlite3.Connection, booking_id: str, new_status: str):
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?;", (new_status, booking_id))
    conn.commit()


def confirm_booking(conn: sqlite3.Connection, booking_id: str) -> bool:
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE bookings SET status = 'CONFIRMED'
    WHERE id = ? AND status = 'HOLD_LEASE';
    """, (booking_id,))
    updated = cursor.rowcount > 0
    conn.commit()
    return updated


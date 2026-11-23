"""
Slot Booking Router for LabLink
Implements O(1) bitmask atomic reservations and BookMyShow-style leased holds.
"""

import time
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.core.database import db
from app.core.bitmask import (
    TOTAL_SLOTS,
    create_interval_mask,
    slot_index_to_time,
    is_interval_available,
    find_next_available_window,
    calculate_utilization_percentage
)
from app.core.security import generate_state_signature
from app.schemas.lablink import BookingCreateRequest, BookingResponse

router = APIRouter(prefix="/api/v1/bookings", tags=["Slot Booking"])


@router.get("/slots/{equipment_id}")
def get_equipment_slots(equipment_id: str):
    """
    Returns the real-time 24 half-hour slot availability matrix for an equipment.
    Computes utilization in O(1).
    """
    equip = db.get_equipment_by_id(equipment_id)
    if not equip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment '{equipment_id}' not found."
        )

    current_mask = equip["daily_bitmask"]
    slots_info = []

    for i in range(TOTAL_SLOTS):
        start_str, end_str = slot_index_to_time(i)
        is_occupied = bool((current_mask >> i) & 1)
        slots_info.append({
            "slot_index": i,
            "start_time": start_str,
            "end_time": end_str,
            "is_available": not is_occupied,
            "status": "OCCUPIED" if is_occupied else "AVAILABLE"
        })

    return {
        "equipment_id": equipment_id,
        "equipment_name": equip["name"],
        "daily_bitmask": current_mask,
        "utilization_percent": calculate_utilization_percentage(current_mask),
        "slots": slots_info
    }


@router.post("", response_model=BookingResponse)
def create_slot_booking(request: BookingCreateRequest):
    """
    Creates an atomic slot reservation using O(1) bitwise operations.
    Implements BookMyShow 10-Minute Leased Hold pattern:
    Slot is locked in 'HOLD_LEASE' status for 10 minutes to allow project submission/faculty signoff.
    """
    equip = db.get_equipment_by_id(request.equipment_id)
    if not equip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment '{request.equipment_id}' not found."
        )

    # 1. Create bitmask for the requested interval in O(1)
    req_mask = create_interval_mask(request.slot_index, request.duration_slots)
    if req_mask == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slot index or duration requested."
        )

    # 2. Check availability in O(1) and reserve atomically
    current_mask = equip["daily_bitmask"]
    if not is_interval_available(current_mask, req_mask):
        # Find next available window as a Vikalp recommendation
        next_slot = find_next_available_window(current_mask, request.duration_slots, start_from=request.slot_index + 1)
        alt_msg = ""
        if next_slot is not None:
            n_start, n_end = slot_index_to_time(next_slot)
            alt_msg = f" Suggested alternative slot today: {n_start} - {n_end}."
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slot contention detected! The requested interval is already booked.{alt_msg} Please use the Smart Conflict Resolver."
        )

    # Perform atomic reservation under mutex lock
    reserved = db.reserve_slot_atomic(request.equipment_id, req_mask)
    if not reserved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Concurrent booking collision detected. Please retry or use Smart Contention Resolver."
        )

    # Generate BookMyShow 10-minute hold lease
    booking_id = f"book_{uuid.uuid4().hex[:8]}"
    start_time, _ = slot_index_to_time(request.slot_index)
    _, end_time = slot_index_to_time(min(TOTAL_SLOTS - 1, request.slot_index + request.duration_slots - 1))
    lease_expires = time.time() + 600.0  # 10 minutes

    # HMAC integrity signature
    sig_payload = f"{booking_id}:{request.equipment_id}:{request.student_id}:{request.slot_index}"
    signature = generate_state_signature(sig_payload)

    booking_record = {
        "booking_id": booking_id,
        "equipment_id": request.equipment_id,
        "equipment_name": equip["name"],
        "student_id": request.student_id,
        "student_name": request.student_name,
        "project_id": request.project_id,
        "project_title": request.project_title,
        "slot_index": request.slot_index,
        "duration_slots": request.duration_slots,
        "start_time": start_time,
        "end_time": end_time,
        "status": "HOLD_LEASE",
        "lease_expires_at": lease_expires,
        "state_signature": signature,
        "created_at": time.time()
    }
    db.add_booking(booking_record)

    return BookingResponse(
        booking_id=booking_id,
        equipment_id=request.equipment_id,
        equipment_name=equip["name"],
        student_id=request.student_id,
        student_name=request.student_name,
        slot_index=request.slot_index,
        duration_slots=request.duration_slots,
        start_time=start_time,
        end_time=end_time,
        status="HOLD_LEASE",
        lease_expires_at=lease_expires,
        state_signature=signature,
        message="Slot secured under 10-Minute BookMyShow Leased Hold. Awaiting faculty proposal confirmation."
    )


@router.get("", response_model=List[Dict[str, Any]])
def list_active_bookings():
    """Returns all current bookings and leased holds across campus."""
    return db.get_all_bookings()

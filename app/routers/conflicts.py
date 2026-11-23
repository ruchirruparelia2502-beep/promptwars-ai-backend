"""
Intelligent Conflict Resolution Router for LabLink
Inspired by IRCTC Tatkal Fairness Quota and BookMyShow Leased Holds.
Resolves overlapping student equipment requests non-randomly using Multi-Factor Priority Scoring (MFPS):
- Verified Deadline Urgency from Server Profile (anti-spoofing)
- Academic Tier (Capstone vs Homework)
- Anti-Hoarding Fairness Factor (penalizes monopolized lab hours)
- Safety & Skill Certifications

Fixes Verified Hackathon Weaknesses:
1. Verifies if requested slot is already booked in the bitmask on that date before awarding.
2. Commits winning resolution into the persistent SQLite database as a real booking.
3. Automatically queues runner-ups in the IRCTC Waiting List (WL-1).
"""

import time
import uuid
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from app.core.database import db
from app.algorithms.smart_allocator import (
    ContenderProfile,
    resolve_slot_contention
)
from app.core.bitmask import (
    slot_index_to_time,
    TOTAL_SLOTS,
    create_interval_mask,
    is_interval_available,
    find_next_available_window
)
from app.core.security import generate_state_signature
from app.schemas.lablink import ContentionResolveRequest, ContentionResolveResponse

router = APIRouter(prefix="/api/v1/conflicts", tags=["Smart Conflict Resolution"])


@router.post("/resolve", response_model=ContentionResolveResponse)
def resolve_contention_endpoint(
    request: ContentionResolveRequest,
    booking_date: Optional[str] = Query(None, description="Target date YYYY-MM-DD")
):
    """
    Arbitrates simultaneous/competing slot requests.
    Prevents race conditions using Multi-Factor Priority Scoring (MFPS).
    Validates against existing booked bitmasks, saves the winning reservation,
    and dispatches IRCTC Vikalp rerouting for runner-ups.
    """
    date_str = request.booking_date or booking_date or datetime.date.today().isoformat()
    equip = db.get_equipment_by_id(request.equipment_id, booking_date=date_str)
    if not equip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment '{request.equipment_id}' not found."
        )

    # 1. Anti-Spoofing: Hydrate contender profiles with server-verified historical hours & deadlines
    contender_profiles = []
    for c in request.contenders:
        verified_prof = db.get_student_profile(c.student_id)
        # Use server-verified data to prevent client tampering
        deadline_h = float(verified_prof.get("current_deadline_days", 3.0)) * 24.0
        used_h = float(verified_prof.get("historical_hours_used", 4.0))
        safety = bool(verified_prof.get("has_safety_cert", 1))

        contender_profiles.append(ContenderProfile(
            student_id=c.student_id,
            student_name=c.student_name or verified_prof.get("student_name", "Student"),
            project_id=c.project_id,
            project_title=c.project_title,
            academic_tier=verified_prof.get("academic_tier", c.academic_tier),
            deadline_hours=deadline_h,
            hours_used_this_month=used_h,
            has_safety_cert=safety,
            requested_slot=c.requested_slot,
            duration_slots=c.duration_slots
        ))

    # 2. Check if the target slot is ALREADY occupied in the bitmask on this date
    current_mask = db.get_availability_mask(request.equipment_id, date_str)
    first_req = contender_profiles[0]
    target_mask = create_interval_mask(first_req.requested_slot, first_req.duration_slots)
    is_already_booked = not is_interval_available(current_mask, target_mask)

    if is_already_booked:
        req_start, req_end = slot_index_to_time(first_req.requested_slot)
        next_free = find_next_available_window(current_mask, first_req.duration_slots, start_from=first_req.requested_slot + 1)
        if next_free is None:
            next_free = find_next_available_window(current_mask, first_req.duration_slots, start_from=0)
        next_hint = f" Nearest available alternative window is slot {next_free} ({slot_index_to_time(next_free)[0]})." if next_free is not None else ""
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Contention Resolution Rejected: Target slot {first_req.requested_slot} ({req_start} - {req_end}) "
                f"is ALREADY confirmed by an existing booking on {date_str}.{next_hint}"
            )
        )

    # Find department alternatives for Vikalp recommendations
    all_equip = db.get_all_equipment(booking_date=date_str)
    alternatives = [
        e for e in all_equip
        if e["id"] != request.equipment_id and (
            e["category"] == equip["category"] or e["department"] == equip["department"]
        )
    ]

    # Execute deterministic O(K log K) smart arbitration
    result = resolve_slot_contention(
        equipment_id=request.equipment_id,
        equipment_name=equip["name"],
        contenders=contender_profiles,
        current_equipment_mask=current_mask,
        alternative_equipment=alternatives
    )

    allocated_slot = result.allocated_slot

    # 3. Commit Winning Allocation to SQLite Database
    success, new_mask, reason = db.reserve_slot_atomic(
        request.equipment_id,
        allocated_slot,
        result.duration_slots,
        booking_date=date_str
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slot reservation failed during arbitration commit: {reason}."
        )

    booking_id = f"book_arb_{uuid.uuid4().hex[:8]}"
    start_str, _ = slot_index_to_time(allocated_slot)
    _, end_str = slot_index_to_time(min(TOTAL_SLOTS - 1, allocated_slot + result.duration_slots - 1))
    lease_expires = time.time() + 600.0

    sig_payload = f"{booking_id}:{request.equipment_id}:{allocated_slot}:{int(lease_expires)}"
    signature = generate_state_signature(sig_payload)

    db.add_booking({
        "id": booking_id,
        "booking_id": booking_id,
        "equipment_id": request.equipment_id,
        "equipment_name": equip["name"],
        "student_id": result.winner_student_id,
        "student_name": result.winner_name,
        "project_id": first_req.project_id,
        "project_title": first_req.project_title,
        "booking_date": date_str,
        "slot_index": allocated_slot,
        "duration_slots": result.duration_slots,
        "start_time": start_str,
        "end_time": end_str,
        "status": "HOLD_LEASE",
        "lease_expires_at": lease_expires,
        "state_signature": signature,
        "purpose_abstract": f"Fair Arbitrated Reservation (MFPS score: {result.priority_score:.3f})",
        "created_at": time.time()
    })

    # Call Gemini for authentic arbitration summary if configured
    from app.services.genai_engine import generate_arbitration_explanation_ai
    gemini_summary = generate_arbitration_explanation_ai(
        winner_name=result.winner_name,
        score=result.priority_score,
        contenders_count=len(request.contenders),
        equip_name=equip["name"],
        time_str=f"{start_str} - {end_str}"
    )

    ai_summary = gemini_summary or (
        f"Smart Priority Arbitration Completed on {date_str}: Evaluated {len(request.contenders)} competing requests "
        f"using verified server profiles. Winner {result.winner_name} secured {start_str} - {end_str} "
        f"(MFPS score: {result.priority_score:.3f}) based on deadline urgency ({result.score_breakdown['deadline_urgency']:.2f}) "
        f"and anti-hoarding equity ({result.score_breakdown['fairness_quotient']:.2f}). "
        f"Runner-ups placed in IRCTC WL-1 with Vikalp recommendations."
    )

    return ContentionResolveResponse(
        winner_student_id=result.winner_student_id,
        winner_name=result.winner_name,
        allocated_slot=allocated_slot,
        start_time=start_str,
        end_time=end_str,
        lease_expires_at=lease_expires,
        priority_score=result.priority_score,
        score_breakdown=result.score_breakdown,
        rationale=result.rationale,
        ai_arbitration_summary=ai_summary,
        runner_ups=result.runner_ups,
        vikalp_alternatives=result.vikalp_alternatives
    )

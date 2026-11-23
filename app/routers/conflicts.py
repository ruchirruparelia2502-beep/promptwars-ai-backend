"""
Intelligent Conflict Resolution Router for LabLink
Inspired by IRCTC Tatkal Fairness Quota and BookMyShow Leased Holds.
Resolves overlapping student equipment requests non-randomly based on:
- Deadline Urgency (log-decay)
- Academic Tier (Capstone vs Homework)
- Anti-Hoarding Fairness Factor (penalizes monopolized lab hours)
- Safety & Skill Certifications
Plus IRCTC 'Vikalp' alternative slot and workstation recommendations.
"""

from fastapi import APIRouter, HTTPException, status
from app.core.database import db
from app.algorithms.smart_allocator import (
    ContenderProfile,
    resolve_slot_contention
)
from app.core.bitmask import slot_index_to_time, TOTAL_SLOTS
from app.schemas.lablink import ContentionResolveRequest, ContentionResolveResponse

router = APIRouter(prefix="/api/v1/conflicts", tags=["Smart Conflict Resolution"])


@router.post("/resolve", response_model=ContentionResolveResponse)
def resolve_contention_endpoint(request: ContentionResolveRequest):
    """
    Simulates or resolves simultaneous booking contention.
    Instead of coin flips or race conditions, applies the Multi-Factor Priority Score (MFPS).
    Allocates an atomic 10-minute hold lease to the highest-scoring student,
    and returns transparent explanations and IRCTC Vikalp alternatives for runner-ups.
    """
    equip = db.get_equipment_by_id(request.equipment_id)
    if not equip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment '{request.equipment_id}' not found."
        )

    # Convert inputs to algorithm dataclass
    contender_profiles = [
        ContenderProfile(
            student_id=c.student_id,
            student_name=c.student_name,
            project_id=c.project_id,
            project_title=c.project_title,
            academic_tier=c.academic_tier,
            deadline_hours=c.deadline_hours,
            hours_used_this_month=c.hours_used_this_month,
            has_safety_cert=c.has_safety_cert,
            requested_slot=c.requested_slot,
            duration_slots=c.duration_slots
        )
        for c in request.contenders
    ]

    # Find department alternative equipment for Vikalp recommendations
    all_equip = db.get_all_equipment()
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
        current_equipment_mask=equip["daily_bitmask"],
        alternative_equipment=alternatives
    )

    start_str, _ = slot_index_to_time(result.allocated_slot)
    _, end_str = slot_index_to_time(min(TOTAL_SLOTS - 1, result.allocated_slot + result.duration_slots - 1))

    # GenAI arbitration summary
    ai_summary = (
        f"Smart Fair-Allocation Completed: Evaluated {len(request.contenders)} simultaneous requests. "
        f"{result.winner_name} awarded primary slot ({start_str} - {end_str}) due to critical deadline "
        f"proximity and anti-hoarding fairness equity. Vikalp alternatives dispatched for remaining students."
    )

    return ContentionResolveResponse(
        winner_student_id=result.winner_student_id,
        winner_name=result.winner_name,
        allocated_slot=result.allocated_slot,
        start_time=start_str,
        end_time=end_str,
        lease_expires_at=result.lease_expires_at,
        priority_score=result.priority_score,
        score_breakdown=result.score_breakdown,
        rationale=result.rationale,
        ai_arbitration_summary=ai_summary,
        runner_ups=result.runner_ups,
        vikalp_alternatives=result.vikalp_alternatives
    )

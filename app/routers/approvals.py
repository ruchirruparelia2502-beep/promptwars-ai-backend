"""
Faculty Approvals & Project Access Workflow for LabLink
Integrates GenAI Proposal Feasibility & Risk Analysis.
"""

import time
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.core.database import db
from app.core.security import generate_state_signature
from app.schemas.lablink import (
    ProjectAccessProposal,
    FacultyDecisionRequest,
    FacultyDecisionResponse
)
from app.services.gemini_assistant import evaluate_faculty_proposal_ai

router = APIRouter(prefix="/api/v1/approvals", tags=["Faculty Approvals"])


@router.post("/proposals", response_model=Dict[str, Any])
def submit_project_proposal(proposal: ProjectAccessProposal):
    """
    Submits a project-based lab access request for faculty sponsorship.
    Triggers automated GenAI feasibility and safety assessment.
    """
    equip = db.get_equipment_by_id(proposal.target_equipment_id)
    if not equip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target equipment '{proposal.target_equipment_id}' does not exist."
        )

    # Automated GenAI evaluation for the professor
    ai_assessment = evaluate_faculty_proposal_ai(proposal.model_dump())

    record = {
        "proposal_id": proposal.project_id or f"prop_{uuid.uuid4().hex[:8]}",
        "project_title": proposal.project_title,
        "student_id": proposal.student_id,
        "student_name": proposal.student_name,
        "faculty_advisor": proposal.faculty_advisor,
        "target_equipment_id": proposal.target_equipment_id,
        "equipment_name": equip["name"],
        "submission_deadline_days": proposal.submission_deadline_days,
        "academic_tier": proposal.academic_tier,
        "abstract": proposal.abstract,
        "status": "PENDING_FACULTY",
        "submission_time": time.time(),
        "ai_assessment": ai_assessment
    }
    db.add_proposal(record)
    return {"message": "Project access proposal submitted for faculty review.", "proposal": record}


@router.get("/pending", response_model=List[Dict[str, Any]])
def list_pending_proposals():
    """Returns all project access proposals requiring faculty action."""
    all_props = db.get_all_proposals()
    return all_props


@router.post("/decision", response_model=FacultyDecisionResponse)
def record_faculty_decision(decision: FacultyDecisionRequest):
    """
    Records a faculty member's decision (APPROVE, REJECT, REQUEST_REVISION).
    Generates HMAC cryptographic verification signature.
    """
    props = {p["proposal_id"]: p for p in db.get_all_proposals()}
    prop = props.get(decision.proposal_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal '{decision.proposal_id}' not found."
        )

    valid_actions = {"APPROVE", "REJECT", "REQUEST_REVISION"}
    action_upper = decision.action.upper().strip()
    if action_upper not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{decision.action}'. Must be one of {valid_actions}."
        )

    new_status = f"{action_upper}D" if action_upper != "REQUEST_REVISION" else "REVISION_REQUESTED"
    db.update_proposal_status(decision.proposal_id, new_status, decision.faculty_notes)

    now = time.time()
    sig_payload = f"{decision.proposal_id}:{new_status}:{now}"
    sig = generate_state_signature(sig_payload)

    return FacultyDecisionResponse(
        proposal_id=decision.proposal_id,
        status=new_status,
        faculty_advisor=prop.get("faculty_advisor", "Faculty Member"),
        decision_timestamp=now,
        state_signature=sig,
        ai_risk_assessment=prop.get("ai_assessment", {}).get("recommendation", "Verified")
    )

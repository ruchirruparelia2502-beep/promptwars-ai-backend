"""
Pydantic Schemas for LabLink Platform
Enforces strict input validation, length bounds, and type safety.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.security import sanitize_ai_prompt


# -------------------------------------------------------------
# Equipment Schemas
# -------------------------------------------------------------
class EquipmentBase(BaseModel):
    id: str = Field(..., max_length=64, description="Unique equipment identifier")
    name: str = Field(..., max_length=128, description="Equipment / workstation name")
    department: str = Field(..., max_length=64, description="Hosting academic department")
    category: str = Field(..., max_length=64, description="Hardware category")
    location: str = Field(..., max_length=128, description="Laboratory room and bench")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Hardware specs")
    safety_level: str = Field(default="Standard", max_length=64)
    tier: Optional[str] = Field(default="MID_RANGE", max_length=32)
    hourly_cost_estimate: Optional[str] = Field(default="$2.00/hr", max_length=32)
    hourly_rate: float = Field(default=2.00, description="Numeric cost per hour for calculations")
    daily_bitmask: int = Field(default=0, description="32-bit integer representing 24 daily slots")
    status: str = Field(default="OPERATIONAL", max_length=32)
    tags: List[str] = Field(default_factory=list)


class EquipmentSearchRequest(BaseModel):
    query: str = Field(..., max_length=200, description="Search query or project need")
    department: Optional[str] = Field(default=None, max_length=64)
    category: Optional[str] = Field(default=None, max_length=64)

    @field_validator("query")
    @classmethod
    def clean_query(cls, v: str) -> str:
        return sanitize_ai_prompt(v, max_chars=200)


class EquipmentSearchResponse(BaseModel):
    total: int
    items: List[EquipmentBase]
    semantic_insights: Optional[str] = None


# -------------------------------------------------------------
# Booking & Slot Schemas
# -------------------------------------------------------------
class BookingCreateRequest(BaseModel):
    equipment_id: str = Field(..., max_length=64)
    student_id: str = Field(..., max_length=64)
    student_name: str = Field(..., max_length=128)
    project_id: str = Field(..., max_length=64)
    project_title: str = Field(..., max_length=200)
    booking_date: Optional[str] = Field(default=None, description="Target date YYYY-MM-DD")
    slot_index: int = Field(..., ge=0, le=23, description="Starting slot (0..23)")
    duration_slots: int = Field(default=2, ge=1, le=8, description="Number of 30-min slots (1..8)")
    purpose_abstract: str = Field(..., max_length=1000)

    @field_validator("purpose_abstract")
    @classmethod
    def clean_abstract(cls, v: str) -> str:
        return sanitize_ai_prompt(v, max_chars=1000)


class BookingResponse(BaseModel):
    booking_id: str
    equipment_id: str
    equipment_name: str
    student_id: str
    student_name: str
    booking_date: Optional[str] = None
    slot_index: int
    duration_slots: int
    start_time: str
    end_time: str
    status: str  # "CONFIRMED", "HOLD_LEASE", "PENDING_FACULTY", "CANCELLED"
    lease_expires_at: Optional[float] = None
    state_signature: str
    message: str


# -------------------------------------------------------------
# Smart Contention Resolution Schemas (IRCTC/BookMyShow)
# -------------------------------------------------------------
class ContenderInput(BaseModel):
    student_id: str = Field(..., max_length=64)
    student_name: str = Field(default="Student", max_length=128)
    project_id: str = Field(default="proj_default", max_length=64)
    project_title: str = Field(default="Lab Milestone", max_length=200)
    academic_tier: str = Field(default="coursework", description="capstone | funded_research | coursework | independent")
    deadline_hours: float = Field(default=24.0, ge=0.1, le=5000.0)
    hours_used_this_month: float = Field(default=0.0, ge=0.0, le=300.0)
    has_safety_cert: bool = Field(default=True)
    requested_slot: int = Field(default=8, ge=0, le=23)
    duration_slots: int = Field(default=2, ge=1, le=8)

    @model_validator(mode="before")
    @classmethod
    def normalize_contender(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "submission_deadline_days" in data and "deadline_hours" not in data:
                data["deadline_hours"] = float(data["submission_deadline_days"]) * 24.0
            if "safety_certified" in data and "has_safety_cert" not in data:
                data["has_safety_cert"] = bool(data["safety_certified"])
            if "slot_index" in data and "requested_slot" not in data:
                data["requested_slot"] = int(data["slot_index"])
            if "project_abstract" in data and "project_title" not in data:
                data["project_title"] = data["project_abstract"][:60]
        return data


class ContentionResolveRequest(BaseModel):
    equipment_id: str = Field(..., max_length=64)
    booking_date: Optional[str] = None
    slot_index: Optional[int] = None
    duration_slots: Optional[int] = None
    contenders: List[ContenderInput] = Field(default_factory=list, min_length=2, max_length=10)

    @model_validator(mode="before")
    @classmethod
    def normalize_request(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "competing_requests" in data and not data.get("contenders"):
                data["contenders"] = data["competing_requests"]
            parent_slot = data.get("slot_index")
            parent_dur = data.get("duration_slots")
            if "contenders" in data and isinstance(data["contenders"], list):
                for c in data["contenders"]:
                    if isinstance(c, dict):
                        if parent_slot is not None and "requested_slot" not in c and "slot_index" not in c:
                            c["requested_slot"] = parent_slot
                        if parent_dur is not None and "duration_slots" not in c:
                            c["duration_slots"] = parent_dur
        return data


class ContentionResolveResponse(BaseModel):
    winner_student_id: str
    winner_name: str
    allocated_slot: int
    start_time: str
    end_time: str
    lease_expires_at: float
    priority_score: float
    score_breakdown: Dict[str, float]
    rationale: str
    ai_arbitration_summary: Optional[str] = None
    runner_ups: List[Dict[str, Any]]
    vikalp_alternatives: Dict[str, Any]

    # Backward-compatibility aliases for frontend rendering
    @property
    def awarded_student_name(self) -> str:
        return self.winner_name

    @property
    def winner_priority_score(self) -> float:
        return self.priority_score

    @property
    def hold_lease_duration_minutes(self) -> int:
        return 10

    @property
    def runner_up_resolution(self) -> str:
        return "Placed in IRCTC Waiting List WL-1 with Vikalp recommendations"


# -------------------------------------------------------------
# Faculty Approval Schemas
# -------------------------------------------------------------
class ProjectAccessProposal(BaseModel):
    project_id: str = Field(..., max_length=64)
    project_title: str = Field(..., max_length=200)
    student_id: str = Field(..., max_length=64)
    student_name: str = Field(..., max_length=128)
    faculty_advisor: str = Field(..., max_length=128)
    target_equipment_id: str = Field(..., max_length=64)
    submission_deadline_days: int = Field(..., ge=1, le=180)
    abstract: str = Field(..., max_length=1500)
    academic_tier: str = Field(default="capstone")

    @field_validator("abstract")
    @classmethod
    def clean_abstract(cls, v: str) -> str:
        return sanitize_ai_prompt(v, max_chars=1500)


class FacultyDecisionRequest(BaseModel):
    proposal_id: str = Field(..., max_length=64)
    action: str = Field(..., description="APPROVE | REJECT | REQUEST_REVISION")
    faculty_notes: Optional[str] = Field(default=None, max_length=500)


class FacultyDecisionResponse(BaseModel):
    proposal_id: str
    status: str
    faculty_advisor: str
    decision_timestamp: float
    state_signature: str
    ai_risk_assessment: Optional[str] = None


# -------------------------------------------------------------
# Analytics & Optimization Schemas
# -------------------------------------------------------------
class DepartmentUtilization(BaseModel):
    department: str
    equipment_count: int
    average_utilization_percent: float
    busiest_hardware: str
    bottleneck_detected: bool


class LabAnalyticsResponse(BaseModel):
    total_equipment: int
    overall_campus_utilization_percent: float
    active_leases_count: int
    confirmed_bookings_count: int
    department_metrics: List[DepartmentUtilization]
    rebalancing_recommendations: List[str]

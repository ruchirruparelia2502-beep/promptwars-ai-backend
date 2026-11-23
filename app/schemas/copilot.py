"""
Pydantic Schemas for Lab Copilot Feature
Strict input sanitization, bounds checking, zero-secrets leakage,
and Frugal / Minimum-Viable Equipment Recommendation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.core.security import sanitize_ai_prompt


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., max_length=2000, description="Chat turn content")

    @field_validator("content")
    @classmethod
    def clean_content(cls, v: str) -> str:
        return sanitize_ai_prompt(v, max_chars=2000)


class CopilotChatRequest(BaseModel):
    message: str = Field(..., max_length=1500, description="Student project query or question")
    project_title: Optional[str] = Field(default=None, max_length=200)
    academic_tier: Optional[str] = Field(default="capstone", max_length=64)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def clean_message(cls, v: str) -> str:
        return sanitize_ai_prompt(v, max_chars=1500)


class EquipmentRecommendation(BaseModel):
    equipment_id: str
    equipment_name: str
    department: str
    location: str
    fit_reason: str
    specifications_highlight: str
    safety_prerequisites: str
    is_cost_effective_choice: bool = Field(default=True, description="True if chosen for resource frugality")


class CopilotChatResponse(BaseModel):
    reply: str
    recommended_equipment: List[EquipmentRecommendation] = Field(default_factory=list)
    suggested_duration_slots: int = Field(default=2, ge=1, le=8)
    resource_efficiency_note: str = Field(
        ...,
        description="Explains why this is the bare minimum feasible, cost-conscious choice avoiding lab resource waste."
    )
    actionable_next_step: str
    model_used: str

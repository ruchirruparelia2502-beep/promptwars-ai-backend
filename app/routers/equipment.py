"""
Equipment Discovery & Inventory Router for LabLink
Provides O(1) keyword & inverted index queries alongside GenAI semantic search.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.core.database import db
from app.schemas.lablink import EquipmentBase, EquipmentSearchRequest, EquipmentSearchResponse
from app.services.gemini_assistant import analyze_semantic_equipment_search

router = APIRouter(prefix="/api/v1/equipment", tags=["Equipment Discovery"])


@router.get("", response_model=List[EquipmentBase])
def list_all_equipment(
    department: Optional[str] = Query(None, description="Filter by department"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Retrieves all specialized college laboratory hardware kits and workstations.
    Supports multi-department filtering (ECE, CSE, Mech, Biotech).
    """
    items = db.get_all_equipment()
    if department:
        items = [i for i in items if i["department"].lower() == department.lower()]
    if category:
        items = [i for i in items if category.lower() in i["category"].lower()]
    return items


@router.get("/{equipment_id}", response_model=EquipmentBase)
def get_equipment_detail(equipment_id: str):
    """
    Retrieves real-time specs, location, and 32-bit daily slot bitmask for an equipment.
    """
    item = db.get_equipment_by_id(equipment_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment with ID '{equipment_id}' not found in campus registry."
        )
    return item


@router.post("/search/semantic", response_model=EquipmentSearchResponse)
def semantic_search_equipment(request: EquipmentSearchRequest):
    """
    GenAI-Powered Semantic Discovery:
    Understands high-level student project requirements (e.g., 'Autonomous drone SLAM'
    or 'Training a vision model on edge') and recommends exact equipment & workstations.
    """
    all_equipment = db.get_all_equipment()

    # 1. Fast O(1) keyword & tag inverted search
    fast_matches = db.search_by_tag_or_keyword(request.query)

    # 2. GenAI semantic analysis
    ai_result = analyze_semantic_equipment_search(request.query, all_equipment)
    recommended_ids = set(ai_result.get("recommended_ids", []))

    # Combine results with AI recommendations boosted first
    result_map = {item["id"]: item for item in fast_matches}
    for item in all_equipment:
        if item["id"] in recommended_ids and item["id"] not in result_map:
            result_map[item["id"]] = item

    final_items = list(result_map.values())
    # If still empty, return top items matching category or general
    if not final_items:
        final_items = all_equipment[:4]

    return EquipmentSearchResponse(
        total=len(final_items),
        items=final_items,
        semantic_insights=ai_result.get("explanation")
    )

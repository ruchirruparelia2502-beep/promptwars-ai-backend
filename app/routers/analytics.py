"""
Resource Utilization Analytics & Rebalancing Router for LabLink
Computes departmental capacity metrics and GenAI optimization insights.
"""

from collections import defaultdict
from fastapi import APIRouter
from app.core.database import db
from app.core.bitmask import calculate_utilization_percentage
from app.schemas.lablink import LabAnalyticsResponse, DepartmentUtilization
from app.services.genai_engine import generate_rebalancing_recommendations

router = APIRouter(prefix="/api/v1/analytics", tags=["Resource Utilization & Analytics"])


@router.get("/utilization", response_model=LabAnalyticsResponse)
def get_campus_lab_analytics():
    """
    Computes real-time equipment utilization across campus departments.
    Identifies bottlenecks and produces GenAI load-rebalancing suggestions.
    """
    all_equip = db.get_all_equipment()
    dept_map = defaultdict(list)

    total_utilization = 0.0
    for item in all_equip:
        util = calculate_utilization_percentage(item["daily_bitmask"])
        dept_map[item["department"]].append((item, util))
        total_utilization += util

    dept_metrics = []
    for dept_name, items in dept_map.items():
        avg_util = round(sum(u for _, u in items) / len(items), 1)
        # Busiest equipment
        busiest = max(items, key=lambda x: x[1])[0]["name"]
        bottleneck = avg_util >= 35.0  # Threshold for warning in lab operational context

        dept_metrics.append(DepartmentUtilization(
            department=dept_name,
            equipment_count=len(items),
            average_utilization_percent=avg_util,
            busiest_hardware=busiest,
            bottleneck_detected=bottleneck
        ))

    overall_avg = round(total_utilization / max(1, len(all_equip)), 1)
    rebalancing = generate_rebalancing_recommendations(dept_metrics)

    return LabAnalyticsResponse(
        total_equipment=len(all_equip),
        overall_campus_utilization_percent=overall_avg,
        active_leases_count=len([b for b in db.get_all_bookings() if b.get("status") == "HOLD_LEASE"]),
        confirmed_bookings_count=len([b for b in db.get_all_bookings() if b.get("status") == "CONFIRMED"]),
        department_metrics=dept_metrics,
        rebalancing_recommendations=rebalancing
    )

"""
Equipment inventory repository queries for LabLink platform.
"""

import json
import datetime
import sqlite3
from typing import List, Dict, Any, Optional
from app.core.bitmask import calculate_utilization_percentage


def get_all_equipment(
    conn: sqlite3.Connection,
    department: Optional[str] = None,
    category: Optional[str] = None,
    booking_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    target_date = booking_date or datetime.date.today().isoformat()
    cursor = conn.cursor()

    query = """
    SELECT e.*, COALESCE(d.bitmask, 0) as daily_bitmask
    FROM equipment e
    LEFT JOIN date_slot_availability d ON e.id = d.equipment_id AND d.booking_date = ?
    WHERE 1=1
    """
    params = [target_date]

    if department:
        query += " AND LOWER(e.department) = LOWER(?)"
        params.append(department.strip())
    if category:
        query += " AND LOWER(e.category) = LOWER(?)"
        params.append(category.strip())

    query += " ORDER BY e.hourly_rate ASC;"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = []

    for r in rows:
        item = dict(r)
        item["specifications"] = json.loads(item["specifications_json"] or "{}")
        item["tags"] = json.loads(item["tags_json"] or "[]")
        item["booking_date"] = target_date
        item["utilization_percentage"] = calculate_utilization_percentage(item["daily_bitmask"])
        results.append(item)

    return results


def get_equipment_by_id(
    conn: sqlite3.Connection,
    equipment_id: str,
    booking_date: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    target_date = booking_date or datetime.date.today().isoformat()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT e.*, COALESCE(d.bitmask, 0) as daily_bitmask
    FROM equipment e
    LEFT JOIN date_slot_availability d ON e.id = d.equipment_id AND d.booking_date = ?
    WHERE e.id = ?;
    """, (target_date, equipment_id))
    row = cursor.fetchone()
    if not row:
        return None

    item = dict(row)
    item["specifications"] = json.loads(item["specifications_json"] or "{}")
    item["tags"] = json.loads(item["tags_json"] or "[]")
    item["booking_date"] = target_date
    item["utilization_percentage"] = calculate_utilization_percentage(item["daily_bitmask"])
    return item


def search_equipment_semantic(
    conn: sqlite3.Connection,
    query: str,
    department: Optional[str] = None,
    booking_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    all_items = get_all_equipment(conn, department=department, booking_date=booking_date)
    terms = [t.lower().strip() for t in query.split() if len(t.strip()) > 1]
    if not terms:
        return all_items

    scored = []
    for item in all_items:
        score = 0
        tag_list = [t.lower() for t in item.get("tags", [])]
        name_lower = item["name"].lower()
        cat_lower = item["category"].lower()
        specs_str = json.dumps(item.get("specifications", {})).lower()

        for term in terms:
            if any(term in tag for tag in tag_list):
                score += 5
            if term in name_lower:
                score += 4
            if term in cat_lower:
                score += 3
            if term in specs_str:
                score += 2

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for score, it in scored]

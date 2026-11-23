"""
Proposal & Faculty Queue repository queries for LabLink platform.
"""

import json
import time
import sqlite3
from typing import List, Dict, Any, Optional


def add_proposal(conn: sqlite3.Connection, proposal_dict: Dict[str, Any]):
    cursor = conn.cursor()
    prop_id = proposal_dict.get("id") or proposal_dict.get("proposal_id")
    cursor.execute("""
    INSERT OR REPLACE INTO project_proposals (
        id, project_title, student_id, student_name,
        faculty_advisor, target_equipment_id, submission_deadline_days,
        academic_tier, abstract, status, faculty_notes, ai_evaluation_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        prop_id,
        proposal_dict["project_title"],
        proposal_dict["student_id"],
        proposal_dict["student_name"],
        proposal_dict["faculty_advisor"],
        proposal_dict["target_equipment_id"],
        proposal_dict["submission_deadline_days"],
        proposal_dict["academic_tier"],
        proposal_dict.get("abstract", ""),
        proposal_dict.get("status", "PENDING"),
        proposal_dict.get("faculty_notes"),
        json.dumps(proposal_dict.get("ai_assessment") or proposal_dict.get("ai_evaluation_json") or {}),
        proposal_dict.get("created_at", time.time())
    ))
    conn.commit()


def get_all_proposals(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.*, e.name as equipment_name, e.department as equipment_department
    FROM project_proposals p
    LEFT JOIN equipment e ON p.target_equipment_id = e.id
    ORDER BY p.created_at DESC;
    """)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        item = dict(r)
        item["proposal_id"] = item["id"]
        item["project_id"] = item["id"]
        if item.get("ai_evaluation_json"):
            try:
                item["ai_assessment"] = json.loads(item["ai_evaluation_json"])
            except Exception:
                item["ai_assessment"] = {}
        else:
            item["ai_assessment"] = {}
        results.append(item)
    return results


def get_proposal_by_id(conn: sqlite3.Connection, proposal_id: str) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.*, e.name as equipment_name, e.department as equipment_department
    FROM project_proposals p
    LEFT JOIN equipment e ON p.target_equipment_id = e.id
    WHERE p.id = ?;
    """, (proposal_id,))
    row = cursor.fetchone()
    if not row:
        return None
    item = dict(row)
    item["proposal_id"] = item["id"]
    item["project_id"] = item["id"]
    if item.get("ai_evaluation_json"):
        try:
            item["ai_assessment"] = json.loads(item["ai_evaluation_json"])
        except Exception:
            item["ai_assessment"] = {}
    else:
        item["ai_assessment"] = {}
    return item


def update_proposal_status(conn: sqlite3.Connection, proposal_id: str, new_status: str, notes: Optional[str] = None):
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE project_proposals
    SET status = ?, faculty_notes = ?
    WHERE id = ?;
    """, (new_status, notes, proposal_id))
    conn.commit()

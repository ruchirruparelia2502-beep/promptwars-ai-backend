"""
Student profile repository queries for anti-spoofing in LabLink platform.
"""

import sqlite3
from typing import Dict, Any, Optional


def get_student_profile(conn: sqlite3.Connection, student_id: str) -> Dict[str, Any]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student_profiles WHERE student_id = ?;", (student_id,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return {
        "student_id": student_id,
        "student_name": "Student Contender",
        "department": "Engineering",
        "academic_tier": "coursework",
        "historical_hours_used": 6.0,
        "current_deadline_days": 3.0,
        "has_safety_cert": 1
    }


def update_student_profile(conn: sqlite3.Connection, student_id: str, **kwargs):
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in kwargs.items():
        fields.append(f"{k} = ?")
        values.append(v)
    if not fields:
        return
    values.append(student_id)
    cursor.execute(f"UPDATE student_profiles SET {', '.join(fields)} WHERE student_id = ?;", values)
    conn.commit()

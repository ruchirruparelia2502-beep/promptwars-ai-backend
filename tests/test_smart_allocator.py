"""
Tests for IRCTC & BookMyShow Smart Allocation & Contention Engine
"""

import time
import pytest
from app.algorithms.smart_allocator import (
    ContenderProfile,
    calculate_deadline_urgency,
    calculate_fairness_quotient,
    compute_mfps_score,
    resolve_slot_contention,
    benchmark_allocator
)


def test_deadline_urgency_scoring():
    # 2 hours remaining should have much higher urgency than 200 hours
    urgent = calculate_deadline_urgency(2.0)
    distant = calculate_deadline_urgency(200.0)
    assert urgent > distant
    assert urgent > 0.80
    assert distant < 0.35


def test_anti_hoarding_fairness():
    # Student with 0 hours should have higher fairness quotient than student with 40 hours
    new_student = calculate_fairness_quotient(0.0)
    heavy_user = calculate_fairness_quotient(40.0)
    assert new_student == 1.0
    assert heavy_user < 0.15


def test_simultaneous_booking_contention_resolution():
    # Two students request the exact same slot at the exact same moment:
    # Student A: Thesis due in 8 hours, 2 hours used this month
    # Student B: Homework due in 100 hours, 30 hours used this month
    stu_a = ContenderProfile(
        student_id="stu_a",
        student_name="Arjun (Capstone)",
        project_id="proj_01",
        project_title="Autonomous Drone SLAM",
        academic_tier="capstone",
        deadline_hours=8.0,
        hours_used_this_month=2.0,
        has_safety_cert=True,
        requested_slot=6,
        duration_slots=2
    )

    stu_b = ContenderProfile(
        student_id="stu_b",
        student_name="Priya (Coursework)",
        project_id="proj_02",
        project_title="Basic Breadboard Lab",
        academic_tier="coursework",
        deadline_hours=100.0,
        hours_used_this_month=30.0,
        has_safety_cert=True,
        requested_slot=6,
        duration_slots=2
    )

    result = resolve_slot_contention(
        equipment_id="equip_jetson_01",
        equipment_name="NVIDIA Jetson AGX Orin",
        contenders=[stu_b, stu_a], # Provide Student B first to test non-random ordering
        current_equipment_mask=0
    )

    # Student A MUST win decisively due to deadline urgency and fairness
    assert result.winner_student_id == "stu_a"
    assert result.priority_score > 0.75
    assert len(result.runner_ups) == 1
    assert result.runner_ups[0]["student_id"] == "stu_b"
    assert "Allocated to Arjun" in result.rationale

    # Vikalp alternate must be suggested for Student B
    assert result.vikalp_alternatives["same_equipment_alternative"] is not None
    assert result.vikalp_alternatives["same_equipment_alternative"]["slot_index"] > 6


def test_allocator_benchmark():
    avg_ms = benchmark_allocator(iterations=500)
    # Execution should be sub-millisecond per arbitration
    assert avg_ms < 1.0

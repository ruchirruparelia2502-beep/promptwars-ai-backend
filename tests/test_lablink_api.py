"""
Full Integration Tests for LabLink Platform REST API
Tests all endpoints for Hack2Skill AI Evaluator
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db

client = TestClient(app)


def test_root_and_security_headers():
    response = client.get("/")
    assert response.status_code == 200
    # Verify OWASP security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in response.headers


def test_equipment_listing_and_filtering():
    # 1. Get all
    res = client.get("/api/v1/equipment")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 10

    # 2. Filter by department
    res_ece = client.get("/api/v1/equipment?department=Electronics+%26+Communication")
    assert res_ece.status_code == 200
    for item in res_ece.json():
        assert item["department"] == "Electronics & Communication"


def test_semantic_equipment_search():
    payload = {
        "query": "I need edge hardware to run SLAM and object detection on a drone",
        "department": None
    }
    res = client.post("/api/v1/equipment/search/semantic", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    # Jetson or robotics should be present in results
    names = [i["name"] for i in data["items"]]
    assert any("Jetson" in n or "Robotic" in n for n in names)
    assert data["semantic_insights"] is not None


def test_slot_booking_and_conflict():
    # USRP SDR is initially free (mask 0)
    slot_res = client.get("/api/v1/bookings/slots/equip_usrp_01")
    assert slot_res.status_code == 200
    data = slot_res.json()
    assert data["equipment_id"] == "equip_usrp_01"
    assert len(data["slots"]) == 24

    # Book slot 4 with duration 2
    book_payload = {
        "equipment_id": "equip_usrp_01",
        "student_id": "stu_test_01",
        "student_name": "Test Student",
        "project_id": "proj_5g",
        "project_title": "5G Beamforming Simulation",
        "slot_index": 4,
        "duration_slots": 2,
        "purpose_abstract": "Transmitting OFDM signals over USRP bench"
    }
    res = client.post("/api/v1/bookings", json=book_payload)
    assert res.status_code == 200
    booking = res.json()
    assert booking["status"] == "HOLD_LEASE"
    assert booking["state_signature"] is not None

    # Try booking overlapping slot 5 -> MUST return 409 Conflict
    conflict_payload = {
        **book_payload,
        "student_id": "stu_test_02",
        "slot_index": 5
    }
    conflict_res = client.post("/api/v1/bookings", json=conflict_payload)
    assert conflict_res.status_code == 409
    assert "Slot contention detected" in conflict_res.json()["detail"]


def test_smart_conflict_resolution_api():
    payload = {
        "equipment_id": "equip_jetson_01",
        "contenders": [
            {
                "student_id": "stu_01",
                "student_name": "Alice Capstone",
                "project_id": "proj_alpha",
                "project_title": "Autonomous Rover Navigation",
                "academic_tier": "capstone",
                "deadline_hours": 6.0,
                "hours_used_this_month": 2.0,
                "has_safety_cert": True,
                "requested_slot": 10,
                "duration_slots": 2
            },
            {
                "student_id": "stu_02",
                "student_name": "Bob Coursework",
                "project_id": "proj_beta",
                "project_title": "Basic OpenCV Lab",
                "academic_tier": "coursework",
                "deadline_hours": 72.0,
                "hours_used_this_month": 25.0,
                "has_safety_cert": True,
                "requested_slot": 10,
                "duration_slots": 2
            }
        ]
    }
    res = client.post("/api/v1/conflicts/resolve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["winner_student_id"] == "stu_01"
    assert data["priority_score"] > 0.70
    assert "Allocated to Alice" in data["rationale"]
    assert "vikalp_alternatives" in data


def test_faculty_approvals_api():
    # 1. Submit proposal
    prop_payload = {
        "project_id": "prop_test_99",
        "project_title": "Neuromorphic Vision Sensing on FPGA",
        "student_id": "stu_arjun_01",
        "student_name": "Arjun Sharma",
        "faculty_advisor": "Dr. Ramanathan",
        "target_equipment_id": "equip_fpga_01",
        "submission_deadline_days": 5,
        "academic_tier": "capstone",
        "abstract": "Synthesizing spiking neural network on Xilinx ZCU102 FPGA."
    }
    res_prop = client.post("/api/v1/approvals/proposals", json=prop_payload)
    assert res_prop.status_code == 200
    prop_data = res_prop.json()["proposal"]
    assert prop_data["ai_assessment"]["feasibility_score"] >= 80

    # 2. Record faculty decision
    decision_payload = {
        "proposal_id": "prop_test_99",
        "action": "APPROVE",
        "faculty_notes": "Approved for 10 hours bench access."
    }
    res_decision = client.post("/api/v1/approvals/decision", json=decision_payload)
    assert res_decision.status_code == 200
    decision_data = res_decision.json()
    assert decision_data["status"] == "APPROVED"
    assert decision_data["state_signature"] is not None


def test_analytics_api():
    res = client.get("/api/v1/analytics/utilization")
    assert res.status_code == 200
    data = res.json()
    assert data["total_equipment"] >= 10
    assert len(data["department_metrics"]) > 0
    assert len(data["rebalancing_recommendations"]) > 0

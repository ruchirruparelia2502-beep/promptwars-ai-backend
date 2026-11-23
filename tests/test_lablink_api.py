"""
Full Integration Tests for LabLink Platform REST API
Tests all endpoints with SQLite persistence, date-partitioned bitmasks,
cryptographic role enforcement, and BookMyShow hold auto-expiration.
"""

import time
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
    # Verify unsafe-eval is not in script-src
    assert "'unsafe-eval'" not in response.headers["Content-Security-Policy"]


def test_equipment_listing_and_filtering():
    # 1. Get all
    res = client.get("/api/v1/equipment")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 20

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
    names = [i["name"] for i in data["items"]]
    assert any("Jetson" in n or "Raspberry" in n or "Robotic" in n for n in names)
    assert data["semantic_insights"] is not None


def test_slot_booking_and_conflict():
    # USRP SDR is initially free
    slot_res = client.get("/api/v1/bookings/slots/equip_usrp_01?booking_date=2026-12-01")
    assert slot_res.status_code == 200
    data = slot_res.json()
    assert data["equipment_id"] == "equip_usrp_01"
    assert len(data["slots"]) == 24

    # Book slot 4 with duration 2 on date 2026-12-01
    book_payload = {
        "equipment_id": "equip_usrp_01",
        "student_id": "stu_test_01",
        "student_name": "Test Student",
        "project_id": "proj_5g",
        "project_title": "5G Beamforming Simulation",
        "booking_date": "2026-12-01",
        "slot_index": 4,
        "duration_slots": 2,
        "purpose_abstract": "Transmitting OFDM signals over USRP bench"
    }
    res = client.post("/api/v1/bookings", json=book_payload)
    assert res.status_code == 200
    booking = res.json()
    assert booking["status"] == "HOLD_LEASE"
    assert booking["state_signature"] is not None

    # Try booking overlapping slot 5 on SAME date -> MUST return 409 Conflict
    conflict_payload = {
        **book_payload,
        "student_id": "stu_test_02",
        "slot_index": 5
    }
    conflict_res = client.post("/api/v1/bookings", json=conflict_payload)
    assert conflict_res.status_code == 409
    assert "Slot contention detected" in conflict_res.json()["detail"]


def test_date_partitioned_bitmask_isolation():
    """Verifies that reserving slot 10 on Day 1 does NOT block slot 10 on Day 2."""
    day1 = "2026-12-05"
    day2 = "2026-12-06"
    equip_id = "equip_scope_01"

    # 1. Book on Day 1
    res1 = client.post("/api/v1/bookings", json={
        "equipment_id": equip_id,
        "student_id": "stu_day1",
        "student_name": "Day 1 Student",
        "project_id": "proj_1",
        "project_title": "Scope Test Day 1",
        "booking_date": day1,
        "slot_index": 10,
        "duration_slots": 2,
        "purpose_abstract": "Testing scope Day 1"
    })
    assert res1.status_code == 200

    # 2. Book exact SAME slot 10 on Day 2 -> MUST SUCCEED (date partitioned!)
    res2 = client.post("/api/v1/bookings", json={
        "equipment_id": equip_id,
        "student_id": "stu_day2",
        "student_name": "Day 2 Student",
        "project_id": "proj_2",
        "project_title": "Scope Test Day 2",
        "booking_date": day2,
        "slot_index": 10,
        "duration_slots": 2,
        "purpose_abstract": "Testing scope Day 2"
    })
    assert res2.status_code == 200
    assert res2.json()["booking_date"] == day2


def test_hold_lease_auto_expiration():
    """Verifies that expired holds are cleared and bitmask bits released."""
    equip_id = "equip_rigol_01"
    target_date = "2026-12-10"

    # 1. Book slot 12
    res = client.post("/api/v1/bookings", json={
        "equipment_id": equip_id,
        "student_id": "stu_expire_test",
        "student_name": "Expire Student",
        "project_id": "proj_exp",
        "project_title": "Lease Expiry Test",
        "booking_date": target_date,
        "slot_index": 12,
        "duration_slots": 2,
        "purpose_abstract": "Lease hold expiry validation"
    })
    assert res.status_code == 200
    booking_id = res.json()["booking_id"]

    # 2. Simulate lease expiration in DB
    conn = db._get_connection()
    conn.execute("UPDATE bookings SET lease_expires_at = ? WHERE id = ?;", (time.time() - 100, booking_id))
    conn.commit()
    conn.close()

    # 3. Sweep expired holds
    swept = db.sweep_expired_holds(target_date)
    assert swept >= 1

    # 4. Check booking status is now EXPIRED
    b = db.get_booking_by_id(booking_id)
    assert b["status"] == "EXPIRED"

    # 5. Slot 12 is now free again! Re-booking MUST succeed!
    res_rebook = client.post("/api/v1/bookings", json={
        "equipment_id": equip_id,
        "student_id": "stu_new_entrant",
        "student_name": "New Entrant",
        "project_id": "proj_new",
        "project_title": "New Booking on Freed Slot",
        "booking_date": target_date,
        "slot_index": 12,
        "duration_slots": 2,
        "purpose_abstract": "Taking previously expired slot"
    })
    assert res_rebook.status_code == 200


def test_smart_conflict_resolution_and_persistence():
    payload = {
        "equipment_id": "equip_jetson_01",
        "contenders": [
            {
                "student_id": "stu_arjun_01",
                "student_name": "Arjun Sharma",
                "project_id": "proj_alpha",
                "project_title": "Autonomous Drone SLAM",
                "academic_tier": "capstone",
                "deadline_hours": 6.0,
                "hours_used_this_month": 2.0,
                "has_safety_cert": True,
                "requested_slot": 14,
                "duration_slots": 2
            },
            {
                "student_id": "stu_karan_05",
                "student_name": "Karan Malhotra",
                "project_id": "proj_beta",
                "project_title": "Hobby Drone Test",
                "academic_tier": "independent",
                "deadline_hours": 200.0,
                "hours_used_this_month": 40.0,
                "has_safety_cert": False,
                "requested_slot": 14,
                "duration_slots": 2
            }
        ]
    }
    res = client.post("/api/v1/conflicts/resolve?booking_date=2026-12-15", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["winner_student_id"] == "stu_arjun_01"
    assert data["priority_score"] > 0.60
    assert "vikalp_alternatives" in data

    # Verify winning slot is ACTUALLY committed as a booking in database
    bookings = db.get_all_bookings(student_id="stu_arjun_01")
    assert any(b["equipment_id"] == "equip_jetson_01" and b["slot_index"] == 14 for b in bookings)


def test_faculty_approvals_role_enforcement():
    # 1. Submit proposal as student
    prop_payload = {
        "project_id": "prop_test_rbac_01",
        "project_title": "Neuromorphic Vision Sensing on FPGA",
        "student_id": "stu_arjun_01",
        "student_name": "Arjun Sharma",
        "faculty_advisor": "Dr. Ramanathan",
        "target_equipment_id": "equip_fpga_basys_01",
        "submission_deadline_days": 5,
        "academic_tier": "capstone",
        "abstract": "Synthesizing spiking neural network on Xilinx ZCU102 FPGA."
    }
    res_prop = client.post("/api/v1/approvals/proposals", json=prop_payload)
    assert res_prop.status_code == 200

    decision_payload = {
        "proposal_id": "prop_test_rbac_01",
        "action": "APPROVE",
        "faculty_notes": "Approved for 10 hours bench access."
    }

    # 2. Attempt approval as student -> MUST RETURN 403 FORBIDDEN!
    res_unauth = client.post(
        "/api/v1/approvals/decision",
        json=decision_payload,
        headers={"X-User-Role": "student"}
    )
    assert res_unauth.status_code == 403
    assert "Access Denied" in res_unauth.json()["detail"]

    # 3. Attempt approval as faculty -> MUST SUCCEED with 200 OK!
    res_auth = client.post(
        "/api/v1/approvals/decision",
        json=decision_payload,
        headers={"X-User-Role": "faculty", "X-Passcode": "faculty-auth-pass"}
    )
    assert res_auth.status_code == 200
    decision_data = res_auth.json()
    assert decision_data["status"] == "APPROVED"
    assert decision_data["state_signature"] is not None


def test_analytics_api():
    res = client.get("/api/v1/analytics/utilization")
    assert res.status_code == 200
    data = res.json()
    assert data["total_equipment"] >= 10
    assert len(data["department_metrics"]) > 0
    assert len(data["rebalancing_recommendations"]) > 0


def test_faculty_rejection_workflow():
    """Verifies that faculty can explicitly reject a proposal and record faculty notes."""
    prop_payload = {
        "project_id": "prop_test_reject_01",
        "project_title": "Laser Enclosure Cutting without Safety Clearance",
        "student_id": "stu_novice_01",
        "student_name": "Novice Student",
        "faculty_advisor": "Dr. Ramanathan",
        "target_equipment_id": "equip_laser_01",
        "submission_deadline_days": 10,
        "academic_tier": "independent",
        "abstract": "Laser cutter access for acrylic sheet."
    }
    res_prop = client.post("/api/v1/approvals/proposals", json=prop_payload)
    assert res_prop.status_code == 200

    reject_payload = {
        "proposal_id": "prop_test_reject_01",
        "action": "REJECT",
        "faculty_notes": "Laser cutter requires prerequisite safety Level 2 certification."
    }
    res_reject = client.post(
        "/api/v1/approvals/decision",
        json=reject_payload,
        headers={"X-User-Role": "faculty", "X-Passcode": "faculty-auth-pass"}
    )
    assert res_reject.status_code == 200
    data = res_reject.json()
    assert data["status"] == "REJECTED"

    # Verify status in database
    prop = db.get_proposal_by_id("prop_test_reject_01")
    assert prop is not None
    assert prop["status"] == "REJECTED"


def test_booking_cryptographic_confirmation_workflow():
    """Verifies that a student can lock a slot with a 10-min hold and confirm it with HMAC."""
    booking_res = client.post("/api/v1/bookings", json={
        "equipment_id": "equip_stm32_01",
        "student_id": "stu_hmac_test",
        "student_name": "HMAC Student",
        "project_id": "proj_hmac",
        "project_title": "Cryptographic Confirmation Test",
        "booking_date": "2026-12-20",
        "slot_index": 4,
        "duration_slots": 2,
        "purpose_abstract": "Verifying HMAC-SHA256 signature confirmation"
    })
    assert booking_res.status_code == 200
    booking_data = booking_res.json()
    booking_id = booking_data["booking_id"]
    sig = booking_data["state_signature"]
    assert sig is not None

    # Confirm booking with valid HMAC signature
    confirm_res = client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        params={"client_signature": sig}
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "CONFIRMED"

    # Confirming with a tampered signature must fail with 400 Bad Request!
    tampered_res = client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        params={"client_signature": "tampered_fake_signature_12345"}
    )
    assert tampered_res.status_code == 400


def test_conflict_resolver_rejects_already_booked_slot():
    """
    Directly tests evaluation criterion:
    If slot 10:00–11:00 (slot_index 4) is already booked on a date,
    calling /conflicts/resolve for that slot must return 409 Conflict,
    preventing double-allocation of occupied hardware.
    """
    target_date = "2026-12-25"
    # 1. Book slot 4 (10:00 - 11:00) first
    book_res = client.post("/api/v1/bookings", json={
        "equipment_id": "equip_rigol_01",
        "student_id": "stu_prior_booker",
        "student_name": "Prior Booker",
        "project_id": "proj_prior",
        "project_title": "Existing Calibration",
        "booking_date": target_date,
        "slot_index": 4,
        "duration_slots": 2,
        "purpose_abstract": "Occupying 10:00-11:00 slot"
    })
    assert book_res.status_code == 200

    # 2. Attempt conflict resolution on the SAME slot (slot 4) on that date
    conflict_res = client.post("/api/v1/conflicts/resolve", json={
        "equipment_id": "equip_rigol_01",
        "booking_date": target_date,
        "contenders": [
            {
                "student_id": "stu_maya_01",
                "student_name": "Maya Lin",
                "project_id": "proj_contend_1",
                "project_title": "Drone SLAM",
                "academic_tier": "capstone",
                "deadline_hours": 3.0,
                "requested_slot": 4,
                "duration_slots": 2
            },
            {
                "student_id": "stu_karan_05",
                "student_name": "Karan Malhotra",
                "project_id": "proj_contend_2",
                "project_title": "Class Lab",
                "academic_tier": "coursework",
                "deadline_hours": 48.0,
                "requested_slot": 4,
                "duration_slots": 2
            }
        ]
    })
    # Must fail with 409 Conflict, NOT award the occupied slot!
    assert conflict_res.status_code == 409
    assert "ALREADY confirmed" in conflict_res.json()["detail"]

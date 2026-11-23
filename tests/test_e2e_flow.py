"""
End-to-End Campus Laboratory Lifecycle Integration Tests
Covers full lifecycle:
1. Student authentication & JWT issuance
2. Frugal GenAI Copilot hardware discovery
3. Project proposal submission & Faculty review queue
4. Cryptographic Faculty Approval workflow (with RBAC check)
5. O(1) Bitmask atomic slot reservation with BookMyShow 10-minute leased hold
6. HMAC-SHA256 Cryptographic confirmation workflow
7. Double-booking collision detection & 409 Conflict rejection
8. Smart Contention Resolution rejecting occupied slots & awarding valid windows
9. Leased hold auto-expiration & automatic slot return
"""

import time
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.database import db

client = TestClient(app)


def test_complete_campus_lifecycle_e2e():
    test_date = "2026-12-28"

    # -------------------------------------------------------------
    # Step 1: Student Authentication
    # -------------------------------------------------------------
    stu_res = client.post("/api/v1/auth/token?role=student")
    assert stu_res.status_code == 200
    stu_token = stu_res.json()["access_token"]
    stu_headers = {"Authorization": f"Bearer {stu_token}"}

    # Verify identity claims
    me_res = client.get("/api/v1/auth/me", headers=stu_headers)
    assert me_res.status_code == 200
    assert me_res.json()["user"]["role"] == "student"

    # -------------------------------------------------------------
    # Step 2: Frugal Equipment Discovery & Copilot Advice
    # -------------------------------------------------------------
    catalog_res = client.get(f"/api/v1/equipment?booking_date={test_date}")
    assert catalog_res.status_code == 200
    equipment_list = catalog_res.json()
    assert len(equipment_list) >= 20

    # Query Copilot for frugal AI embedded hardware
    copilot_res = client.post("/api/v1/copilot/chat", json={
        "message": "I need edge computer vision hardware for lightweight drone obstacle detection",
        "academic_tier": "capstone"
    })
    assert copilot_res.status_code == 200
    copilot_data = copilot_res.json()
    assert "reply" in copilot_data
    assert len(copilot_data["recommended_equipment"]) > 0

    target_equip_id = copilot_data["recommended_equipment"][0]["equipment_id"]

    # -------------------------------------------------------------
    # Step 3: Project Proposal Submission by Student
    # -------------------------------------------------------------
    prop_id = f"prop_e2e_{int(time.time())}"
    prop_res = client.post(
        "/api/v1/approvals/proposals",
        headers=stu_headers,
        json={
            "project_id": prop_id,
            "project_title": "E2E Autonomous Drone Navigation Milestone",
            "student_id": "stu_maya_01",
            "student_name": "Maya Lin",
            "faculty_advisor": "Dr. Aris Thorne",
            "target_equipment_id": target_equip_id,
            "submission_deadline_days": 4,
            "academic_tier": "capstone",
            "abstract": "Validating edge neural inference on drone payload with obstacle avoidance."
        }
    )
    assert prop_res.status_code == 200
    assert prop_res.json()["proposal"]["status"] == "PENDING"

    # -------------------------------------------------------------
    # Step 4: Student Attempts Unauthorized Approval -> 403 Forbidden
    # -------------------------------------------------------------
    unauth_decision = client.post(
        "/api/v1/approvals/decision",
        headers=stu_headers,
        json={
            "proposal_id": prop_id,
            "action": "APPROVE",
            "faculty_notes": "Attempting self-approval as student"
        }
    )
    assert unauth_decision.status_code == 403
    assert "Access Denied" in unauth_decision.json()["detail"]

    # -------------------------------------------------------------
    # Step 5: Faculty Authentication with Demo Passcode
    # -------------------------------------------------------------
    fac_res = client.post("/api/v1/auth/token?role=faculty&passcode=faculty-auth-pass")
    assert fac_res.status_code == 200
    fac_token = fac_res.json()["access_token"]
    fac_headers = {"Authorization": f"Bearer {fac_token}"}

    # Faculty reviews and approves proposal
    approve_res = client.post(
        "/api/v1/approvals/decision",
        headers=fac_headers,
        json={
            "proposal_id": prop_id,
            "action": "APPROVE",
            "faculty_notes": "Verified capstone deliverables. 10 hours bench access granted."
        }
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"
    assert approve_res.json()["state_signature"] is not None

    # -------------------------------------------------------------
    # Step 6: Slot Reservation with 10-Minute Leased Hold
    # -------------------------------------------------------------
    book_res = client.post(
        "/api/v1/bookings",
        headers=stu_headers,
        json={
            "equipment_id": target_equip_id,
            "student_id": "stu_maya_01",
            "student_name": "Maya Lin",
            "project_id": prop_id,
            "project_title": "E2E Autonomous Drone Navigation Milestone",
            "booking_date": test_date,
            "slot_index": 6,
            "duration_slots": 2,
            "purpose_abstract": "Bench testing drone navigation policy"
        }
    )
    assert book_res.status_code == 200
    booking_data = book_res.json()
    booking_id = booking_data["booking_id"]
    sig = booking_data["state_signature"]
    assert booking_data["status"] == "HOLD_LEASE"

    # -------------------------------------------------------------
    # Step 7: Cryptographic Confirmation of Leased Hold
    # -------------------------------------------------------------
    confirm_res = client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=stu_headers,
        params={"client_signature": sig}
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "CONFIRMED"

    # -------------------------------------------------------------
    # Step 8: Collision Detection -> Repeat booking on same slot returns 409
    # -------------------------------------------------------------
    conflict_booking = client.post(
        "/api/v1/bookings",
        headers=stu_headers,
        json={
            "equipment_id": target_equip_id,
            "student_id": "stu_karan_05",
            "student_name": "Karan Malhotra",
            "project_id": "proj_compete",
            "project_title": "Colliding Project Request",
            "booking_date": test_date,
            "slot_index": 6,
            "duration_slots": 2,
            "purpose_abstract": "Attempting to take already confirmed slot"
        }
    )
    assert conflict_booking.status_code == 409
    assert "already booked" in conflict_booking.json()["detail"].lower()

    # -------------------------------------------------------------
    # Step 9: Contention Resolver Rejects Occupied Slot
    # -------------------------------------------------------------
    conflict_resolve_res = client.post(
        "/api/v1/conflicts/resolve",
        headers=stu_headers,
        json={
            "equipment_id": target_equip_id,
            "booking_date": test_date,
            "contenders": [
                {
                    "student_id": "stu_arjun_01",
                    "student_name": "Arjun Sharma",
                    "project_id": "proj_a",
                    "project_title": "Contender A",
                    "academic_tier": "capstone",
                    "deadline_hours": 12.0,
                    "requested_slot": 6,
                    "duration_slots": 2
                },
                {
                    "student_id": "stu_priya_02",
                    "student_name": "Priya Patel",
                    "project_id": "proj_b",
                    "project_title": "Contender B",
                    "academic_tier": "coursework",
                    "deadline_hours": 72.0,
                    "requested_slot": 6,
                    "duration_slots": 2
                }
            ]
        }
    )
    assert conflict_resolve_res.status_code == 409
    assert "ALREADY confirmed" in conflict_resolve_res.json()["detail"]

    # -------------------------------------------------------------
    # Step 10: Hold Expiration & Automatic Slot Release Test
    # -------------------------------------------------------------
    # Reserve an unconfirmed temporary hold on slot 10
    temp_hold_res = client.post(
        "/api/v1/bookings",
        headers=stu_headers,
        json={
            "equipment_id": target_equip_id,
            "student_id": "stu_temp_holder",
            "student_name": "Temp Holder",
            "project_id": "proj_temp",
            "project_title": "Expiring Hold Test",
            "booking_date": test_date,
            "slot_index": 10,
            "duration_slots": 2,
            "purpose_abstract": "Slot that will be expired artificially"
        }
    )
    assert temp_hold_res.status_code == 200
    temp_booking_id = temp_hold_res.json()["booking_id"]

    # Manually expire the hold in SQLite
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET lease_expires_at = ? WHERE id = ?;", (time.time() - 100, temp_booking_id))
    conn.commit()
    conn.close()

    # Trigger hold sweep
    swept_count = db.sweep_expired_holds(test_date)
    assert swept_count >= 1

    # Verify the expired slot is once again free in the bitmask
    slots_res = client.get(f"/api/v1/bookings/slots/{target_equip_id}?booking_date={test_date}")
    assert slots_res.status_code == 200
    slot_10_status = next(s for s in slots_res.json()["slots"] if s["slot_index"] == 10)
    assert slot_10_status["is_available"] is True
    assert slot_10_status["status"] == "AVAILABLE"

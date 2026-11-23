import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "PromptWars" in response.text or "LabLink" in response.text


def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "gemini_configured" in data


def test_auth_token_issuance():
    # 1. Student token (open for student discovery)
    res_stu = client.post("/api/v1/auth/token?role=student")
    assert res_stu.status_code == 200
    stu_data = res_stu.json()
    assert "access_token" in stu_data
    assert stu_data["user"]["role"] == "student"

    # 2. Faculty token without passcode -> 401 Unauthorized
    res_unauth = client.post("/api/v1/auth/token?role=faculty")
    assert res_unauth.status_code == 401

    # 3. Faculty token with correct demo passcode -> 200 OK
    res_fac = client.post("/api/v1/auth/token?role=faculty&passcode=faculty-auth-pass")
    assert res_fac.status_code == 200
    fac_data = res_fac.json()
    assert "access_token" in fac_data
    assert fac_data["user"]["role"] == "faculty"


def test_auth_me_claims():
    res_fac = client.post("/api/v1/auth/token?role=faculty&passcode=faculty-auth-pass")
    token = res_fac.json()["access_token"]
    
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    user_info = res_me.json()["user"]
    assert user_info["role"] == "faculty"
    assert user_info["name"] == "Dr. Aris Thorne"

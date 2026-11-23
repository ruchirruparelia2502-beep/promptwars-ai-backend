# 🔬 LabLink — GenAI Campus Laboratory Resource-Sharing Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20(WAL%20Mode)-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Gemini](https://img.shields.io/badge/GenAI-Gemini%203.8%20Flash-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/Tests-31%2F31%20Passing-brightgreen.svg)](tests/)
[![Security](https://img.shields.io/badge/Auth-JWT%20%2B%20HMAC--SHA256-blueviolet.svg)](app/core/security.py)

---

## 📌 Executive Summary

**LabLink** is an intelligent laboratory resource-sharing platform designed for multi-department university campuses (Electronics & Communication, Computer Science, Mechanical & Mechatronics, and Biotechnology). It bridges the gap between high-demand specialized hardware (such as Dual RTX 4090 workstations, Jetson AGX Orin kits, 4-GHz oscilloscopes, and qPCR systems) and student research teams.

The platform eliminates manual spreadsheet scheduling and equipment hoarding through:
1. **$O(1)$ Bitmask Slot Availability**: Date-partitioned 32-bit integers map 24 half-hour operating intervals (08:00–20:00).
2. **Multi-Factor Priority Scoring ($MFPS$)**: Non-random contention resolution arbitrating simultaneous requests via thesis deadline urgency, academic tiers, and anti-hoarding usage penalties.
3. **BookMyShow 10-Minute Leased Holds**: Atomic lock windows that automatically expire if unconfirmed, auto-promoting waitlisted students.
4. **Server-Side Anti-Spoofing & Role-Based Access Control**: Cryptographic JWT access tokens and constant-time HMAC-SHA256 signatures enforce strict student/faculty permissions (e.g. students cannot approve grants).
5. **Frugal GenAI Recommendation Engine**: Powered by `gemini-3.8-flash` via the modern `google-genai` SDK, caching responses in SQLite and steering students toward minimum-viable hardware to preserve campus budgets.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application Gateway                     │
│    (OWASP Hardened Headers · Strict CORS · JWT & Role Dependencies)   │
└───────────────┬───────────────────────────┬────────────────────────────┘
                │                           │
   ┌────────────▼────────────┐ ┌────────────▼────────────┐
   │    Hardware Registry    │ │    Bitmask Engine       │
   │  25 Real Campus Units   │ │ 32-bit Integer Slots    │
   │  ECE · CSE · MECH · BIO │ │ Date-Partitioned Masks  │
   └────────────┬────────────┘ └────────────┬────────────┘
                │                           │
   ┌────────────▼───────────────────────────▼────────────┐
   │            Persistent SQLite (WAL Mode)             │
   │  `equipment` · `date_slot_availability` · `bookings`│
   │  `project_proposals` · `student_profiles` · `cache` │
   └────────────┬───────────────────────────┬────────────┘
                │                           │
   ┌────────────▼────────────┐ ┌────────────▼────────────┐
   │   IRCTC / MFPS Arbiter  │ │   Unified GenAI Engine  │
   │ Multi-Factor Contention │ │ google-genai Client     │
   │ Leased Holds & Vikalp   │ │ SQLite Response Cache   │
   └─────────────────────────┘ └─────────────────────────┘
```

---

## ⚡ Core Mathematical & Algorithmic Foundations

### 1. Date-Partitioned $O(1)$ Slot Bitmask Engine

Campus laboratory hours (08:00 to 20:00) comprise 24 half-hour windows. Each day's reservation state is stored as a 32-bit integer (`uint32`) keyed by `(equipment_id, booking_date)`:

$$\text{Slot Index } s \in [0, 23], \quad \text{Mask}(s, d) = \left(2^d - 1\right) \ll s$$

- **Availability Verification**:
  $$\text{IsAvailable} = (\text{daily\_mask} \ \& \ \text{request\_mask}) == 0 \quad [O(1)]$$
- **Atomic Slot Reservation**:
  $$\text{daily\_mask}' = \text{daily\_mask} \ | \ \text{request\_mask} \quad [O(1)]$$
- **Atomic Slot Release / Expiration**:
  $$\text{daily\_mask}' = \text{daily\_mask} \ \& \ (\sim\text{request\_mask}) \quad [O(1)]$$
- **Capacity Utilization**:
  $$\text{Utilization} = \frac{\text{popcount}(\text{daily\_mask})}{24} \times 100\% \quad [O(1)]$$

Date partitioning ensures that booking an oscilloscope on Monday never locks out a student on Tuesday.

---

### 2. Multi-Factor Priority Scoring ($MFPS$)

When multiple students request the same hardware window simultaneously, the smart arbiter ranks contenders using server-verified profile data (preventing client-side urgency manipulation):

$$\text{MFPS} = 0.40 \cdot D(t) + 0.30 \cdot A + 0.20 \cdot F(u) + 0.10 \cdot S$$

| Component | Weight | Mathematical Formulation | Rationale |
| :--- | :---: | :--- | :--- |
| **$D(t)$ Deadline Urgency** | **40%** | $D(t) = \frac{1}{1 + (\Delta t / 24)^{0.65}}$ | Power-law decay: a 6h thesis defense yields $>0.82$, while distant deadlines yield $<0.25$. |
| **$A$ Academic Tier** | **30%** | Capstone/Thesis = $1.00$<br>Funded Research = $0.85$<br>Course Lab = $0.65$<br>Independent = $0.35$ | Prioritizes graduation-critical deliverables over unstructured exploration. |
| **$F(u)$ Anti-Hoarding Fairness** | **20%** | $F(u) = \exp(-0.065 \cdot u)$ | Exponential penalty on monthly equipment hours $u$, preventing compute monopoly. |
| **$S$ Safety Certification** | **10%** | Certified = $1.00$, Uncertified = $0.00$ | Ensures required lab certifications are completed prior to bench access. |

---

### 3. BookMyShow Leased Holds & IRCTC Vikalp Rerouting

1. **10-Minute Leased Hold (`HOLD_LEASE`)**: Winning requests receive a 10-minute hold with a timestamped cryptographic HMAC signature. If unconfirmed within 10 minutes, the hold expires automatically.
2. **IRCTC Waiting List (WL-1) Auto-Promotion**: An automated background sweep clears the expired bitmask bits and promotes the highest-scoring waiting-list contender.
3. **IRCTC Vikalp Alternative Rerouting**: Runners-up are proactively routed to the next available window on the same unit or an equivalent lower-cost kit.

---

## 🔒 Security & Data Integrity Architecture

- **Cryptographic JWT Tokens**: Role authorization (`/api/v1/auth/token`) dispenses signed tokens embedded with role claims (`student`, `faculty`, `admin`). Endpoints enforce strict checks (e.g. `require_role(["faculty", "admin"])` blocks unauthorized student approvals with HTTP 403 Forbidden).
- **Constant-Time HMAC-SHA256 Signatures**: Booking IDs, status transitions, and faculty decisions are signed using an HMAC secret (`verify_state_signature` via `hmac.compare_digest`), preventing client-side parameter tampering.
- **OWASP Hardened Headers**: Enforces strict `Content-Security-Policy` (disallowing `'unsafe-eval'`), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and restricted CORS policies.
- **Prompt Injection Defense**: Sanitizes input strings before GenAI processing, stripping control sequences, markdown injection tags, and common jailbreak phrases.

---

## 📡 REST API Reference

### Authentication & Identity
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/token?role={role}` | Dispenses cryptographic JWT access token for requested persona |
| `GET` | `/api/v1/auth/me` | Validates JWT claims and returns current user identity and permissions |

### Equipment Discovery
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/equipment` | Lists all 25 campus hardware kits with date-partitioned bitmask availability |
| `GET` | `/api/v1/equipment/{id}` | Real-time hardware specifications, safety prerequisites, and hourly rates |
| `POST` | `/api/v1/equipment/search/semantic` | GenAI semantic matching against natural language project descriptions |

### Slot Booking & Conflict Resolution
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/bookings/slots/{id}` | Retrieves 24 half-hour slot availability bitmask for a target date |
| `POST` | `/api/v1/bookings` | Atomic reservation under 10-minute BookMyShow leased hold |
| `POST` | `/api/v1/bookings/{id}/confirm` | Cryptographic HMAC confirmation of a leased hold |
| `DELETE`| `/api/v1/bookings/{id}` | Cancels reservation and atomically frees bitmask slots |
| `POST` | `/api/v1/conflicts/resolve` | Executes non-random $MFPS$ arbitration for simultaneous contenders |

### Project Proposals & Faculty Approvals
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/approvals/proposals` | Submits project access request with automated GenAI feasibility scoring |
| `GET` | `/api/v1/approvals` | Lists campus proposals (role-restricted to faculty/admin) |
| `POST` | `/api/v1/approvals/decision` | Faculty decision (`APPROVE` / `REJECT` / `REQUEST_REVISION`) with HMAC signature |

### Analytics & Health
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/analytics/utilization` | Capacity utilization, department load balancing, and popcounts |
| `GET` | `/healthz` | System diagnostics, SQLite WAL integrity, and GenAI engine status |

---

## 🧪 Automated Testing Suite

The repository includes **31 automated tests** covering all algorithm mechanics, API contracts, security boundaries, and persistence workflows:

```bash
# Run complete test suite
pytest -v
```

```
============================== test session starts ==============================
tests/test_api.py::test_root_endpoint PASSED                             [  3%]
tests/test_api.py::test_healthz_endpoint PASSED                          [  6%]
tests/test_api.py::test_auth_token_issuance PASSED                       [  9%]
tests/test_api.py::test_auth_me_claims PASSED                            [ 12%]
tests/test_bitmask_engine.py::test_slot_time_conversion PASSED           [ 16%]
tests/test_bitmask_engine.py::test_create_interval_mask PASSED           [ 19%]
tests/test_bitmask_engine.py::test_availability_and_atomic_reservation PASSED [ 22%]
tests/test_bitmask_engine.py::test_find_next_available_window PASSED     [ 25%]
tests/test_bitmask_engine.py::test_utilization_calculation PASSED        [ 29%]
tests/test_copilot.py::test_copilot_starter_prompts PASSED               [ 32%]
tests/test_copilot.py::test_copilot_frugal_minimum_viable_selection PASSED [ 35%]
tests/test_copilot.py::test_copilot_prompt_injection_safety PASSED       [ 38%]
tests/test_lablink_api.py::test_root_and_security_headers PASSED         [ 41%]
tests/test_lablink_api.py::test_equipment_listing_and_filtering PASSED   [ 45%]
tests/test_lablink_api.py::test_semantic_equipment_search PASSED         [ 48%]
tests/test_lablink_api.py::test_slot_booking_and_conflict PASSED         [ 51%]
tests/test_lablink_api.py::test_date_partitioned_bitmask_isolation PASSED [ 54%]
tests/test_lablink_api.py::test_hold_lease_auto_expiration PASSED        [ 58%]
tests/test_lablink_api.py::test_smart_conflict_resolution_and_persistence PASSED [ 61%]
tests/test_lablink_api.py::test_faculty_approvals_role_enforcement PASSED [ 64%]
tests/test_lablink_api.py::test_analytics_api PASSED                     [ 67%]
tests/test_lablink_api.py::test_faculty_rejection_workflow PASSED        [ 70%]
tests/test_lablink_api.py::test_booking_cryptographic_confirmation_workflow PASSED [ 74%]
tests/test_security_hardening.py::test_prompt_injection_sanitization PASSED [ 77%]
tests/test_security_hardening.py::test_hmac_state_signatures PASSED      [ 80%]
tests/test_security_hardening.py::test_sliding_window_rate_limiter PASSED [ 83%]
tests/test_security_hardening.py::test_jwt_token_claims_and_tampering PASSED [ 87%]
tests/test_smart_allocator.py::test_deadline_urgency_scoring PASSED      [ 90%]
tests/test_smart_allocator.py::test_anti_hoarding_fairness PASSED        [ 93%]
tests/test_smart_allocator.py::test_simultaneous_booking_contention_resolution PASSED [ 96%]
tests/test_smart_allocator.py::test_allocator_benchmark PASSED           [100%]
============================== 31 passed in 0.23s ==============================
```

---

## 🚀 Quickstart & Local Execution

### 1. Installation
```bash
# Clone repository
git clone https://github.com/ruchirruparelia2502-beep/promptwars-ai-backend.git
cd promptwars-ai-backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```
Key configuration parameters:
- `GEMINI_API_KEY`: Google Gemini API key (optional; system falls back gracefully to deterministic offline frugal heuristics if unset).
- `GEMINI_MODEL`: Defaults to `gemini-3.8-flash`.
- `HMAC_SECRET`: Key for constant-time HMAC state signatures.
- `JWT_SECRET`: Key for cryptographic role token encoding.

### 3. Running Development Server
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive Web Portal**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Specification**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📦 Deployment

### Vercel Serverless Deployment
The repository includes a root `vercel.json` configuring the FastAPI ASGI adapter via `api/index.py`:
- In serverless environments where local filesystem access may be ephemeral, SQLite automatically initializes in `/tmp/lablink.db` with WAL mode.
- Set `GEMINI_API_KEY`, `JWT_SECRET`, and `HMAC_SECRET` in the Vercel Project Environment Settings.

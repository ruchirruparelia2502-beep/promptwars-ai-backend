"""
Pytest Fixtures for LabLink Automated Test Suite
Ensures clean SQLite database isolation across test runs.
"""

import pytest
from app.core.database import db

@pytest.fixture(autouse=True)
def clean_database_tables():
    """Resets test bookings, slot availability, and proposals between tests."""
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM date_slot_availability;")
    cursor.execute("DELETE FROM bookings;")
    cursor.execute("DELETE FROM project_proposals;")
    cursor.execute("DELETE FROM waiting_list;")
    cursor.execute("DELETE FROM copilot_cache;")
    conn.commit()
    conn.close()
    db._seed_initial_data()
    yield
    # Re-seed after test run for live portal use
    db._seed_initial_data()

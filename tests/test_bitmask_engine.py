"""
Tests for High-Efficiency O(1) Bitmask Engine
"""

import pytest
from app.core.bitmask import (
    TOTAL_SLOTS,
    slot_index_to_time,
    time_to_slot_index,
    create_interval_mask,
    is_interval_available,
    apply_reservation,
    cancel_reservation,
    find_next_available_window,
    calculate_utilization_percentage,
    mask_to_slots,
    slots_to_mask
)


def test_slot_time_conversion():
    # Slot 0 is 08:00 - 08:30
    s_start, s_end = slot_index_to_time(0)
    assert s_start == "08:00"
    assert s_end == "08:30"

    # Slot 23 is 19:30 - 20:00
    last_start, last_end = slot_index_to_time(23)
    assert last_start == "19:30"
    assert last_end == "20:00"

    assert time_to_slot_index("08:00") == 0
    assert time_to_slot_index("09:30") == 3


def test_create_interval_mask():
    # Slots 2, 3, 4 -> bits 2, 3, 4 -> (1<<2) + (1<<3) + (1<<4) = 4 + 8 + 16 = 28
    mask = create_interval_mask(start_slot=2, duration_slots=3)
    assert mask == 28
    assert mask_to_slots(mask) == [2, 3, 4]


def test_availability_and_atomic_reservation():
    current_mask = 0b000000000000000000000011 # Slots 0 and 1 occupied

    # Slot 2 with duration 2 (bits 2, 3 = 12) is available
    req_mask = create_interval_mask(start_slot=2, duration_slots=2)
    assert is_interval_available(current_mask, req_mask) is True

    # Overlapping slot (e.g., slot 1 duration 2) should conflict
    conflict_mask = create_interval_mask(start_slot=1, duration_slots=2)
    assert is_interval_available(current_mask, conflict_mask) is False

    # Apply reservation in O(1)
    new_mask = apply_reservation(current_mask, req_mask)
    assert new_mask == 0b000000000000000000001111 # Bits 0, 1, 2, 3 set

    # Release reservation in O(1)
    freed_mask = cancel_reservation(new_mask, req_mask)
    assert freed_mask == current_mask


def test_find_next_available_window():
    # Occupy slots 0..9 (first 10 bits)
    mask = (1 << 10) - 1
    # Search for a 2-slot window starting from 0 -> should find slot 10
    next_win = find_next_available_window(mask, duration_slots=2, start_from=0)
    assert next_win == 10


def test_utilization_calculation():
    # 6 slots out of 24 = 25.0%
    mask = 0b111111
    util = calculate_utilization_percentage(mask)
    assert util == 25.0

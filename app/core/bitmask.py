"""
High-Efficiency O(1) Bitmask Slot Engine for LabLink
Encodes a daily laboratory schedule (08:00 to 20:00 = 24 half-hour slots)
into a compact 32-bit unsigned integer (uint32).

Time Complexities:
- Availability Check: O(1)
- Slot Reservation:   O(1)
- Slot Cancellation:  O(1)
- Next Free Window:   O(1)
Space Complexity: O(1) [Single 32-bit register per day per equipment]
"""

from typing import List, Tuple, Optional

# Constants
DAY_START_HOUR = 8       # 08:00 AM
DAY_END_HOUR = 20        # 08:00 PM
TOTAL_SLOTS = 24         # 24 x 30-min slots in a 12-hour operational window
FULL_DAY_MASK = (1 << TOTAL_SLOTS) - 1  # 0x00FFFFFF (24 ones)


def slot_index_to_time(slot_index: int) -> Tuple[str, str]:
    """
    Converts a slot index (0..23) to formatted start and end strings.
    Example: 0 -> ("08:00", "08:30"), 1 -> ("08:30", "09:00")
    Time Complexity: O(1)
    """
    if not (0 <= slot_index < TOTAL_SLOTS):
        raise ValueError(f"Slot index {slot_index} out of range [0, {TOTAL_SLOTS-1}]")

    start_minutes = DAY_START_HOUR * 60 + slot_index * 30
    end_minutes = start_minutes + 30

    start_str = f"{start_minutes // 60:02d}:{start_minutes % 60:02d}"
    end_str = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
    return start_str, end_str


def time_to_slot_index(time_str: str) -> int:
    """
    Parses "HH:MM" into the nearest starting slot index.
    Time Complexity: O(1)
    """
    parts = time_str.strip().split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0

    total_minutes = hour * 60 + minute
    start_minutes = DAY_START_HOUR * 60

    if total_minutes < start_minutes:
        return 0
    slot = (total_minutes - start_minutes) // 30
    return min(max(0, slot), TOTAL_SLOTS - 1)


def create_interval_mask(start_slot: int, duration_slots: int = 1) -> int:
    """
    Creates a contiguous bitmask for an interval [start_slot, start_slot + duration_slots - 1].
    Example: start_slot=2, duration=3 -> bits 2, 3, 4 set -> 0b00011100 (28)
    Time Complexity: O(1)
    """
    if duration_slots <= 0:
        return 0
    if start_slot < 0 or start_slot >= TOTAL_SLOTS:
        return 0

    valid_duration = min(duration_slots, TOTAL_SLOTS - start_slot)
    return ((1 << valid_duration) - 1) << start_slot


def is_interval_available(current_mask: int, request_mask: int) -> bool:
    """
    O(1) Bitwise intersection check.
    Returns True if NO bits overlap between current occupied mask and request mask.
    """
    return (current_mask & request_mask) == 0


def apply_reservation(current_mask: int, request_mask: int) -> int:
    """
    O(1) Atomic bitwise reservation (bitwise OR).
    """
    return current_mask | request_mask


def cancel_reservation(current_mask: int, request_mask: int) -> int:
    """
    O(1) Bitwise cancellation (bitwise AND with bitwise NOT).
    """
    return current_mask & ~request_mask


def find_next_available_window(current_mask: int, duration_slots: int = 1, start_from: int = 0) -> Optional[int]:
    """
    Finds the first available contiguous slot window of length `duration_slots`
    starting from `start_from`.
    Uses bitwise masks for ultra-fast lookup (at most 24 shifts).
    Time Complexity: O(1) [Bounded by 24 constant operations]
    """
    if duration_slots <= 0 or duration_slots > TOTAL_SLOTS:
        return None

    target_pattern = (1 << duration_slots) - 1
    max_start = TOTAL_SLOTS - duration_slots

    for candidate_slot in range(start_from, max_start + 1):
        window_mask = target_pattern << candidate_slot
        if (current_mask & window_mask) == 0:
            return candidate_slot
    return None


def mask_to_slots(mask: int) -> List[int]:
    """
    Extracts all set bit indices from a uint32 mask.
    Time Complexity: O(1) [Bounded by 24 bits]
    """
    slots = []
    for i in range(TOTAL_SLOTS):
        if (mask >> i) & 1:
            slots.append(i)
    return slots


def slots_to_mask(slots: List[int]) -> int:
    """
    Encodes a list of slot indices into a uint32 mask.
    Time Complexity: O(1)
    """
    mask = 0
    for s in slots:
        if 0 <= s < TOTAL_SLOTS:
            mask |= (1 << s)
    return mask


def calculate_utilization_percentage(mask: int) -> float:
    """
    Calculates equipment daily capacity utilization using bit count (popcount).
    Time Complexity: O(1)
    """
    occupied_count = bin(mask & FULL_DAY_MASK).count("1")
    return round((occupied_count / TOTAL_SLOTS) * 100.0, 1)

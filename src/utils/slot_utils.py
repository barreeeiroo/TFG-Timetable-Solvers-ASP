from datetime import timedelta
from typing import List, Optional, Tuple

from models.slot import Slot
from models.timeframe import Timeframe
from utils.time_utils import add_time


def generate_sub_slots(full_slot: Slot, slot_duration: timedelta) -> List[Slot]:
    timeframe = Timeframe(start=full_slot.timeframe.start, end=add_time(full_slot.timeframe.start, slot_duration))
    slots: List[Slot] = []
    while timeframe.end <= full_slot.timeframe.end:
        slots.append(Slot(
            week_day=full_slot.week_day,
            timeframe=timeframe,
            slot_type=full_slot.slot_type,
        ))
        timeframe = Timeframe(start=timeframe.end, end=add_time(timeframe.end, slot_duration))
    return slots


def generate_slot_groups(nums: List[int], manual_breaks: Optional[List[int]] = None) -> List[Tuple[int, int]]:
    nums = sorted(set(nums))
    gaps = [[s, e] for s, e in zip(nums, nums[1:]) if s + 1 < e]
    edges = iter(nums[:1] + sum(gaps, []) + nums[-1:])
    ranges = []
    for a, b in list(zip(edges, edges)):
        matching_breaks = [br for br in manual_breaks if a < br < b] if manual_breaks else []
        for matching_break in matching_breaks:
            ranges.append((a, matching_break,))
            a = matching_break + 1
        ranges.append((a, b,))
    return [(a, b, ) for a, b in ranges]

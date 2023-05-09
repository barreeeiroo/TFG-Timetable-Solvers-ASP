from datetime import timedelta
from typing import List

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


def generate_slot_groups(nums: List[int]) -> str:
    nums = sorted(set(nums))
    gaps = [[s, e] for s, e in zip(nums, nums[1:]) if s + 1 < e]
    edges = iter(nums[:1] + sum(gaps, []) + nums[-1:])
    ranges = list(zip(edges, edges))
    return ";".join([str(a) if a == b else f"{a}..{b}" for a, b in ranges])

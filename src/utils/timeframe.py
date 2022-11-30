from datetime import timedelta, datetime
from typing import Union, List

from pydantic import BaseModel


class Timeframe(BaseModel):
    start: datetime
    end: datetime


def generate_timeframe(start: str, end: str) -> Timeframe:
    date_start, date_end = datetime.strptime(start, "%H:%M"), datetime.strptime(end, "%H:%M")
    return Timeframe(start=date_start, end=date_end)


def generate_slots(start: str, end: str, slot_size: Union[str, timedelta]) -> List[Timeframe]:
    date_start, date_end = datetime.strptime(start, "%H:%M"), datetime.strptime(end, "%H:%M")

    full_slot = Timeframe(start=date_start, end=date_end)
    if isinstance(slot_size, timedelta):
        duration = slot_size
    else:
        duration = parse_slot_duration(slot_size)

    slot = Timeframe(start=date_start, end=full_slot.start + duration)
    slots: List[Timeframe] = []
    while slot.end <= full_slot.end:
        slots.append(slot)
        slot = Timeframe(start=slot.end, end=slot.end + duration)
    return slots


def parse_slot_duration(slot: str) -> timedelta:
    unit = slot[-1].lower()
    duration = int(slot[:-1])
    if unit == 'h':
        return timedelta(hours=duration)
    elif unit == 'm':
        return timedelta(minutes=duration)
    elif unit == 's':
        return timedelta(seconds=duration)
    raise NotImplementedError(f"Unit {unit} not supported")

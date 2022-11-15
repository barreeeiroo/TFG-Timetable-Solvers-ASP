from __future__ import annotations

from datetime import datetime, timedelta
from typing import Union, List


class Timeframe:
    def __init__(self, start: Union[str, datetime], end: Union[str, datetime]):
        self.start: datetime = Timeframe.__string_or_datetime_to_datetime(start)
        self.end: datetime = Timeframe.__string_or_datetime_to_datetime(end)
        assert self.start < self.end

    @staticmethod
    def __string_or_datetime_to_datetime(obj) -> datetime:
        if isinstance(obj, datetime):
            return obj
        return datetime.strptime(obj, "%H:%M")

    @staticmethod
    def generate_slots(start: str, end: str, slot_size: Union[str, timedelta]) -> List[Timeframe]:
        full_slot = Timeframe(start, end)
        if isinstance(slot_size, timedelta):
            duration = slot_size
        else:
            duration = Timeframe.parse_slot_duration(slot_size)

        slot = Timeframe(start, full_slot.start + duration)
        slots: List[Timeframe] = []
        while slot.end <= full_slot.end:
            slots.append(slot)
            slot = Timeframe(slot.end, slot.end + duration)
        return slots

    @staticmethod
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

    def __contains__(self, item):
        return not (item.end <= self.start or self.end <= item.start)

    def __repr__(self):
        return f"Timeframe({self.start.strftime('%H:%M')}-{self.end.strftime('%H:%M')})"

    def __eq__(self, other):
        return isinstance(other, Timeframe) and other.start == self.start and other.end == self.end

    def __hash__(self) -> int:
        return hash((self.start, self.end,))

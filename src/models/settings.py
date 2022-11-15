from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import timedelta
from enum import Enum
from typing import List, Dict

from models.course import SessionType
from utils.timeframe import Timeframe


class Settings:
    def __init__(self):
        self.week: Week = Week()
        self.preferred_slots_per_session_type: Dict[SessionType, Timeframe] = dict()


class SlotType(Enum):
    AVAILABLE = "available"
    UNDESIRABLE = "undesirable"
    BLOCKED = "blocked"

    @staticmethod
    def parse_from_string(slot_type: str) -> SlotType:
        slot_type = slot_type.lower()
        if slot_type == "available":
            return SlotType.AVAILABLE
        if slot_type == "undesirable":
            return SlotType.UNDESIRABLE
        if slot_type in ["blocked", "unavailable"]:
            return SlotType.BLOCKED
        raise NotImplementedError(f"Slot Type {slot_type} is not supported")


class Week:
    def __init__(self):
        self.__day_slot: Timeframe = Timeframe("08:00", "18:00")
        self.__slot_duration: timedelta = timedelta(hours=1)
        self.slots: Dict[int, Dict[Timeframe, SlotType]] = defaultdict(dict)

    def set_week_settings(self, days: List[int], start: str, end: str, slot_size: str):
        self.__day_slot = Timeframe(start, end)
        self.__slot_duration = Timeframe.parse_slot_duration(slot_size)

        slots = Timeframe.generate_slots(start, end, self.__slot_duration)
        for day in days:
            self.slots[day] = {slot: SlotType.AVAILABLE for slot in slots}

    def modify_slot(self, day: str, start: str, end: str, slot_type: str):
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        calendar_day = days.index(day.lower())
        slots = Timeframe.generate_slots(start, end, self.__slot_duration)
        for slot in slots:
            self.slots[calendar_day][slot] = SlotType.parse_from_string(slot_type)

    def get_slots_per_day_count(self) -> int:
        return int((self.__day_slot.end - self.__day_slot.start) / self.__slot_duration)

    def get_slots_count_for_timedelta(self, td: timedelta) -> int:
        return int(td / self.__slot_duration)

    def get_total_slot_count(self) -> int:
        return sum(map(len, self.slots.values()))

    def print_available_slots(self):
        self.__print_slots()

    def print_undesirable_slots(self):
        self.__print_slots(undesirable=True)

    def __print_slots(self, undesirable: bool = False):
        for day, day_slots in self.slots.items():
            for slot, slot_type in day_slots.items():
                if slot_type == SlotType.BLOCKED:
                    continue
                if undesirable and slot_type != SlotType.UNDESIRABLE:
                    continue
                print(f"{calendar.day_name[day]}: {slot}")

    def __repr__(self):
        return f"Week({self.get_total_slot_count()})"

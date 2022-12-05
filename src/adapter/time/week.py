import calendar
from collections import defaultdict
from datetime import timedelta
from typing import Dict, List

from models.settings import Settings
from models.slot import Slot, SlotType
from models.timeframe import Timeframe
from utils.slot_utils import generate_sub_slots
from utils.time_utils import time_to_datetime


class Week:
    def __init__(self, settings: Settings):
        self.__day_timeframe: Timeframe = Timeframe(start=settings.day_start, end=settings.day_end)
        self.__slot_duration: timedelta = settings.slot_duration

        self.slots: Dict[int, List[Slot]] = defaultdict(list)
        for day in settings.week_days:
            day_slot = Slot(
                week_day=day,
                timeframe=self.__day_timeframe,
                status=SlotType.AVAILABLE,
            )
            self.slots[day] = generate_sub_slots(day_slot, self.__slot_duration)

        for slot in settings.modified_slots:
            self.__update_slot_type(slot)

    def __update_slot_type(self, full_slot: Slot):
        slots_to_update = generate_sub_slots(full_slot, self.__slot_duration)
        original_slots = self.slots[full_slot.week_day]
        for slot in slots_to_update:
            current_index = original_slots.index(slot)
            original_slots[current_index] = slot

    def get_slots_per_day_count(self) -> int:
        delta = time_to_datetime(self.__day_timeframe.end) - time_to_datetime(self.__day_timeframe.start)
        return int(delta / self.__slot_duration)

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
            for slot in day_slots:
                if slot.slot_type == SlotType.BLOCKED:
                    continue
                if undesirable and slot.slot_type != SlotType.UNDESIRABLE:
                    continue
                print(f"{calendar.day_name[day]}: {slot}")

    def __repr__(self):
        return f"Week({self.get_total_slot_count()})"

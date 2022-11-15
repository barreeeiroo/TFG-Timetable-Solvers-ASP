from typing import List

from models.course import Course
from models.room import Room
from models.settings import Settings, SlotType
from solvers.asp.constants import ClingoConstants as ClC, ClingoNaming as ClN


class Constraints:
    @staticmethod
    def get_room_already_booked() -> str:
        assigned_slot_one = ClC.assigned_slot(timeslot=ClC.TIMESLOT, unit=f'{ClC.UNIT}1', room=ClC.ROOM)
        assigned_slot_two = ClC.assigned_slot(timeslot=ClC.TIMESLOT, unit=f'{ClC.UNIT}2', room=ClC.ROOM)
        condition = f"{ClC.UNIT}1 != {ClC.UNIT}2"
        return f":- {assigned_slot_one}, {assigned_slot_two}, {condition}."

    @staticmethod
    def get_unit_in_same_room() -> str:
        assigned_slot_one = ClC.assigned_slot(unit=ClC.UNIT, room=f'{ClC.ROOM}1')
        assigned_slot_two = ClC.assigned_slot(unit=ClC.UNIT, room=f'{ClC.ROOM}2')
        condition = f"{ClC.ROOM}1 != {ClC.ROOM}2"
        return f":- {assigned_slot_one}, {assigned_slot_two}, {condition}."


class Statements:
    def __init__(self, settings: Settings, courses: List[Course], rooms: List[Room]):
        self.__settings = settings
        self.__courses = courses
        self.__rooms = rooms

    def generate_constraints(self) -> List[str]:
        assert self.__settings
        return [
            Constraints.get_room_already_booked(),
            Constraints.get_unit_in_same_room(),
        ]

    def generate_timeslots(self) -> str:
        return f"{ClC.timeslot(f'1..{self.__settings.week.get_total_slot_count()}')}."

    def generate_rooms(self) -> List[str]:
        return [f"{ClC.room(ClN.room_to_clingo(room))}." for room in self.__rooms]

    def __get_slot_ids_per_type(self, desired_slot_type: SlotType) -> List[int]:
        slot_ids: List[int] = []
        for week_day, slots in self.__settings.week.slots.items():
            offset = week_day * self.__settings.week.get_slots_per_day_count()
            for slot_id, (slot, slot_type) in enumerate(slots.items()):
                if slot_type == desired_slot_type:
                    slot_ids.append(offset + slot_id)
        return slot_ids

    def generate_undesirable_slots(self, penalty_amount: int = 10) -> List[str]:
        statements = []
        assigned_slot = ClC.assigned_slot(timeslot=ClC.TIMESLOT)
        for blocked_slot in self.__get_slot_ids_per_type(SlotType.UNDESIRABLE):
            penalty = f"{ClC.TIMESLOT}=={blocked_slot}.[{penalty_amount},{ClC.TIMESLOT}]"
            statements.append(f":~ {assigned_slot}, {penalty}")
        return statements

    def generate_blocked_slots(self) -> List[str]:
        blocked_slots: List[int] = self.__get_slot_ids_per_type(SlotType.BLOCKED)
        if not blocked_slots:
            return []

        statements = []
        for blocked_slot in blocked_slots:
            stmt = f"{ClC.BLOCKED_SLOT} :- {ClC.assigned_slot(timeslot=str(blocked_slot))}."
            statements.append(stmt)
        statements.append(f":- {ClC.BLOCKED_SLOT}.")
        return statements

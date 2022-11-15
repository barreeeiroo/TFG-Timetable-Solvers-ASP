from typing import List

from models.course import Course
from models.room import Room
from models.settings import Settings, SlotType
from solvers.asp.constants import ClingoConstants as ClC, ClingoNaming as ClN


class Constraints:
    ROOM_ALREADY_BOOKED = ":- roomBooked(T,U1,R), roomBooked(T,U2,R), U1 != U2."
    SESSION_IN_SAME_ROOM = ":- roomBooked(_,U,R1), roomBooked(_,U,R2), R1 != R2."


class Statements:
    def __init__(self, settings: Settings, courses: List[Course], rooms: List[Room]):
        self.__settings = settings
        self.__courses = courses
        self.__rooms = rooms

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

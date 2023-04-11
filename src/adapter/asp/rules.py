from typing import List

from adapter.asp.constants import ClingoConstants as ClC, ClingoNaming as ClN
from adapter.time.week import Week
from models.dto.input import Room, Session
from models.slot import SlotType


class Constraints:
    @staticmethod
    def get_room_already_booked() -> str:
        assigned_slot_one = ClC.assigned_slot(ClC.TIMESLOT, f'{ClC.SESSION}1', ClC.ANY, ClC.ROOM)
        assigned_slot_two = ClC.assigned_slot(ClC.TIMESLOT, f'{ClC.SESSION}2', ClC.ANY, ClC.ROOM)
        condition = f"{ClC.SESSION}1 != {ClC.SESSION}2"
        return f":- {assigned_slot_one}, {assigned_slot_two}, {condition}."

    @staticmethod
    def get_unit_in_same_room() -> str:
        assigned_slot_one = ClC.assigned_slot(ClC.ANY, ClC.SESSION, ClC.SESSION_TYPE, f'{ClC.ROOM}1')
        assigned_slot_two = ClC.assigned_slot(ClC.ANY, ClC.SESSION, ClC.SESSION_TYPE, f'{ClC.ROOM}2')
        condition = f"{ClC.ROOM}1 != {ClC.ROOM}2"
        return f":- {assigned_slot_one}, {assigned_slot_two}, {condition}."

    @staticmethod
    def get_unit_in_same_timeslot_with_same_session_type() -> str:
        assigned_slot_one = ClC.assigned_slot(ClC.TIMESLOT, ClC.SESSION, f"{ClC.SESSION_TYPE}1", ClC.ANY)
        assigned_slot_two = ClC.assigned_slot(ClC.TIMESLOT, ClC.SESSION, f"{ClC.SESSION_TYPE}2", ClC.ANY)
        condition = f"{ClC.SESSION_TYPE}1 != {ClC.SESSION_TYPE}2"
        return f":- {assigned_slot_one}, {assigned_slot_two}, {condition}."


class Statements:
    def __init__(self, week: Week, sessions: List[Session], rooms: List[Room]):
        self.__week = week
        self.__sessions = sessions
        self.__rooms = rooms

    def generate_scheduled_units_store(self):
        assert self
        # Store scheduled units
        assigned_slot = ClC.assigned_slot(ClC.TIMESLOT, ClC.SESSION, ClC.SESSION_TYPE, ClC.ROOM)
        timeslot = ClC.timeslot(ClC.TIMESLOT)
        room = ClC.room(ClC.ROOM, ClC.ANY, ClC.ANY)
        session = ClC.session(ClC.SESSION, ClC.SESSION_TYPE, ClC.SESSION_DURATION)

        head = f"{ClC.SESSION_DURATION} {{ {assigned_slot} : {timeslot} , {room} }} {ClC.SESSION_DURATION}"
        return f"{head} :- {session}."

    def generate_scheduled_room_type_with_session_type_store(self):
        assert self
        # Store scheduled units
        used_room = ClC.used_room(ClC.TIMESLOT, ClC.ROOM, ClC.ROOM_TYPE, ClC.SESSION_TYPE)
        room = ClC.room(ClC.ROOM, ClC.ROOM_TYPE, ClC.ANY)
        session = ClC.session(ClC.SESSION, ClC.SESSION_TYPE, ClC.ANY)
        assigned_slot = ClC.assigned_slot(ClC.TIMESLOT, ClC.SESSION, ClC.SESSION_TYPE, ClC.ROOM)

        head = f"1 {{ {used_room} : {room} , {session} }} 1"
        return f"{head} :- {assigned_slot}."

    def generate_constraints(self) -> List[str]:
        assert self
        return [
            Constraints.get_room_already_booked(),
            Constraints.get_unit_in_same_room(),
            Constraints.get_unit_in_same_timeslot_with_same_session_type(),
        ]

    def generate_penalized_room_types(self, penality_amount: int = 45) -> str:
        assert self
        used_room = ClC.used_room(ClC.TIMESLOT, ClC.ROOM, ClC.ROOM_TYPE, ClC.SESSION_TYPE)
        condition = f"{ClC.ROOM_TYPE}!={ClC.SESSION_TYPE}"
        return f":~ {used_room}, {condition}.[{penality_amount},{ClC.TIMESLOT}]"

    def __get_slot_ids_per_type(self, desired_slot_type: SlotType) -> List[int]:
        slot_ids: List[int] = []
        for week_day, slots in self.__week.slots.items():
            offset = week_day * self.__week.get_slots_per_day_count()
            for slot_id, slot in enumerate(slots):
                if slot.slot_type == desired_slot_type:
                    slot_ids.append(offset + slot_id)
        return slot_ids

    def generate_undesirable_slots(self, penalty_amount: int = 10) -> List[str]:
        statements = []
        assigned_slot = ClC.assigned_slot(ClC.TIMESLOT, ClC.ANY, ClC.ANY, ClC.ANY)
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
            stmt = f"{ClC.BLOCKED_SLOT} :- {ClC.assigned_slot(str(blocked_slot), ClC.ANY, ClC.ANY, ClC.ANY)}."
            statements.append(stmt)
        statements.append(f":- {ClC.BLOCKED_SLOT}.")
        return statements

    def generate_timeslots(self) -> str:
        return f"{ClC.timeslot(f'1..{self.__week.get_total_slot_count()}')}."

    def generate_rooms(self) -> List[str]:
        statements: List[str] = []
        for room in self.__rooms:
            for session_type in room.constraints.session_types:
                clingo_room = ClC.room(
                    ClN.room_to_clingo(room), ClN.session_type_to_clingo(session_type),
                    room.constraints.capacity
                )
                statements.append(f"{clingo_room}.")
        return statements

    def generate_sessions(self) -> List[str]:
        statements: List[str] = []
        for session in self.__sessions:
            clingo_session = ClC.session(
                ClN.session_to_clingo(session), session.constraints.session_type,
                self.__week.get_slots_count_for_timedelta(session.constraints.duration)
            )
            statements.append(f"{clingo_session}.")
        return statements

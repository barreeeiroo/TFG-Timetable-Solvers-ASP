from typing import Union
from uuid import UUID

from models.room import Room
from models.session import Session


class ClingoVariables:
    ANY = "_"

    TIMESLOT = "T"
    CONTIGUOUS_TIMESLOT = "CT"
    SESSION = "S"
    SESSION_TYPE = "ST"
    SESSION_DURATION = "H"
    ROOM = "R"
    ROOM_TYPE = "RT"
    ROOM_CAPACITY = "RC"

    PENALTY_NAME = "PN"
    PENALTY_COST = "PC"
    PENALTY_VALUE = "PV"
    PENALTY_PRIORITY = "PP"
    BONUS_NAME = "BN"
    BONUS_COST = "BC"
    BONUS_VALUE = "BV"
    BONUS_PRIORITY = "BP"


class ClingoPredicates:
    TIMESLOT = "timeslot"
    CONTIGUOUS_TIMESLOT = "ct"
    ROOM = "room"
    ROOM_TYPE = "roomType"
    SESSION = "session"

    ASSIGNED_SLOT = "assignedSlot"
    SCHEDULED_SESSION = "scheduledSession"
    SCHEDULED_SESSION_CHAIN = "scheduledSessionChain"
    NO_TIMESLOT_OVERLAP_IN_SESSIONS = "noTimeslotOverlapInSessions"
    AVOID_TIMESLOT_OVERLAP_IN_SESSIONS = "avoidTimeslotOverlapInSessions"
    BREAK_SESSION_TIMESLOT = "breakSessionTimeslot"
    USED_ROOM = "usedRoom"
    BLOCKED_TIMESLOT = "blockedTimeslot"
    UNDESIRABLE_TIMESLOT = "undesirableTimeslot"
    DISALLOWED_ROOM_FOR_SESSION = "disallowedRoomForSession"
    PREFERRED_ROOM_FOR_SESSION = "preferredRoomForSession"
    PENALIZED_ROOM_FOR_SESSION = "penalizedRoomForSession"
    DISALLOWED_TIMESLOT_FOR_SESSION = "disallowedTimeslotForSession"
    PREFERRED_TIMESLOT_FOR_SESSION = "preferredTimeslotForSession"
    PENALIZED_TIMESLOT_FOR_SESSION = "penalizedTimeslotForSession"

    PENALTY = "penalty"
    BONUS = "bonus"

    @staticmethod
    def scheduled_session(timeslot: Union[int, str], session: str) -> str:
        return f"{ClingoPredicates.SCHEDULED_SESSION}({timeslot},{session})"

    @staticmethod
    def scheduled_session_chain(session: str, timeslot: str, contiguous_timeslot: Union[int, str]) -> str:
        return f"{ClingoPredicates.SCHEDULED_SESSION_CHAIN}({session},{timeslot},{contiguous_timeslot})"

    @staticmethod
    def assigned_slot(timeslot: Union[str, int], session: str, room: str) -> str:
        return f"{ClingoPredicates.ASSIGNED_SLOT}({timeslot},{session},{room})"

    @staticmethod
    def no_timeslot_overlap_in_sessions(session1: str, session2: str) -> str:
        return f"{ClingoPredicates.NO_TIMESLOT_OVERLAP_IN_SESSIONS}({session1},{session2})"

    @staticmethod
    def avoid_timeslot_overlap_in_sessions(session1: str, session2: str) -> str:
        return f"{ClingoPredicates.AVOID_TIMESLOT_OVERLAP_IN_SESSIONS}({session1},{session2})"

    @staticmethod
    def break_session_timeslot(timeslot1: Union[int, str], timeslot2: Union[int, str]):
        return f"{ClingoPredicates.BREAK_SESSION_TIMESLOT}({timeslot1},{timeslot2})"

    @staticmethod
    def timeslot(timeslot: str) -> str:
        return f"{ClingoPredicates.TIMESLOT}({timeslot})"

    @staticmethod
    def room(room: str, room_capacity: int) -> str:
        return f"{ClingoPredicates.ROOM}({room},{room_capacity})"

    @staticmethod
    def room_type(room: str, room_type: str) -> str:
        return f"{ClingoPredicates.ROOM_TYPE}({room},{room_type})"

    @staticmethod
    def session(session: str, session_type: str, session_duration: int):
        return f"{ClingoPredicates.SESSION}({session},{session_type},{session_duration})"

    @staticmethod
    def contiguous_timeslot(ct: Union[int, str]):
        return f"{ClingoPredicates.CONTIGUOUS_TIMESLOT}({ct})"

    @staticmethod
    def blocked_timeslot(timeslot: Union[str, int]):
        return f"{ClingoPredicates.BLOCKED_TIMESLOT}({timeslot})"

    @staticmethod
    def undesirable_timeslot(timeslot: Union[str, int], penalty: Union[str, int]):
        return f"{ClingoPredicates.UNDESIRABLE_TIMESLOT}({timeslot},{penalty})"

    @staticmethod
    def disallowed_room_for_session(session: str, room: str):
        return f"{ClingoPredicates.DISALLOWED_ROOM_FOR_SESSION}({session},{room})"

    @staticmethod
    def penalized_room_for_session(session: str, room: str):
        return f"{ClingoPredicates.PENALIZED_ROOM_FOR_SESSION}({session},{room})"

    @staticmethod
    def preferred_room_for_session(session: str, room: str):
        return f"{ClingoPredicates.PREFERRED_ROOM_FOR_SESSION}({session},{room})"

    @staticmethod
    def disallowed_timeslot_for_session(session: str, timeslot: Union[str, int]):
        return f"{ClingoPredicates.DISALLOWED_TIMESLOT_FOR_SESSION}({session},{timeslot})"

    @staticmethod
    def penalized_timeslot_for_session(session: str, timeslot: Union[str, int]):
        return f"{ClingoPredicates.PENALIZED_TIMESLOT_FOR_SESSION}({session},{timeslot})"

    @staticmethod
    def preferred_timeslot_for_session(session: str, timeslot: Union[str, int]):
        return f"{ClingoPredicates.PREFERRED_TIMESLOT_FOR_SESSION}({session},{timeslot})"

    @staticmethod
    def penalty(name: str, cost: Union[str, int], value: Union[str, int], priority: Union[str, int]):
        return f"{ClingoPredicates.PENALTY}({name},{cost},{value},{priority})"

    @staticmethod
    def bonus(name: str, cost: Union[str, int], value: Union[str, int], priority: Union[str, int]):
        return f"{ClingoPredicates.BONUS}({name},{cost},{value},{priority})"


class ClingoNaming:
    ROOM = "room"
    SESSION = "session"
    SESSION_TYPE = "st"

    @staticmethod
    def room_to_clingo(room: Union[Room, UUID]) -> str:
        if isinstance(room, UUID):
            return f"{ClingoNaming.ROOM}_{room.hex}"
        return f"{ClingoNaming.ROOM}_{room.id.hex}"

    @staticmethod
    def session_to_clingo(session: Union[Session, UUID]) -> str:
        if isinstance(session, UUID):
            return f"{ClingoNaming.SESSION}_{session.hex}"
        return f"{ClingoNaming.SESSION}_{session.id.hex}"

    @staticmethod
    def session_type_to_clingo(session_type: str) -> str:
        return f"{ClingoNaming.SESSION_TYPE}_{session_type}"

    @staticmethod
    def get_id_from_clingo(clingo: str) -> str:
        _, data = clingo.split("_")
        return data

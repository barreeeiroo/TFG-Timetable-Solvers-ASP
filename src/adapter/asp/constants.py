from typing import Union
from uuid import UUID

from models.room import Room
from models.session import Session


class ClingoVariables:
    ANY = "_"

    TIMESLOT = "T"
    SESSION = "S"
    SESSION_TYPE = "ST"
    SESSION_DURATION = "H"
    ROOM = "R"
    ROOM_TYPE = "RT"
    ROOM_CAPACITY = "RC"


class ClingoPredicates:
    TIMESLOT = "timeslot"
    ROOM = "room"
    ROOM_TYPE = "roomType"
    SESSION = "session"

    ASSIGNED_SLOT = "assignedSlot"
    SCHEDULED_SESSION = "scheduledSession"
    NO_TIMESLOT_OVERLAP_IN_SESSIONS = "noTimeslotOverlapInSessions"
    USED_ROOM = "usedRoom"
    BLOCKED_SLOT = "blockedSlot"
    UNDESIRABLE_SLOT = "undesirableSlot"

    @staticmethod
    def scheduled_session(timeslot: str, session: str) -> str:
        return f"{ClingoPredicates.SCHEDULED_SESSION}({timeslot},{session})"

    @staticmethod
    def assigned_slot(timeslot: str, session: str, room: str) -> str:
        return f"{ClingoPredicates.ASSIGNED_SLOT}({timeslot},{session},{room})"

    @staticmethod
    def no_timeslot_overlap_in_sessions(session1: str, session2: str) -> str:
        return f"{ClingoPredicates.NO_TIMESLOT_OVERLAP_IN_SESSIONS}({session1},{session2})"

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


class ClingoNaming:
    ROOM = "room"
    SESSION = "session"
    SESSION_TYPE = "st"

    @staticmethod
    def room_to_clingo(room: Room) -> str:
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

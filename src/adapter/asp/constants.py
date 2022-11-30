from __future__ import annotations

from models.dto.input import Room, Session


class ClingoConstants:
    ANY = "_"

    TIMESLOT = "T"
    SESSION = "S"
    SESSION_TYPE = "ST"
    SESSION_DURATION = "H"
    ROOM = "R"
    ROOM_TYPE = "RT"
    ROOM_CAPACITY = "RC"

    ASSIGNED_SLOT = "assignedSlot"
    USED_ROOM = "usedRoom"
    BLOCKED_SLOT = "blockedSlot"
    UNDESIRABLE_SLOT = "undesirableSlot"

    @staticmethod
    def assigned_slot(timeslot: str, unit: str, session_type: str, room: str) -> str:
        return f"{ClingoConstants.ASSIGNED_SLOT}({timeslot},{unit},{session_type},{room})"

    @staticmethod
    def used_room(timeslot: str, room: str, room_type: str, session_type: str) -> str:
        return f"{ClingoConstants.USED_ROOM}({timeslot},{room},{room_type},{session_type})"

    @staticmethod
    def timeslot(timeslot: str) -> str:
        return f"timeslot({timeslot})"

    @staticmethod
    def room(room: str, room_type: str, room_capacity: int) -> str:
        return f"room({room},{room_type},{room_capacity})"

    @staticmethod
    def session(session: str, session_type: str, session_duration: int):
        return f"session({session},{session_type},{session_duration})"


class ClingoNaming:
    @staticmethod
    def room_to_clingo(room: Room) -> str:
        return f"room_{room.id.hex}"

    @staticmethod
    def session_to_clingo(session: Session) -> str:
        return f"session_{session.id.hex}"

    @staticmethod
    def session_type_to_clingo(session_type: str) -> str:
        return f"st_{session_type}"

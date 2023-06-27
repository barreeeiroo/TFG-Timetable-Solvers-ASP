from typing import Union
from uuid import UUID

from models.room import Room
from models.session import Session
from models.slot import Slot
from models.timeframe import Timeframe


class ClingoVariables:
    ANY = "_"

    TIMESLOT = "T"
    SESSION = "S"
    SESSION_DURATION = "H"
    ROOM = "R"
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
    ROOM = "room"
    SESSION = "session"

    ROOM_DISTANCE = "roomDistance"

    SCHEDULED_SESSION = "scheduledSession"
    ASSIGNED_TIMESLOT = "assignedTimeslot"
    ASSIGNED_ROOM = "assignedRoom"

    ELIGIBLE_ROOM_FOR_SESSION = "eligibleRoomForSession"
    ELIGIBLE_TIMESLOT_FOR_SESSION = "eligibleTimeslotForSession"

    NO_TIMESLOT_OVERLAP_IN_SESSIONS = "noTimeslotOverlapInSessions"
    AVOID_TIMESLOT_OVERLAP_IN_SESSIONS = "avoidTimeslotOverlapInSessions"
    UNDESIRABLE_TIMESLOT = "undesirableTimeslot"
    PREFERRED_ROOM_FOR_SESSION = "preferredRoomForSession"
    PENALIZED_ROOM_FOR_SESSION = "penalizedRoomForSession"
    PREFERRED_TIMESLOT_FOR_SESSION = "preferredTimeslotForSession"
    PENALIZED_TIMESLOT_FOR_SESSION = "penalizedTimeslotForSession"
    SAME_ROOM_IF_CONTIGUOUS_SESSIONS = "sameRoomIfContiguousSessions"
    APPLY_ROOM_DISTANCES_TO_SESSIONS = "applyRoomDistancesToSessions"

    PENALTY = "penalty"
    BONUS = "bonus"

    @staticmethod
    def timeslot(timeslot: str) -> str:
        return f"{ClingoPredicates.TIMESLOT}({timeslot})"

    @staticmethod
    def room(room: str, room_capacity: int) -> str:
        return f"{ClingoPredicates.ROOM}({room},{room_capacity})"

    @staticmethod
    def session(session: str, session_duration: Union[str, int]):
        return f"{ClingoPredicates.SESSION}({session},{session_duration})"

    @staticmethod
    def room_distance(room1: str, room2: str, distance: Union[str, int]):
        # Note that distance is in number of timeslots
        return f"{ClingoPredicates.ROOM_DISTANCE}({room1},{room2},{distance})"

    @staticmethod
    def scheduled_session(timeslot: Union[int, str], session: str, room: str) -> str:
        return f"{ClingoPredicates.SCHEDULED_SESSION}({timeslot},{session},{room})"

    @staticmethod
    def assigned_timeslot(timeslot: Union[str, int], session: str) -> str:
        return f"{ClingoPredicates.ASSIGNED_TIMESLOT}({timeslot},{session})"

    @staticmethod
    def assigned_room(room: str, session: str) -> str:
        return f"{ClingoPredicates.ASSIGNED_ROOM}({room},{session})"

    @staticmethod
    def eligible_room_for_session(session: str, room: str):
        return f"{ClingoPredicates.ELIGIBLE_ROOM_FOR_SESSION}({session},{room})"

    @staticmethod
    def eligible_timeslot_for_session(session: str, timeslot: Union[str, int]):
        return f"{ClingoPredicates.ELIGIBLE_TIMESLOT_FOR_SESSION}({session},{timeslot})"

    @staticmethod
    def no_timeslot_overlap_in_sessions(session1: str, session2: str) -> str:
        return f"{ClingoPredicates.NO_TIMESLOT_OVERLAP_IN_SESSIONS}({session1},{session2})"

    @staticmethod
    def avoid_timeslot_overlap_in_sessions(session1: str, session2: str) -> str:
        return f"{ClingoPredicates.AVOID_TIMESLOT_OVERLAP_IN_SESSIONS}({session1},{session2})"

    @staticmethod
    def undesirable_timeslot(timeslot: Union[str, int], penalty: Union[str, int]):
        return f"{ClingoPredicates.UNDESIRABLE_TIMESLOT}({timeslot},{penalty})"

    @staticmethod
    def penalized_room_for_session(session: str, room: str):
        return f"{ClingoPredicates.PENALIZED_ROOM_FOR_SESSION}({session},{room})"

    @staticmethod
    def preferred_room_for_session(session: str, room: str):
        return f"{ClingoPredicates.PREFERRED_ROOM_FOR_SESSION}({session},{room})"

    @staticmethod
    def penalized_timeslot_for_session(session: str, timeslot: Union[str, int]):
        return f"{ClingoPredicates.PENALIZED_TIMESLOT_FOR_SESSION}({session},{timeslot})"

    @staticmethod
    def preferred_timeslot_for_session(session: str, timeslot: Union[str, int]):
        return f"{ClingoPredicates.PREFERRED_TIMESLOT_FOR_SESSION}({session},{timeslot})"

    @staticmethod
    def same_room_if_contiguous_sessions(session1: str, session2: str):
        return f"{ClingoPredicates.SAME_ROOM_IF_CONTIGUOUS_SESSIONS}({session1},{session2})"

    @staticmethod
    def apply_room_distances_to_sessions(session1: str, session2: str):
        return f"{ClingoPredicates.APPLY_ROOM_DISTANCES_TO_SESSIONS}({session1},{session2})"

    @staticmethod
    def penalty(name: str, cost: Union[str, int], value: Union[str, int], priority: Union[str, int]):
        return f"{ClingoPredicates.PENALTY}({name},{cost},{value},{priority})"

    @staticmethod
    def bonus(name: str, cost: Union[str, int], value: Union[str, int], priority: Union[str, int]):
        return f"{ClingoPredicates.BONUS}({name},{cost},{value},{priority})"


class ClingoNaming:
    ROOM = "room"
    SESSION = "session"

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
    def get_id_from_clingo(clingo: str) -> str:
        _, data = clingo.split("_")
        return data

    @staticmethod
    def get_timeslot_for_comment(slot: Slot):
        days = [
            "MON",
            "TUE",
            "WED",
            "THU",
            "FRI",
            "SAT",
            "SUN",
        ]
        day = days[(slot.week_day - 1) % 7]
        return f"{day} @ {slot.timeframe.start} - {slot.timeframe.end}"

    @staticmethod
    def get_timeslot_range_for_comment(a: Slot, b: Slot):
        return ClingoNaming.get_timeslot_for_comment(Slot(
            week_day=a.week_day,
            timeframe=Timeframe(
                start=min(a.timeframe.start, b.timeframe.start),
                end=max(a.timeframe.start, b.timeframe.start),
            ),
        ))

    @staticmethod
    def get_room_for_comment(room: Room):
        if not isinstance(room.metadata, dict):
            return ""

        if "room" not in room.metadata:
            return ""
        comment = room.metadata['room']
        if "building" in room.metadata:
            comment = f"{room.metadata['room']} | {room.metadata['building']}"
        return f" % {comment}"

    @staticmethod
    def get_session_for_comment(session: Session, simple: bool = False):
        if not isinstance(session.metadata, dict):
            return ""

        data = [session.constraints.session_type]
        if "course" in session.metadata:
            course = session.metadata['course']
            if simple:
                return course
            data.append(course)
        if "sessionGroup" in session.metadata:
            data.append(session.metadata['sessionGroup'])
        if "nGroup" in session.metadata and "nWeek" in session.metadata:
            data.append(f"{session.metadata['nGroup'] + 1}-{session.metadata['nWeek'] + 1}")

        return ' | '.join(data)

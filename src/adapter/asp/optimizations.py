from enum import Enum


class OptimizationPriorities(int, Enum):
    PENALTY__UNDESIRABLE_TIMESLOT_5 = 6
    PENALTY__UNDESIRABLE_TIMESLOT_2 = 5
    PENALTY__UNDESIRABLE_TIMESLOT_1 = 4
    PENALTY__AVOID_ROOM_FOR_SESSION = 3
    PENALTY__AVOID_SESSION_OVERLAP = 2

    BONUS__PREFER_ROOM_FOR_SESSION = 1


class PenaltyNames(str, Enum):
    UNDESIRABLE_TIMESLOT = '"UndesirableTimeslot"'
    AVOID_ROOM_FOR_SESSION = '"AvoidRoomForDegree"'
    AVOID_SESSION_OVERLAP = '"AvoidSessionOverlap"'


class PenaltyCosts(int, Enum):
    UNDESIRABLE_TIMESLOT_1 = 10
    UNDESIRABLE_TIMESLOT_2 = 20
    UNDESIRABLE_TIMESLOT_5 = 50
    AVOID_ROOM_FOR_SESSION = 15
    AVOID_SESSION_OVERLAP = 15


class BonusNames(str, Enum):
    PREFER_ROOM_FOR_SESSION = '"PreferRoomForSession"'


class BonusCosts(int, Enum):
    PREFER_ROOM_FOR_SESSION = 15

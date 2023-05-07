from enum import Enum


class OptimizationPriorities(int, Enum):
    PENALTY__UNDESIRABLE_TIMESLOT_5 = 5
    PENALTY__UNDESIRABLE_TIMESLOT_2 = 4
    PENALTY__UNDESIRABLE_TIMESLOT_1 = 3
    PENALTY__AVOID_ROOM_FOR_SESSION = 2

    BONUS__PREFER_ROOM_FOR_SESSION = 1


class PenaltyNames(str, Enum):
    UNDESIRABLE_TIMESLOT = '"UndesirableTimeslot"'
    AVOID_ROOM_FOR_SESSION = '"AvoidRoomForDegree"'


class PenaltyCosts(int, Enum):
    UNDESIRABLE_TIMESLOT_1 = 10
    UNDESIRABLE_TIMESLOT_2 = 20
    UNDESIRABLE_TIMESLOT_5 = 50
    AVOID_ROOM_FOR_SESSION = 15


class BonusNames(str, Enum):
    PREFER_ROOM_FOR_SESSION = '"PreferRoomForSession"'


class BonusCosts(int, Enum):
    PREFER_ROOM_FOR_SESSION = 15

from enum import Enum


class OptimizationPriorities(int, Enum):
    UNDESIRABLE_TIMESLOT_5 = 4
    UNDESIRABLE_TIMESLOT_2 = 3
    UNDESIRABLE_TIMESLOT_1 = 2
    ROOM_PREFERENCE_FOR_SESSION = 1


class PenaltyNames(str, Enum):
    UNDESIRABLE_TIMESLOT = '"UndesirableTimeslot"'
    AVOID_ROOM_FOR_SESSION = '"AvoidRoomForDegree"'


class PenaltyCosts(int, Enum):
    UNDESIRABLE_TIMESLOT_1 = 10
    AVOID_ROOM_FOR_SESSION = 15
    UNDESIRABLE_TIMESLOT_2 = 20
    UNDESIRABLE_TIMESLOT_5 = 50


class BonusNames(str, Enum):
    PREFER_ROOM_FOR_SESSION = '"PreferRoomForSession"'


class BonusCosts(int, Enum):
    PREFER_ROOM_FOR_SESSION = 15

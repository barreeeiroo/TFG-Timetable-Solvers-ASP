from enum import Enum


class PenaltyNames(str, Enum):
    UNDESIRABLE_TIMESLOT_1 = '"UndesirableTimeslot1"'
    UNDESIRABLE_TIMESLOT_2 = '"UndesirableTimeslot2"'
    UNDESIRABLE_TIMESLOT_5 = '"UndesirableTimeslot5"'


class PenaltyPriorities(int, Enum):
    UNDESIRABLE_TIMESLOT_1 = 3
    UNDESIRABLE_TIMESLOT_2 = 2
    UNDESIRABLE_TIMESLOT_5 = 1


class SlotPenalties(int, Enum):
    UNDESIRABLE_1 = 10
    UNDESIRABLE_2 = 20
    UNDESIRABLE_5 = 50

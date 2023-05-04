from enum import Enum


class PenaltyNames(str, Enum):
    UNDESIRABLE_TIMESLOT = '"UndesirableTimeslot"'


class SlotPenalties(int, Enum):
    UNDESIRABLE_1 = 10
    UNDESIRABLE_2 = 20
    UNDESIRABLE_5 = 50

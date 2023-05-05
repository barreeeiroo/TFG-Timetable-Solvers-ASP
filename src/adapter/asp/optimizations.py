from enum import Enum


class OptimizationPriorities(int, Enum):
    UNDESIRABLE_TIMESLOT_5 = 3
    UNDESIRABLE_TIMESLOT_2 = 2
    UNDESIRABLE_TIMESLOT_1 = 1


class PenaltyNames(str, Enum):
    UNDESIRABLE_TIMESLOT = '"UndesirableTimeslot"'


class PenaltyCosts(int, Enum):
    UNDESIRABLE_TIMESLOT_1 = 10
    UNDESIRABLE_TIMESLOT_2 = 20
    UNDESIRABLE_TIMESLOT_5 = 50

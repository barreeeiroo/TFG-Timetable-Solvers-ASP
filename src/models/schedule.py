from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from functools import partial
from typing import Dict, List

from models.course import Course, SessionType
from models.room import Room
from utils.timeframe import Timeframe


class ScheduleUnit:
    def __init__(self, timeframe: Timeframe, course: Course, session_type: SessionType, room: Room):
        self.time: Timeframe = timeframe
        self.course: Course = course
        self.session_type: SessionType = session_type
        self.room: Room = room

    def is_overlapping(self, other: ScheduleUnit) -> bool:
        return other in self

    def __contains__(self, item):
        if isinstance(item, ScheduleUnit):
            start, end = max(item.time.start, self.time.start), min(item.time.end, self.time.end)
            return (end - start) > timedelta(milliseconds=0)
        return super().__contains__(item)


class Timetable:
    def __init__(self, can_overlap: bool = True):
        self.__can_overlap: bool = can_overlap
        self.__timetable: List[ScheduleUnit] = []

    def add_scheduled_unit(self, schedule_unit: ScheduleUnit):
        if not self.__can_overlap:
            for scheduled_unit in self.__timetable:
                if scheduled_unit.is_overlapping(schedule_unit):
                    raise ValueError(f"{schedule_unit.course} @ {schedule_unit.time} has a strong conflict with "
                                     f"{scheduled_unit.course} @ {scheduled_unit.time}")
        self.__timetable.append(schedule_unit)

    def get_timetable(self) -> List[ScheduleUnit]:
        return sorted(self.__timetable, key=lambda x: x.start)


class Schedule:
    def __init__(self):
        self.course_view: Dict[Course, Timetable] = defaultdict(partial(Timetable, can_overlap=True))
        self.room_view: Dict[Room, Timetable] = defaultdict(partial(Timetable, can_overlap=False))

    def store_schedule_unit(self, schedule_unit: ScheduleUnit):
        self.course_view[schedule_unit.course].add_scheduled_unit(schedule_unit)
        self.room_view[schedule_unit.room].add_scheduled_unit(schedule_unit)

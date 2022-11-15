from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from enum import Enum
from typing import Union, Dict, List

from utils.timeframe import Timeframe


class Semester(Enum):
    FIRST_SEMESTER = "1SG"
    SECOND_SEMESTER = "2SG"
    ANUAL = "ANG"

    @staticmethod
    def from_string(original_semester: str) -> Semester:
        semester = original_semester.upper()
        if semester == "1SG":
            return Semester.FIRST_SEMESTER
        if semester == "2SG":
            return Semester.ANUAL
        if semester == "ANG":
            return Semester.ANUAL
        raise NotImplementedError(f"Semester {original_semester} is not valid")


class SessionType(Enum):
    CLE = "Lecture"
    CLIS = "Seminar"
    CLIL = "Laboratory"

    @staticmethod
    def parse_from_string(session_type: str) -> SessionType:
        session_type = session_type.upper()
        if session_type == "CLE":
            return SessionType.CLE
        if session_type == "CLIS":
            return SessionType.CLIS
        if session_type == "CLIL":
            return SessionType.CLIL
        raise NotImplementedError(f"Session Type {session_type} not supported")

    def __repr__(self):
        return self.value


class Course:
    def __init__(self, year: Union[str, int], code: str, name: str, short_name: str, semester: str):
        self.year: int = int(year)
        self.code: str = str(code)
        self.name: str = str(name)
        self.short_name: str = str(short_name)
        self.semester: Semester = Semester.from_string(semester)

        self.sessions: Dict[SessionType, List[timedelta]] = defaultdict(list)

    def add_session_type(self, session_type: str, slot_duration: str, count: int):
        session = SessionType.parse_from_string(session_type)
        slot = Timeframe.parse_slot_duration(slot_duration)
        for _ in range(count):
            self.sessions[session].append(slot)

    def __repr__(self):
        return f"Course({self.short_name})"

    def __eq__(self, other):
        return isinstance(other, Course) and other.short_name == self.short_name

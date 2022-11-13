from __future__ import annotations

from enum import Enum
from typing import Union


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


class Course:
    def __init__(self, year: Union[str, int], code: str, name: str, short_name: str, semester: str):
        self.year: int = int(year)
        self.code: str = str(code)
        self.name: str = str(name)
        self.short_name: str = str(short_name)
        self.semester: Semester = Semester.from_string(semester)

    def __repr__(self):
        return f"Course({self.short_name})"

    def __eq__(self, other):
        return isinstance(other, Course) and other.short_name == self.short_name

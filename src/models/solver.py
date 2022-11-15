from abc import ABC, abstractmethod
from typing import List

from models.course import Course
from models.room import Room
from models.schedule import Schedule
from models.settings import Settings


class Solver(ABC):
    def __init__(self, courses: List[Course], rooms: List[Room], settings: Settings):
        self._courses = courses
        self._rooms = rooms
        self._settings = settings

    @abstractmethod
    def solve(self) -> Schedule:
        raise NotImplementedError()

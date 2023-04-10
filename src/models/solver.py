from abc import ABC, abstractmethod
from typing import List

from models.dto.output import Output
from models.room import Room
from models.session import Session
from models.settings import Settings


class Solver(ABC):
    def __init__(self, sessions: List[Session], rooms: List[Room], settings: Settings):
        self._sessions = sessions
        self._rooms = rooms
        self._settings = settings

    @abstractmethod
    def solve(self) -> Output:
        raise NotImplementedError()

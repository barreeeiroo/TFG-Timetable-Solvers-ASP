from abc import ABC, abstractmethod
from typing import List, Optional

from models.dto.output import Output
from models.room import Room
from models.session import Session
from models.settings import Settings


class Solver(ABC):
    def __init__(self, sessions: List[Session], rooms: List[Room], settings: Settings):
        self._sessions = sessions
        self._rooms = rooms
        self._settings = settings
        self._execution_uuid: Optional[str] = None

    def with_execution_uuid(self, execution_uuid: str):
        self._execution_uuid = execution_uuid

    @abstractmethod
    def solve(self) -> Output:
        raise NotImplementedError()

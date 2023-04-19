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

    def _find_session_by_hex(self, uuid_hex: str) -> Session:
        return next(session for session in self._sessions if session.id.hex == uuid_hex)

    def _find_room_by_hex(self, uuid_hex: str) -> Room:
        return next(room for room in self._rooms if room.id.hex == uuid_hex)

    @abstractmethod
    def solve(self) -> Output:
        raise NotImplementedError()

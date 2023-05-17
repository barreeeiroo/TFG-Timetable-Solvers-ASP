from abc import ABC, abstractmethod
from pathlib import Path
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
        self._local_dir: Optional[Path] = None
        self._timeout: Optional[int] = None

    def with_execution_uuid(self, execution_uuid: str):
        self._execution_uuid = execution_uuid

    def with_local_working_directory(self, working_directory: Path):
        self._local_dir = working_directory

    def with_timeout(self, timeout: int):
        self._timeout = timeout

    def _find_session_by_hex(self, uuid_hex: str) -> Session:
        return next(session for session in self._sessions if session.id.hex == uuid_hex)

    def _find_room_by_hex(self, uuid_hex: str) -> Room:
        return next(room for room in self._rooms if room.id.hex == uuid_hex)

    @abstractmethod
    def solve(self) -> Output:
        raise NotImplementedError()

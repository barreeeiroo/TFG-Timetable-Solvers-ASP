from __future__ import annotations

from datetime import timedelta
from enum import Enum


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


class Session:
    def __init__(self, session_type: SessionType, duration: timedelta, per_week: int, num_groups: int):
        self.session_type: SessionType = session_type
        self.duration: timedelta = duration
        self.num_per_week: int = per_week
        self.num_groups: int = num_groups

from typing import List

from models.course import SessionType


class Building:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"Building({self.name})"

    def __eq__(self, other):
        return isinstance(other, Building) and other.name == self.name


class Room:
    def __init__(self, name: str, building: str, capacity: int, session_types: str):
        self.name: str = str(name)
        self.building: Building = Building(building)
        self.capacity: int = int(capacity)
        self.session_types: List[SessionType] = [
            SessionType.parse_from_string(session_type) for session_type in session_types.split("-")
        ]

    def __repr__(self):
        return f"Room({self.name})"

    def __eq__(self, other):
        return isinstance(other, Room) and other.building == self.building and other.name == self.name

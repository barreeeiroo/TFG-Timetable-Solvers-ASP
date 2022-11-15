from __future__ import annotations

from models.room import Room


class ClingoConstants:
    TIMESLOT = "T"
    UNIT = "U"
    ROOM = "R"

    BLOCKED_SLOT = "blockedSlot"
    UNDESIRABLE_SLOT = "undesirableSlot"

    @staticmethod
    def assigned_slot(timeslot: str = "_", unit: str = "_", room: str = "_", name: bool = False) -> str:
        assigned_slot = "assignedSlot"
        if name:
            return f"{assigned_slot}/3."
        return f"{assigned_slot}({timeslot},{unit},{room})"

    @staticmethod
    def timeslot(t: str) -> str:
        return f"timeslot({t})"

    @staticmethod
    def room(r: str) -> str:
        return f"room({r})"


class ClingoNaming:
    @staticmethod
    def room_to_clingo(room: Room) -> str:
        building = room.building.name
        room_name = room.name
        return f"room_{building}_{room_name}"

    @staticmethod
    def clingo_to_room(clingo: str) -> Room:
        _, building_name, room_name = clingo.split("_")
        return Room(room_name, building_name, 0)

from __future__ import annotations

from pydantic import BaseModel

from models.dto.input import Room, Session
from models.slot import Slot


class ScheduleUnit(BaseModel):
    slot: Slot
    session: Session
    room: Room

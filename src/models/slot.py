from enum import Enum
from typing import Optional

from pydantic import BaseModel

from models.timeframe import Timeframe


class SlotType(str, Enum):
    AVAILABLE = "available"
    UNDESIRABLE = "undesirable"
    # Or SCHEDULED
    BLOCKED = "blocked"


class Slot(BaseModel):
    week_day: int
    timeframe: Timeframe
    slot_type: Optional[SlotType]

    def __hash__(self):
        return hash((self.week_day, self.timeframe,))

    def __eq__(self, other):
        return isinstance(other, Slot) and other.week_day == self.week_day and other.timeframe == self.timeframe

    def __repr__(self):
        return f"Slot({self.week_day}, {self.timeframe}, {self.slot_type})"

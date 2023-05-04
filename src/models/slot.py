from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from models.timeframe import Timeframe


class SlotType(str, Enum):
    AVAILABLE = "available"
    UNDESIRABLE_1 = "undesirable1"
    UNDESIRABLE_2 = "undesirable2"
    UNDESIRABLE_5 = "undesirable5"
    # Or SCHEDULED
    BLOCKED = "blocked"


class Slot(BaseModel):
    class Config:
        allow_population_by_field_name = True

    week_day: int = Field(alias="weekDay")
    timeframe: Timeframe
    slot_type: Optional[SlotType] = Field(alias="slotType")

    def __hash__(self):
        return hash((self.week_day, self.timeframe,))

    def __eq__(self, other):
        return isinstance(other, Slot) and other.week_day == self.week_day and other.timeframe == self.timeframe

    def __repr__(self):
        return f"Slot({self.week_day}, {self.timeframe}, {self.slot_type})"

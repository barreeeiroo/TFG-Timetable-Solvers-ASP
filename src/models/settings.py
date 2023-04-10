from __future__ import annotations

from datetime import time, timedelta
from typing import List

from pydantic import BaseModel, Field

from models.slot import Slot


class Settings(BaseModel):
    class Config:
        allow_population_by_field_name = True

    day_start: time = Field(alias="dayStart")
    day_end: time = Field(alias="dayEnd")
    week_days: List[int] = Field(alias="weekDays")
    slot_duration: timedelta = Field(alias="slotDuration")

    modified_slots: List[Slot] = Field(alias="modifiedSlots")

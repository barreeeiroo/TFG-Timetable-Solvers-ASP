from __future__ import annotations

from datetime import time, timedelta
from typing import List

from pydantic import BaseModel

from models.slot import Slot


class Settings(BaseModel):
    day_start: time
    day_end: time
    week_days: List[int]
    slot_duration: timedelta

    modified_slots: List[Slot]

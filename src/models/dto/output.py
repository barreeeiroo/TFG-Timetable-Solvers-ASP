from typing import List

from pydantic import BaseModel, Field

from models.schedule import ScheduleUnit


class Output(BaseModel):
    timetable: List[ScheduleUnit] = Field(default_factory=list)

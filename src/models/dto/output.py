from typing import List

from pydantic import Field, BaseModel

from models.schedule import ScheduleUnit


class Output(BaseModel):
    timetable: List[ScheduleUnit] = Field(default=list)

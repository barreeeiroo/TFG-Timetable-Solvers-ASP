from pydantic import BaseModel

from models.dto.input import Room, Session
from utils.timeframe import Timeframe


class ScheduleUnit(BaseModel):
    timeframe: Timeframe
    session: Session
    room: Room

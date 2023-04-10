from typing import List

from pydantic import BaseModel

from models.room import Room
from models.session import Session
from models.settings import Settings


class SolverInput(BaseModel):
    class Config:
        allow_population_by_field_name = True

    settings: Settings
    sessions: List[Session]
    rooms: List[Room]

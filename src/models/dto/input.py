from typing import List

from pydantic import BaseModel

from models.room import Room
from models.session import Session
from models.settings import Settings


class Input(BaseModel):
    settings: Settings
    sessions: List[Session]
    rooms: List[Room]

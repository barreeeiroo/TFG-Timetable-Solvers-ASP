from typing import List

from pydantic import BaseModel

from models.room import Room
from models.session import Session


class Input(BaseModel):
    sessions: List[Session]
    rooms: List[Room]

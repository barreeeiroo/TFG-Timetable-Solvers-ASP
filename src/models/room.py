from __future__ import annotations

from typing import Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, UUID4


class Room(BaseModel):
    id: UUID4 = Field(default_factory=uuid4)

    constraints: RoomConstraints
    metadata: Optional[Any] = None


class RoomConstraints(BaseModel):
    capacity: int

    preferred_session_types: List[str]

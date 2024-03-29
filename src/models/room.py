from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, UUID4


class RoomConstraints(BaseModel):
    class Config:
        allow_population_by_field_name = True

    capacity: int
    session_types: List[str] = Field(alias="sessionTypes")

    distances_in_minutes: Dict[str, float] = Field(alias="distancesInMinutes", default_factory=dict)


class Room(BaseModel):
    class Config:
        allow_population_by_field_name = True

    id: UUID4 = Field(default_factory=uuid4)

    constraints: RoomConstraints
    metadata: Optional[Any] = None

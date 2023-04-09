from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, UUID4


class RoomConstraints(BaseModel):
    class Config:
        allow_population_by_field_name = True

    capacity: Optional[int] = Field(default=None)
    preferred_session_types: Optional[List[str]] = Field(alias="preferredSessionTypes", default=None)

    distances_in_minutes: Optional[Dict[str, float]] = Field(alias="distancesInMinutes", default=None)


class Room(BaseModel):
    class Config:
        allow_population_by_field_name = True

    id: UUID4 = Field(default_factory=uuid4)

    constraints: RoomConstraints = Field(default=RoomConstraints())
    metadata: Optional[Any] = Field(default=None)

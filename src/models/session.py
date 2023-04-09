from __future__ import annotations

from datetime import timedelta
from typing import Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, UUID4

from models.timeframe import Timeframe


class SessionConstraints(BaseModel):
    class Config:
        allow_population_by_field_name = True

    session_type: str = Field(alias="sessionType")
    duration: timedelta

    cannot_conflict_in_time: Optional[List[UUID4]] = Field(alias="cannotConflictInTime", default=None)
    preferred_slots: Optional[List[Timeframe]] = Field(alias="preferredSlots", default=None)


class Session(BaseModel):
    class Config:
        allow_population_by_field_name = True

    id: UUID4 = Field(default_factory=uuid4)

    constraints: SessionConstraints
    metadata: Optional[Any] = None

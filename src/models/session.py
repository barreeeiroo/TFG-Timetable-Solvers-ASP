from __future__ import annotations

from datetime import timedelta
from typing import Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, UUID4

from models.timeframe import Timeframe


class Session(BaseModel):
    id: UUID4 = Field(default_factory=uuid4)

    constraints: SessionConstraints
    metadata: Optional[Any] = None


class SessionConstraints(BaseModel):
    session_type: str
    duration: timedelta

    cannot_conflict_in_time: List[UUID4] = Field(default_factory=list)
    preferred_slots: List[Timeframe] = Field(default_factory=list)

from datetime import timedelta
from typing import Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Session(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    session_type: str
    duration: timedelta

    metadata: Optional[Any] = None

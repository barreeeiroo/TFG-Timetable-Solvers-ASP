from typing import List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Room(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    capacity: int
    preferred_session_types: List[str]

    metadata: Optional[Any] = None

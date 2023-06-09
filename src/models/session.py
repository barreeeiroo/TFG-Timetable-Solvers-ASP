from __future__ import annotations

from datetime import timedelta
from typing import Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, UUID4

from models.slot import Slot


class SessionRoomPreferences(BaseModel):
    class Config:
        allow_population_by_field_name = True

    disallowed_rooms: List[UUID4] = Field(alias="disallowedRooms", default_factory=list)
    penalized_rooms: List[UUID4] = Field(alias="penalizedRooms", default_factory=list)
    preferred_rooms: List[UUID4] = Field(alias="preferredRooms", default_factory=list)


class SessionTimeslotPreferences(BaseModel):
    class Config:
        allow_population_by_field_name = True

    disallowed_slots: List[Slot] = Field(alias="disallowedSlots", default_factory=list)
    penalized_slots: List[Slot] = Field(alias="penalizedSlots", default_factory=list)
    preferred_slots: List[Slot] = Field(alias="preferredSlots", default_factory=list)


class SessionConstraints(BaseModel):
    class Config:
        allow_population_by_field_name = True

    session_type: str = Field(alias="sessionType")
    duration: timedelta

    cannot_conflict_in_time: List[UUID4] = Field(alias="cannotConflictInTime", default_factory=list)
    avoid_conflict_in_time: List[UUID4] = Field(alias="avoidConflictInTime", default_factory=list)
    same_room_if_contiguous_in_time: List[UUID4] = Field(alias="sameRoomIfContiguousInTime", default_factory=list)
    rooms_preferences: SessionRoomPreferences = Field(alias="roomsPreferences", default=SessionRoomPreferences())
    timeslots_preferences: SessionTimeslotPreferences = Field(alias="timeslotsPreferences",
                                                              default=SessionTimeslotPreferences())


class Session(BaseModel):
    class Config:
        allow_population_by_field_name = True

    id: UUID4 = Field(default_factory=uuid4)

    constraints: SessionConstraints
    metadata: Optional[Any] = None

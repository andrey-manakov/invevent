
from datetime import datetime, timezone
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import String,Integer,DateTime,ForeignKey,Text,Enum as SAEnum
from sqlalchemy import Float
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import event
from .database import Base

class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    first_name:Mapped[str]=mapped_column(String(64))
    username:Mapped[Optional[str]]=mapped_column(String(64))

class EventVisibility(str,PyEnum):
    Public="Public"
    Private="Private"

class EventState(str,PyEnum):
    Active="Active"
    Past="Past"
    Deleted="Deleted"

class Event(Base):
    __tablename__="events"
    id:Mapped[str]=mapped_column(String(36),primary_key=True)
    owner_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id"))
    title:Mapped[str]=mapped_column(String(80))
    description:Mapped[str]=mapped_column(Text)
    datetime_utc:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    
    # location_txt:Mapped[str]=mapped_column(String(120))
    location_txt:Mapped[Optional[str]]=mapped_column(String(120), nullable=True)

    visibility:Mapped[EventVisibility]=mapped_column(SAEnum(EventVisibility))
    tags:Mapped[str]=mapped_column(String(120))
    state:Mapped[EventState]=mapped_column(SAEnum(EventState),default=EventState.Active)

    # New fields to store geolocation or fallback address
    latitude:Mapped[Optional[float]]  = mapped_column(Float, nullable=True)
    longitude:Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    address:Mapped[Optional[str]]     = mapped_column(String(120), nullable=True)

class Participation(Base):
    __tablename__="participations"
    event_id:Mapped[str]=mapped_column(String(36),ForeignKey("events.id"),primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id"),primary_key=True)
    joined_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda: datetime.utcnow())

class Friendship(Base):
    __tablename__="friendships"
    follower_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id"),primary_key=True)
    followee_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id"),primary_key=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda: datetime.utcnow())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Older databases might contain naive timestamps for ``Event.datetime_utc``.
# When an ``Event`` object is loaded, ensure this field is timezone-aware to
# avoid ``TypeError`` during comparisons.

@event.listens_for(Event, "load")
def _event_fix_naive_dt(target, _context) -> None:
    dt = target.datetime_utc
    if dt is not None and dt.tzinfo is None:
        target.datetime_utc = dt.replace(tzinfo=timezone.utc)


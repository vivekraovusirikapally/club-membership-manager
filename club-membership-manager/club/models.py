"""Plain data classes for members and events."""
from dataclasses import dataclass, field, asdict


@dataclass
class Member:
    member_id: str
    name: str
    email: str
    phone: str
    department: str
    year: int
    join_date: str            # YYYY-MM-DD
    status: str = "active"    # active / inactive / alumni
    dues_paid: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class Event:
    event_id: str
    title: str
    date: str                 # YYYY-MM-DD
    category: str
    capacity: int
    attendees: list = field(default_factory=list)   # member ids

    def to_dict(self):
        return asdict(self)

    @property
    def seats_left(self):
        return self.capacity - len(self.attendees)

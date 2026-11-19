"""The actual club rules: members, events, registrations, search, import."""
import csv
from collections import Counter
from datetime import date, timedelta

from . import validation as v
from .models import Member, Event


class ClubError(Exception):
    """A rule was broken (duplicate email, event full, etc)."""


class Club:
    def __init__(self, members=None, events=None):
        self.members = members if members is not None else {}
        self.events = events if events is not None else {}

    # ---- ids ------------------------------------------------------------
    def _next_id(self, prefix, existing):
        nums = [int(k[1:]) for k in existing if k[1:].isdigit()]
        return f"{prefix}{(max(nums) + 1) if nums else 1:03d}"

    # ---- members --------------------------------------------------------
    def email_taken(self, email, ignore_id=None):
        return any(m.email == email and m.member_id != ignore_id for m in self.members.values())

    def add_member(self, name, email, phone, department, year, join_date, status="active", dues_paid=False):
        if self.email_taken(email):
            raise ClubError(f"A member with {email} already exists.")
        mid = self._next_id("M", self.members)
        m = Member(mid, name, email, phone, department, year, join_date, status, dues_paid)
        self.members[mid] = m
        return m

    def get_member(self, member_id):
        mid = member_id.strip().upper()
        if mid not in self.members:
            raise ClubError(f"No member with id {mid}.")
        return self.members[mid]

    def update_member(self, member_id, **changes):
        m = self.get_member(member_id)
        if "email" in changes and self.email_taken(changes["email"], ignore_id=m.member_id):
            raise ClubError("That email belongs to someone else.")
        for key, value in changes.items():
            setattr(m, key, value)
        return m

    def remove_member(self, member_id):
        m = self.get_member(member_id)
        del self.members[m.member_id]
        for e in self.events.values():
            if m.member_id in e.attendees:
                e.attendees.remove(m.member_id)
        return m

    def search(self, keyword="", department="", status=""):
        kw = keyword.strip().lower()
        out = []
        for m in self.members.values():
            if department and m.department != department.upper():
                continue
            if status and m.status != status.lower():
                continue
            if kw and kw not in f"{m.member_id} {m.name} {m.email} {m.phone}".lower():
                continue
            out.append(m)
        return sorted(out, key=lambda m: m.name.lower())

    # ---- events ---------------------------------------------------------
    def add_event(self, title, event_date, category, capacity):
        if any(e.title.lower() == title.lower() and e.date == event_date for e in self.events.values()):
            raise ClubError("An event with this title and date already exists.")
        eid = self._next_id("E", self.events)
        e = Event(eid, title, event_date, category, capacity)
        self.events[eid] = e
        return e

    def get_event(self, event_id):
        eid = event_id.strip().upper()
        if eid not in self.events:
            raise ClubError(f"No event with id {eid}.")
        return self.events[eid]

    def register(self, event_id, member_id):
        e = self.get_event(event_id)
        m = self.get_member(member_id)
        if m.status != "active":
            raise ClubError(f"{m.name} is {m.status}; only active members can register.")
        if m.member_id in e.attendees:
            raise ClubError(f"{m.name} is already registered for {e.title}.")
        if e.seats_left <= 0:
            raise ClubError(f"{e.title} is full ({e.capacity}/{e.capacity}).")
        e.attendees.append(m.member_id)
        return e, m

    def unregister(self, event_id, member_id):
        e = self.get_event(event_id)
        m = self.get_member(member_id)
        if m.member_id not in e.attendees:
            raise ClubError(f"{m.name} isn't registered for {e.title}.")
        e.attendees.remove(m.member_id)
        return e, m

    def events_attended(self, member_id):
        return sum(1 for e in self.events.values() if member_id in e.attendees)

    # ---- bulk import ----------------------------------------------------
    def import_csv(self, path):
        """Returns (added_count, errors) where errors is a list of 'row N: reason' strings."""
        needed = {"name", "email", "phone", "department", "year", "join_date"}
        errors, added = [], 0
        try:
            f = open(path, newline="", encoding="utf-8-sig")
        except OSError as err:
            return 0, [f"Could not open file: {err}"]
        with f:
            reader = csv.DictReader(f)
            headers = {h.strip().lower() for h in (reader.fieldnames or [])}
            missing = needed - headers
            if missing:
                return 0, [f"Missing column(s): {', '.join(sorted(missing))}"]
            for row_no, raw in enumerate(reader, start=2):   # row 1 is the header
                row = {(k or "").strip().lower(): (val or "").strip() for k, val in raw.items()}
                try:
                    self.add_member(
                        v.clean_name(row["name"]),
                        v.clean_email(row["email"]),
                        v.clean_phone(row["phone"]),
                        v.clean_department(row["department"]),
                        v.clean_year(row["year"]),
                        v.clean_join_date(row["join_date"]),
                        v.clean_status(row.get("status") or "active"),
                        v.clean_yes_no(row.get("dues_paid") or "n"),
                    )
                    added += 1
                except (v.ValidationError, ClubError) as err:
                    errors.append(f"row {row_no}: {err}")
        return added, errors

    # ---- numbers --------------------------------------------------------
    def summary(self):
        ms = list(self.members.values())
        es = list(self.events.values())
        total = len(ms)
        paid = sum(1 for m in ms if m.dues_paid)
        rates = [len(e.attendees) / e.capacity for e in es if e.capacity]
        busiest = sorted(ms, key=lambda m: -self.events_attended(m.member_id))[:3]
        return {
            "total_members": total,
            "by_status": dict(Counter(m.status for m in ms)),
            "by_department": dict(Counter(m.department for m in ms).most_common()),
            "by_year": dict(sorted(Counter(m.year for m in ms).items())),
            "dues_paid": paid,
            "dues_rate": (paid / total * 100) if total else 0.0,
            "avg_year": (sum(m.year for m in ms) / total) if total else 0.0,
            "total_events": len(es),
            "avg_fill_rate": (sum(rates) / len(rates) * 100) if rates else 0.0,
            "total_registrations": sum(len(e.attendees) for e in es),
            "joins_by_month": dict(sorted(Counter(m.join_date[:7] for m in ms).items())),
            "top_attendees": [(m.name, self.events_attended(m.member_id)) for m in busiest
                              if self.events_attended(m.member_id) > 0],
            "top_events": [(e.title, len(e.attendees)) for e in
                           sorted(es, key=lambda e: -len(e.attendees))[:3]],
        }

    def warnings(self, today=None):
        today = today or date.today()
        out = []
        for m in self.members.values():
            joined = date.fromisoformat(m.join_date)
            if m.status == "active" and not m.dues_paid and (today - joined) > timedelta(days=30):
                out.append(f"Dues overdue: {m.name} ({m.member_id}) joined {m.join_date} and hasn't paid.")
        for e in self.events.values():
            d = date.fromisoformat(e.date)
            fill = len(e.attendees) / e.capacity
            if d >= today and fill >= 0.9:
                out.append(f"Almost full: {e.title} on {e.date} is at {len(e.attendees)}/{e.capacity}.")
            if today <= d <= today + timedelta(days=7) and fill < 0.3:
                out.append(f"Low turnout risk: {e.title} is within a week, only {len(e.attendees)}/{e.capacity} signed up.")
            if d < today and not e.attendees:
                out.append(f"Empty past event: {e.title} on {e.date} has no recorded attendees.")
        idle = [m for m in self.members.values()
                if m.status == "active" and self.events and self.events_attended(m.member_id) == 0]
        if idle:
            out.append(f"{len(idle)} active member(s) haven't joined any event yet.")
        return out

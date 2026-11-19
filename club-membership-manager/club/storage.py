"""Reading and writing the JSON data file. Never crashes on a bad file."""
import json
import os
import shutil
from datetime import datetime

from .models import Member, Event

DEFAULT_PATH = os.path.join("data", "club_data.json")


def save(members, events, path=DEFAULT_PATH):
    """Write to a temp file first, then swap it in, so a crash can't half-write the data."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    payload = {
        "members": [m.to_dict() for m in members.values()],
        "events": [e.to_dict() for e in events.values()],
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


def load(path=DEFAULT_PATH):
    """Returns (members, events, notes). notes is a list of things worth telling the user."""
    notes = []
    members, events = {}, {}

    if not os.path.exists(path):
        notes.append("No data file found, starting fresh.")
        return members, events, notes

    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("top level must be an object")
    except (json.JSONDecodeError, ValueError, OSError) as err:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = f"{path}.corrupt_{stamp}"
        try:
            shutil.copy(path, backup)
            notes.append(f"Data file was unreadable ({err}). Copied it to {backup} and started fresh.")
        except OSError:
            notes.append(f"Data file was unreadable ({err}). Started fresh.")
        return members, events, notes

    skipped = 0
    for item in raw.get("members", []):
        try:
            m = Member(**item)
            members[m.member_id] = m
        except (TypeError, ValueError):
            skipped += 1
    for item in raw.get("events", []):
        try:
            e = Event(**item)
            events[e.event_id] = e
        except (TypeError, ValueError):
            skipped += 1
    if skipped:
        notes.append(f"Skipped {skipped} malformed record(s) while loading.")
    return members, events, notes

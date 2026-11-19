"""The menu and all the print/input code."""
import os
import sys

from . import reports, storage
from . import validation as v
from .logic import Club, ClubError

PAGE_SIZE = 10
USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def paint(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def good(t): return paint(t, "32")
def bad(t): return paint(t, "31")
def warn(t): return paint(t, "33")
def head(t): return paint(t, "1;36")


BANNER = r"""
  ____ _       _     __  __                _
 / ___| |_   _| |__ |  \/  | __ _ _ __   __| | __ _  ___ _ __
| |   | | | | | '_ \| |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
| |___| | |_| | |_) | |  | | (_| | | | | (_| | (_| |  __/ |
 \____|_|\__,_|_.__/|_|  |_|\__,_|_| |_|\__,_|\__, |\___|_|
                                              |___/
"""

MENU = """
 MEMBERS                      EVENTS
  1) Add member                6) Create event
  2) View all members          7) View events
  3) Search members            8) Register member for event
  4) Update member             9) Cancel a registration
  5) Remove member

 REPORTS & DATA
  10) Summary    11) Warnings    12) Export reports    13) Import CSV
  0) Save and exit
"""


def table(rows, headers, widths):
    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    def fmt(cells):
        return "| " + " | ".join(str(c)[:w].ljust(w) for c, w in zip(cells, widths)) + " |"
    print(line)
    print(fmt(headers))
    print(line)
    for r in rows:
        print(fmt(r))
    print(line)


def paged(rows, headers, widths):
    if not rows:
        print(warn("  Nothing to show."))
        return
    for start in range(0, len(rows), PAGE_SIZE):
        table(rows[start:start + PAGE_SIZE], headers, widths)
        end = min(start + PAGE_SIZE, len(rows))
        print(f"  showing {start + 1}-{end} of {len(rows)}")
        if end < len(rows):
            if input("  Enter for next page, q to stop: ").strip().lower() == "q":
                break


def member_rows(club, members):
    return [(m.member_id, m.name, m.department, m.year, m.status,
             "yes" if m.dues_paid else "NO", club.events_attended(m.member_id)) for m in members]


MEMBER_HEADERS = ("ID", "Name", "Dept", "Yr", "Status", "Dues", "Events")
MEMBER_WIDTHS = (5, 24, 6, 2, 8, 4, 6)


class App:
    def __init__(self, data_path=storage.DEFAULT_PATH):
        self.path = data_path
        members, events, notes = storage.load(data_path)
        self.club = Club(members, events)
        for n in notes:
            print(warn("  Note: " + n))

    def save(self):
        storage.save(self.club.members, self.club.events, self.path)

    # ---- members --------------------------------------------------------
    def add_member(self):
        print(head("\nAdd member") + "  (type 'cancel' anytime)")
        name = v.ask("  Full name: ", v.clean_name)
        while True:
            email = v.ask("  Email: ", v.clean_email)
            if not self.club.email_taken(email):
                break
            print(bad("  ! That email is already registered."))
        phone = v.ask("  Phone: ", v.clean_phone)
        dept = v.ask(f"  Department ({'/'.join(v.DEPARTMENTS)}): ", v.clean_department)
        year = v.ask("  Year (1-4): ", v.clean_year)
        from datetime import date
        today = date.today().isoformat()
        joined = v.ask(f"  Join date [Enter = {today}]: ", v.clean_join_date, default=today)
        paid = v.ask("  Dues paid? (y/n) [n]: ", v.clean_yes_no, default=False)
        m = self.club.add_member(name, email, phone, dept, year, joined, "active", paid)
        self.save()
        print(good(f"  Added {m.name} as {m.member_id}."))

    def view_members(self):
        members = self.club.search()
        paged(member_rows(self.club, members), MEMBER_HEADERS, MEMBER_WIDTHS)

    def search_members(self):
        print(head("\nSearch") + "  (leave a filter blank to skip it)")
        kw = input("  Keyword (name/email/phone/id): ").strip()
        dept = input("  Department: ").strip().upper()
        status = input("  Status (active/inactive/alumni): ").strip().lower()
        if dept and dept not in v.DEPARTMENTS:
            print(bad("  ! Unknown department.")); return
        if status and status not in v.STATUSES:
            print(bad("  ! Unknown status.")); return
        found = self.club.search(kw, dept, status)
        paged(member_rows(self.club, found), MEMBER_HEADERS, MEMBER_WIDTHS)

    def update_member(self):
        print(head("\nUpdate member") + "  (Enter keeps the current value)")
        m = self.club.get_member(input("  Member id: "))
        print(f"  Editing {m.name} ({m.member_id})")
        changes = {
            "name": v.ask(f"  Name [{m.name}]: ", v.clean_name, default=m.name),
            "email": v.ask(f"  Email [{m.email}]: ", v.clean_email, default=m.email),
            "phone": v.ask(f"  Phone [{m.phone}]: ", v.clean_phone, default=m.phone),
            "department": v.ask(f"  Department [{m.department}]: ", v.clean_department, default=m.department),
            "year": v.ask(f"  Year [{m.year}]: ", v.clean_year, default=m.year),
            "status": v.ask(f"  Status [{m.status}]: ", v.clean_status, default=m.status),
            "dues_paid": v.ask(f"  Dues paid? [{'y' if m.dues_paid else 'n'}]: ", v.clean_yes_no, default=m.dues_paid),
        }
        self.club.update_member(m.member_id, **changes)
        self.save()
        print(good("  Updated."))

    def remove_member(self):
        m = self.club.get_member(input("\n  Member id to remove: "))
        if input(f"  Really remove {m.name}? (y/n): ").strip().lower() != "y":
            print("  Kept."); return
        self.club.remove_member(m.member_id)
        self.save()
        print(good(f"  Removed {m.name}."))

    # ---- events ---------------------------------------------------------
    def create_event(self):
        print(head("\nCreate event") + "  (type 'cancel' anytime)")
        title = v.ask("  Title: ", v.clean_title)
        when = v.ask("  Date (YYYY-MM-DD): ", v.clean_date)
        cat = v.ask(f"  Category ({'/'.join(v.CATEGORIES)}): ", v.clean_category)
        cap = v.ask("  Capacity (1-500): ", v.clean_capacity)
        e = self.club.add_event(title, when, cat, cap)
        self.save()
        print(good(f"  Created {e.event_id}: {e.title}"))

    def view_events(self):
        rows = [(e.event_id, e.title, e.date, e.category, f"{len(e.attendees)}/{e.capacity}")
                for e in sorted(self.club.events.values(), key=lambda e: e.date)]
        paged(rows, ("ID", "Title", "Date", "Category", "Seats"), (5, 30, 10, 10, 7))

    def register(self):
        e = self.club.get_event(input("\n  Event id: "))
        m = self.club.get_member(input("  Member id: "))
        self.club.register(e.event_id, m.member_id)
        self.save()
        print(good(f"  {m.name} registered for {e.title} ({len(e.attendees)}/{e.capacity})."))

    def unregister(self):
        e = self.club.get_event(input("\n  Event id: "))
        m = self.club.get_member(input("  Member id: "))
        self.club.unregister(e.event_id, m.member_id)
        self.save()
        print(good(f"  {m.name} removed from {e.title}."))

    # ---- reports --------------------------------------------------------
    def summary(self):
        print()
        print(reports.summary_text(self.club))

    def warnings(self):
        warns = self.club.warnings()
        print(head("\nWarnings"))
        if not warns:
            print(good("  All clear."))
        for w in warns:
            print(warn("  ! " + w))

    def export(self):
        for p in reports.export_all(self.club):
            print(good("  wrote " + p))

    def import_csv(self):
        path = input("\n  CSV path [data/sample_import.csv]: ").strip() or os.path.join("data", "sample_import.csv")
        added, errors = self.club.import_csv(path)
        if added:
            self.save()
        print(good(f"  Imported {added} member(s)."))
        if errors:
            log = os.path.join("data", "import_errors.log")
            os.makedirs("data", exist_ok=True)
            with open(log, "w", encoding="utf-8") as f:
                f.write("\n".join(errors) + "\n")
            print(warn(f"  {len(errors)} row(s) rejected, details in {log}:"))
            for line in errors[:5]:
                print("    " + line)
            if len(errors) > 5:
                print(f"    ... and {len(errors) - 5} more")

    # ---- loop -----------------------------------------------------------
    def run(self):
        print(head(BANNER))
        print(f"  {len(self.club.members)} members, {len(self.club.events)} events loaded.")
        actions = {
            "1": self.add_member, "2": self.view_members, "3": self.search_members,
            "4": self.update_member, "5": self.remove_member, "6": self.create_event,
            "7": self.view_events, "8": self.register, "9": self.unregister,
            "10": self.summary, "11": self.warnings, "12": self.export, "13": self.import_csv,
        }
        while True:
            print(MENU)
            try:
                choice = input("  Choose: ").strip()
            except (EOFError, KeyboardInterrupt):
                choice = "0"
            if choice == "0":
                self.save()
                print(good("\n  Saved. See you next time!"))
                return
            action = actions.get(choice)
            if action is None:
                print(bad("  ! Pick a number from the menu."))
                continue
            try:
                action()
            except v.Cancelled:
                print(warn("\n  Cancelled."))
            except ClubError as err:
                print(bad(f"  ! {err}"))
            except KeyboardInterrupt:
                print(warn("\n  Interrupted."))

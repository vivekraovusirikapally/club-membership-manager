"""Builds the sample data: data/club_data.json, data/sample_members.csv and data/sample_import.csv.
Run:  python seed.py
"""
import csv
import json
import os
import random
from datetime import date, timedelta

from club.logic import Club
from club import storage

random.seed(29)
today = date.today()

FIRST = ["Aarav", "Ananya", "Rohan", "Sneha", "Vikram", "Priya", "Karthik", "Divya", "Arjun", "Meera",
         "Sai", "Lakshmi", "Rahul", "Neha", "Harsha", "Pooja", "Kiran", "Swathi", "Manoj", "Ishita"]
LAST = ["Reddy", "Sharma", "Rao", "Nair", "Patel", "Iyer", "Gupta", "Kumar", "Varma", "Das"]
DEPTS = ["CSE", "CSE", "CSE", "ECE", "ECE", "IT", "IT", "MECH", "EEE", "CIVIL", "MBA"]


def main():
    club = Club()
    names = set()
    while len(club.members) < 40:
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        if name in names:
            continue
        names.add(name)
        email = name.lower().replace(" ", ".") + "@college.edu"
        phone = str(random.choice("6789")) + "".join(random.choice("0123456789") for _ in range(9))
        joined = (today - timedelta(days=random.randint(2, 330))).isoformat()
        status = random.choices(["active", "inactive", "alumni"], [80, 12, 8])[0]
        club.add_member(name, email, phone, random.choice(DEPTS), random.randint(1, 4),
                        joined, status, random.random() < 0.65)

    # a few deliberate edge cases for the demo
    first = list(club.members.values())
    first[0].join_date = today.isoformat()       # joined today, dues not yet due
    first[0].dues_paid = False
    first[1].join_date = (today - timedelta(days=31)).isoformat()   # just past the 30-day line
    first[1].dues_paid = False
    first[1].status = "active"

    specs = [("Intro to Python Workshop", -40, "workshop", 30), ("Hack Night", -15, "technical", 25),
             ("Cultural Fest Planning", -5, "cultural", 20), ("Inter-Dept Cricket", 3, "sports", 12),
             ("Resume Clinic", 5, "workshop", 10), ("Annual Meetup", 20, "social", 40)]
    for title, offset, cat, cap in specs:
        club.add_event(title, (today + timedelta(days=offset)).isoformat(), cat, cap)

    active = [m.member_id for m in club.members.values() if m.status == "active"]
    for e in club.events.values():
        pick = min(len(active), e.capacity if e.title == "Resume Clinic" else random.randint(3, max(4, e.capacity - 2)))
        for mid in random.sample(active, pick):
            club.register(e.event_id, mid)

    os.makedirs("data", exist_ok=True)
    storage.save(club.members, club.events)

    with open(os.path.join("data", "sample_members.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["member_id", "name", "email", "phone", "department", "year", "join_date", "status", "dues_paid"])
        for m in club.members.values():
            w.writerow([m.member_id, m.name, m.email, m.phone, m.department, m.year,
                        m.join_date, m.status, "yes" if m.dues_paid else "no"])

    # legacy file with deliberate mistakes, to show off the row-by-row error log
    rows = [
        ["name", "email", "phone", "department", "year", "join_date", "status", "dues_paid"],
        ["Tara Menon", "tara.menon@college.edu", "9876501234", "CSE", "2", "2026-01-15", "active", "yes"],
        ["Dev Malhotra", "dev.m@college.edu", "8123456780", "ECE", "3", "2025-11-02", "active", "no"],
        ["", "blank.name@college.edu", "9876543210", "IT", "1", "2026-02-01", "active", "no"],
        ["Bad Email", "not-an-email", "9876543211", "IT", "1", "2026-02-01", "active", "no"],
        ["Year Nine", "year9@college.edu", "9876543212", "CSE", "9", "2026-02-01", "active", "no"],
        ["Short Phone", "short@college.edu", "12345", "CSE", "2", "2026-02-01", "active", "no"],
        ["Future Joiner", "future@college.edu", "9876543213", "CSE", "2", "2099-01-01", "active", "no"],
        ["Wrong Dept", "dept@college.edu", "9876543214", "BIOLOGY", "2", "2026-02-01", "active", "no"],
        ["Isha Bose", "isha.bose@college.edu", "7012345678", "MBA", "1", "2026-03-10", "active", "yes"],
    ]
    with open(os.path.join("data", "sample_import.csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"Seeded {len(club.members)} members and {len(club.events)} events.")


if __name__ == "__main__":
    main()

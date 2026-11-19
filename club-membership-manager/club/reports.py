"""Turning club numbers into text, Markdown and CSV."""
import csv
import os
from datetime import datetime


def _bar(count, biggest, width=20):
    if biggest == 0:
        return ""
    return "#" * max(1, round(count / biggest * width)) if count else ""


def summary_text(club):
    s = club.summary()
    lines = []
    add = lines.append
    add("CLUB SUMMARY")
    add("=" * 44)
    add(f"Total members      : {s['total_members']}")
    for status, n in sorted(s["by_status"].items()):
        add(f"  {status:<10}       : {n}")
    add(f"Dues paid          : {s['dues_paid']} ({s['dues_rate']:.1f}%)")
    add(f"Average year       : {s['avg_year']:.2f}")
    add(f"Events             : {s['total_events']}")
    add(f"Registrations      : {s['total_registrations']}")
    add(f"Avg seat fill rate : {s['avg_fill_rate']:.1f}%")
    add("")
    add("Members by department")
    add("-" * 44)
    biggest = max(s["by_department"].values(), default=0)
    for dept, n in s["by_department"].items():
        add(f"  {dept:<6} {n:>3}  {_bar(n, biggest)}")
    add("")
    add("Members by year")
    add("-" * 44)
    biggest = max(s["by_year"].values(), default=0)
    for yr, n in s["by_year"].items():
        add(f"  Year {yr} {n:>3}  {_bar(n, biggest)}")
    add("")
    add("Joining trend (members per month)")
    add("-" * 44)
    biggest = max(s["joins_by_month"].values(), default=0)
    for month, n in s["joins_by_month"].items():
        add(f"  {month} {n:>3}  {_bar(n, biggest)}")
    if s["top_events"]:
        add("")
        add("Most popular events")
        add("-" * 44)
        for title, n in s["top_events"]:
            add(f"  {title:<32} {n:>3}")
    if s["top_attendees"]:
        add("")
        add("Most active members")
        add("-" * 44)
        for name, n in s["top_attendees"]:
            add(f"  {name:<32} {n:>3} events")
    return "\n".join(lines)


def summary_markdown(club):
    s = club.summary()
    out = [f"# Club Summary", f"_Generated {datetime.now():%Y-%m-%d %H:%M}_", ""]
    out += ["| Metric | Value |", "|---|---|",
            f"| Total members | {s['total_members']} |",
            f"| Dues paid | {s['dues_paid']} ({s['dues_rate']:.1f}%) |",
            f"| Average year | {s['avg_year']:.2f} |",
            f"| Events | {s['total_events']} |",
            f"| Registrations | {s['total_registrations']} |",
            f"| Average seat fill | {s['avg_fill_rate']:.1f}% |", ""]
    out += ["## Members by department", "", "| Department | Members |", "|---|---|"]
    out += [f"| {d} | {n} |" for d, n in s["by_department"].items()]
    out += ["", "## Members by status", "", "| Status | Members |", "|---|---|"]
    out += [f"| {k} | {n} |" for k, n in sorted(s["by_status"].items())]
    out += ["", "## Joining trend", "", "| Month | New members |", "|---|---|"]
    out += [f"| {k} | {n} |" for k, n in s["joins_by_month"].items()]
    out += ["", "## Warnings", ""]
    warns = club.warnings()
    out += [f"- {w}" for w in warns] or ["- None"]
    return "\n".join(out) + "\n"


def audit_log(club):
    lines = [f"AUDIT LOG  {datetime.now():%Y-%m-%d %H:%M:%S}", "-" * 50]
    lines.append(f"{len(club.members)} members, {len(club.events)} events")
    lines.append("")
    lines.append("Warnings:")
    warns = club.warnings()
    lines += [f"  * {w}" for w in warns] or ["  (none)"]
    lines.append("")
    lines.append("Event registrations:")
    for e in club.events.values():
        names = ", ".join(club.members[a].name for a in e.attendees if a in club.members) or "-"
        lines.append(f"  {e.event_id} {e.title} ({e.date}) [{len(e.attendees)}/{e.capacity}]: {names}")
    return "\n".join(lines) + "\n"


def export_all(club, folder="exports"):
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = {
        "md": os.path.join(folder, f"summary_{stamp}.md"),
        "txt": os.path.join(folder, f"audit_{stamp}.txt"),
        "csv": os.path.join(folder, f"members_{stamp}.csv"),
    }
    with open(paths["md"], "w", encoding="utf-8") as f:
        f.write(summary_markdown(club))
    with open(paths["txt"], "w", encoding="utf-8") as f:
        f.write(audit_log(club))
    with open(paths["csv"], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["member_id", "name", "email", "phone", "department", "year",
                    "join_date", "status", "dues_paid", "events_attended"])
        for m in club.members.values():
            w.writerow([m.member_id, m.name, m.email, m.phone, m.department, m.year,
                        m.join_date, m.status, "yes" if m.dues_paid else "no",
                        club.events_attended(m.member_id)])
    return list(paths.values())

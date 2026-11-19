import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from club import storage, validation as v
from club.logic import Club, ClubError


def make_club():
    c = Club()
    c.add_member("Asha Rao", "asha@college.edu", "9876543210", "CSE", 2, "2026-01-01", "active", True)
    c.add_member("Ben Iyer", "ben@college.edu", "9123456780", "ECE", 3, "2026-01-02", "inactive", False)
    return c


class ValidationTests(unittest.TestCase):
    def test_phone_formats(self):
        self.assertEqual(v.clean_phone("+91 98765-43210"), "9876543210")
        with self.assertRaises(v.ValidationError):
            v.clean_phone("12345")

    def test_year_bounds(self):
        self.assertEqual(v.clean_year("4"), 4)
        for bad in ("0", "5", "x", ""):
            with self.assertRaises(v.ValidationError):
                v.clean_year(bad)

    def test_email_and_date(self):
        self.assertEqual(v.clean_email("  A@B.com "), "a@b.com")
        with self.assertRaises(v.ValidationError):
            v.clean_email("nope")
        with self.assertRaises(v.ValidationError):
            v.clean_join_date("2999-01-01")
        with self.assertRaises(v.ValidationError):
            v.clean_date("14/03/2026")


class LogicTests(unittest.TestCase):
    def test_duplicate_email_rejected(self):
        c = make_club()
        with self.assertRaises(ClubError):
            c.add_member("Other", "asha@college.edu", "9876543210", "CSE", 1, "2026-01-01")

    def test_capacity_and_inactive(self):
        c = make_club()
        c.add_member("Cara Das", "cara@college.edu", "9000000001", "IT", 1, "2026-01-03")
        e = c.add_event("Tiny Talk", "2030-01-01", "social", 1)
        c.register(e.event_id, "M001")
        with self.assertRaises(ClubError):
            c.register(e.event_id, "M003")      # full
        with self.assertRaises(ClubError):
            c.register(e.event_id, "M002")      # inactive
        with self.assertRaises(ClubError):
            c.register(e.event_id, "M001")      # duplicate

    def test_remove_member_clears_registrations(self):
        c = make_club()
        e = c.add_event("Talk", "2030-01-01", "social", 5)
        c.register(e.event_id, "M001")
        c.remove_member("M001")
        self.assertEqual(e.attendees, [])

    def test_search_filters(self):
        c = make_club()
        self.assertEqual(len(c.search("asha")), 1)
        self.assertEqual(len(c.search(department="ECE")), 1)
        self.assertEqual(len(c.search(status="active")), 1)

    def test_summary_numbers(self):
        s = make_club().summary()
        self.assertEqual(s["total_members"], 2)
        self.assertEqual(s["dues_paid"], 1)
        self.assertAlmostEqual(s["avg_year"], 2.5)

    def test_empty_summary_does_not_crash(self):
        self.assertEqual(Club().summary()["total_members"], 0)


class StorageTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.json")
            c = make_club()
            storage.save(c.members, c.events, p)
            members, events, notes = storage.load(p)
            self.assertEqual(len(members), 2)

    def test_corrupt_file_recovers(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.json")
            with open(p, "w") as f:
                f.write("{ this is not json")
            members, events, notes = storage.load(p)
            self.assertEqual(members, {})
            self.assertTrue(notes)
            self.assertTrue(any(n.startswith("x.json.corrupt") for n in os.listdir(d)))

    def test_missing_file(self):
        members, events, notes = storage.load("/nonexistent/nowhere.json")
        self.assertEqual((members, events), ({}, {}))

    def test_bad_record_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.json")
            with open(p, "w") as f:
                json.dump({"members": [{"oops": 1}], "events": []}, f)
            members, _, notes = storage.load(p)
            self.assertEqual(members, {})
            self.assertTrue(notes)


class ImportTests(unittest.TestCase):
    def test_import_logs_bad_rows(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "in.csv")
            with open(p, "w") as f:
                f.write("name,email,phone,department,year,join_date\n")
                f.write("Good One,good@x.com,9876543210,CSE,2,2026-01-01\n")
                f.write("Bad Year,bad@x.com,9876543210,CSE,9,2026-01-01\n")
            c = Club()
            added, errors = c.import_csv(p)
            self.assertEqual(added, 1)
            self.assertEqual(len(errors), 1)
            self.assertIn("row 3", errors[0])


if __name__ == "__main__":
    unittest.main()

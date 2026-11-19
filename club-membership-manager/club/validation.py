"""Input cleaning. Every checker either returns a clean value or raises ValidationError."""
import re
from datetime import date, datetime

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
STATUSES = ("active", "inactive", "alumni")
DEPARTMENTS = ("CSE", "ECE", "EEE", "MECH", "CIVIL", "IT", "MBA", "OTHER")
CATEGORIES = ("technical", "cultural", "sports", "workshop", "social")


class ValidationError(ValueError):
    pass


class Cancelled(Exception):
    """Raised when the user types 'cancel' at a prompt."""


def clean_name(raw):
    name = " ".join(str(raw).split())
    if not 2 <= len(name) <= 60:
        raise ValidationError("Name must be between 2 and 60 characters.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", name):
        raise ValidationError("Name can only contain letters, spaces, . ' and -")
    return name


def clean_email(raw):
    email = str(raw).strip().lower()
    if not EMAIL_RE.match(email):
        raise ValidationError("That doesn't look like an email (try name@college.edu).")
    return email


def clean_phone(raw):
    digits = re.sub(r"[\s\-()]", "", str(raw))
    if digits.startswith("+91"):
        digits = digits[3:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if not re.fullmatch(r"[6-9]\d{9}", digits):
        raise ValidationError("Phone must be a 10-digit mobile number starting with 6-9.")
    return digits


def clean_department(raw):
    dept = str(raw).strip().upper()
    if dept not in DEPARTMENTS:
        raise ValidationError("Department must be one of: " + ", ".join(DEPARTMENTS))
    return dept


def clean_year(raw):
    try:
        year = int(str(raw).strip())
    except ValueError:
        raise ValidationError("Year must be a whole number.")
    if not 1 <= year <= 4:
        raise ValidationError("Year must be between 1 and 4.")
    return year


def clean_status(raw):
    status = str(raw).strip().lower()
    if status not in STATUSES:
        raise ValidationError("Status must be one of: " + ", ".join(STATUSES))
    return status


def clean_category(raw):
    cat = str(raw).strip().lower()
    if cat not in CATEGORIES:
        raise ValidationError("Category must be one of: " + ", ".join(CATEGORIES))
    return cat


def clean_date(raw, allow_future=True):
    try:
        d = datetime.strptime(str(raw).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Use the date format YYYY-MM-DD (e.g. 2026-03-14).")
    if not 2000 <= d.year <= 2100:
        raise ValidationError("Year in the date looks wrong.")
    if not allow_future and d > date.today():
        raise ValidationError("Date can't be in the future.")
    return d.isoformat()


def clean_join_date(raw):
    return clean_date(raw, allow_future=False)


def clean_capacity(raw):
    try:
        cap = int(str(raw).strip())
    except ValueError:
        raise ValidationError("Capacity must be a whole number.")
    if not 1 <= cap <= 500:
        raise ValidationError("Capacity must be between 1 and 500.")
    return cap


def clean_title(raw):
    title = " ".join(str(raw).split())
    if not 3 <= len(title) <= 80:
        raise ValidationError("Title must be 3-80 characters.")
    return title


def clean_yes_no(raw):
    v = str(raw).strip().lower()
    if v in ("y", "yes", "true", "1", "paid"):
        return True
    if v in ("n", "no", "false", "0", "unpaid"):
        return False
    raise ValidationError("Please answer y or n.")


def ask(prompt, checker, default=None):
    """Keep asking until the checker accepts the answer. 'cancel' backs out."""
    while True:
        try:
            raw = input(prompt).strip()
        except EOFError:
            raise Cancelled()
        if raw.lower() == "cancel":
            raise Cancelled()
        if raw == "" and default is not None:
            return default
        try:
            return checker(raw)
        except ValidationError as err:
            print(f"  ! {err}")

import re
from datetime import date

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def is_valid_email(value):
    return re.match(EMAIL_PATTERN, str(value)) is not None


def is_valid_isbn(value):
    digits = str(value).replace("-", "")
    return digits.isdigit() and len(digits) in (10, 13)


def is_valid_date(value):
    try:
        date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def is_valid_member_type(value):
    return value in ("student", "staff")

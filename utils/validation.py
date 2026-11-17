import re
from datetime import date


def check(value, kind):
    if kind == "email":
        return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(value)) is not None
    if kind == "isbn":
        digits = str(value).replace("-", "")
        return digits.isdigit() and len(digits) in (10, 13)
    if kind == "date":
        try:
            date.fromisoformat(str(value))
            return True
        except ValueError:
            return False
    if kind == "member_type":
        return value in ("student", "staff")
    return False
"""Library fine rules: late returns cost a fixed amount per day overdue."""
from datetime import date

FINE_PER_DAY = 0.50


def days_late(due_date: str, today: date | None = None) -> int:
    """Days past the due date (negative while the loan is not yet due)."""
    today = today or date.today()
    return (today - date.fromisoformat(due_date)).days


def late_fine(due_date: str, today: date | None = None) -> float:
    """Fine accrued for a loan with this due date, returned or checked as of `today`."""
    return max(0, days_late(due_date, today)) * FINE_PER_DAY


def balance_owed(due_date: str, returned: bool, fine: float, fine_paid: bool, today: date | None = None) -> float:
    """What a single loan currently costs its member.

    Open loans owe the fine accrued so far; returned loans owe their stored fine until it is paid.
    """
    if not returned:
        return late_fine(due_date, today)
    if not fine_paid:
        return fine
    return 0.0

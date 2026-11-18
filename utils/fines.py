from datetime import date

FINE_PER_DAY = 0.50


def days_late(due_date):
    return (date.today() - date.fromisoformat(due_date)).days


def fine_for(due_date):
    return max(0, days_late(due_date)) * FINE_PER_DAY


def money(amount):
    return round(float(amount), 2)


def current_fine(loan):
    """The fine so far: still growing while the book is out, fixed once it is returned."""
    if loan["returned"] == 0:
        return fine_for(loan["due_date"])
    return loan["fine"]


def amount_owed(loan):
    """What the member still has to pay for this loan."""
    if loan["returned"] == 0:
        return fine_for(loan["due_date"])
    if loan["fine_paid"] == 0:
        return loan["fine"]
    return 0


def total_owed(loans):
    total = 0
    for loan in loans:
        total += amount_owed(loan)
    return total

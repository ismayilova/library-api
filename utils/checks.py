"""Yes/no questions about books, members and loans.

Each function only answers a question. Raising an error (or not) is up to the service.
"""

from utils import fines

LOAN_LIMITS = {"student": 3, "staff": 5}
DEFAULT_LOAN_LIMIT = LOAN_LIMITS["student"]
MAX_RENEWALS = 1


def is_available(book):
    return book["available"] != 0


def is_open(loan):
    """True while the book has not been returned."""
    return loan["returned"] == 0


def is_overdue(loan):
    return is_open(loan) and fines.days_late(loan["due_date"]) > 0


def has_renewals_left(loan):
    return loan["renewals"] < MAX_RENEWALS


def has_fine_to_pay(loan):
    return loan["fine"] > 0 and loan["fine_paid"] == 0


def has_unpaid_fines(loans):
    return fines.total_owed(loans) > 0


def count_open_loans(loans):
    count = 0
    for loan in loans:
        if is_open(loan):
            count += 1
    return count


def loan_limit(member):
    return LOAN_LIMITS.get(member["type"], DEFAULT_LOAN_LIMIT)


def loans_remaining(member, loans):
    return loan_limit(member) - count_open_loans(loans)


def has_reached_loan_limit(member, loans):
    return loans_remaining(member, loans) <= 0

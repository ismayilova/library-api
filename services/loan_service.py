from datetime import date, timedelta

import notifications
from errors import bad_request, conflict, not_found
from repositories import book_repository, loan_repository, member_repository
from utils import checks, fines, validation

LOAN_DAYS = 14
RENEWAL_DAYS = 14


def list_loans(only_overdue):
    loans = loan_repository.list_loans()
    if only_overdue:
        loans = [loan for loan in loans if checks.is_overdue(loan)]
    return loans


def get_loan(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        raise not_found("loan not found")
    return loan


def create_loan(data):
    if not data.get("book_id") or not data.get("member_id"):
        raise bad_request("book_id and member_id are required")
    if data.get("due_date") and not validation.is_valid_date(data["due_date"]):
        raise bad_request("invalid due_date")

    book = book_repository.get_book(data["book_id"])
    if book is None:
        raise not_found("book not found")
    member = member_repository.get_member(data["member_id"])
    if member is None:
        raise not_found("member not found")
    if not checks.is_available(book):
        raise conflict("book is not available")

    member_loans = loan_repository.list_loans_for_member(member["id"])
    if checks.has_unpaid_fines(member_loans):
        raise conflict("member has unpaid fines")
    if checks.has_reached_loan_limit(member, member_loans):
        raise conflict("loan limit reached")

    today = date.today()
    due_date = data.get("due_date") or (today + timedelta(days=LOAN_DAYS)).isoformat()
    loan = loan_repository.create_loan(book["id"], member["id"], due_date, today.isoformat())

    notifications.send_email(member["email"], "Book checked out", "You checked out " + book["title"])
    return loan


def return_book(loan_id):
    loan = get_loan(loan_id)
    if not checks.is_open(loan):
        raise conflict("loan already returned")

    fine = fines.fine_for(loan["due_date"])
    updated = loan_repository.mark_returned(loan_id, loan["book_id"], fine)

    member = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])
    notifications.send_email(
        member["email"],
        "Book returned",
        "You returned " + book["title"] + ". Fine: $" + str(fines.money(fine)),
    )
    return updated


def renew_loan(loan_id):
    loan = get_loan(loan_id)
    if not checks.is_open(loan):
        raise conflict("loan already returned")
    if checks.is_overdue(loan):
        raise conflict("overdue loans cannot be renewed")
    if not checks.has_renewals_left(loan):
        raise conflict("loan was already renewed")

    new_due = (date.fromisoformat(loan["due_date"]) + timedelta(days=RENEWAL_DAYS)).isoformat()
    updated = loan_repository.extend_loan(loan_id, new_due)

    member = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])
    notifications.send_email(member["email"], "Loan renewed", "You renewed " + book["title"])
    return updated


def pay_fine(loan_id):
    loan = get_loan(loan_id)
    if checks.is_open(loan):
        raise conflict("return the book before paying")
    if not checks.has_fine_to_pay(loan):
        raise conflict("no fine to pay")

    updated = loan_repository.mark_fine_paid(loan_id)

    member = member_repository.get_member(loan["member_id"])
    notifications.send_email(
        member["email"], "Fine paid", "We received $" + str(fines.money(loan["fine"]))
    )
    return updated

from datetime import date, timedelta

from repositories import book_repository
from repositories import loan_repository
from repositories import member_repository
from core import fines
from core import notifications
from core import validation
from core.errors import bad_request, not_found, conflict

LOAN_DAYS = 14
STUDENT_LIMIT = 3
STAFF_LIMIT = 5
MAX_RENEWALS = 1


def amount_owed(loan):
    if not loan.returned:
        return fines.fine_for(loan.due_date)
    return 0 if loan.fine_paid else loan.fine


def total_owed(loans):
    return sum(amount_owed(loan) for loan in loans)


def count_open_loans(loans):
    return sum(1 for loan in loans if not loan.returned)


def loan_limit(member):
    return STAFF_LIMIT if member.type == "staff" else STUDENT_LIMIT


def current_fine(loan):
    return loan.fine if loan.returned else fines.fine_for(loan.due_date)


def is_overdue(loan):
    return not loan.returned and fines.days_late(loan.due_date) > 0


def list_loans(only_overdue):
    allLoans = loan_repository.list_loans()
    return [loan for loan in allLoans if is_overdue(loan)] if only_overdue else allLoans


def get_loan(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        raise not_found("loan not found")
    return loan


def create_loan(data):
    bookId, memberId, dueDate = data.get("book_id"), data.get("member_id"), data.get("due_date")

    if not bookId or not memberId:
        raise bad_request("book_id and member_id are required")
    if dueDate and not validation.is_valid_date(dueDate):
        raise bad_request("invalid due_date")

    book = book_repository.get_book(bookId)
    if book is None:
        raise not_found("book not found")
    member = member_repository.get_member(memberId)
    if member is None:
        raise not_found("member not found")
    if not book.available:
        raise conflict("book is not available")

    memberLoans = loan_repository.list_loans_for_member(memberId)
    if total_owed(memberLoans) > 0:
        raise conflict("member has unpaid fines")
    if count_open_loans(memberLoans) >= loan_limit(member):
        raise conflict("loan limit reached")

    today = date.today()
    dueDate = dueDate or (today + timedelta(days=LOAN_DAYS)).isoformat()
    loan = loan_repository.create_loan(bookId, memberId, dueDate, today.isoformat())

    notifications.send_email(member.email, "Book checked out", "You checked out " + book.title)
    return loan


def return_book(loan_id):
    loan = get_loan(loan_id)
    if loan.returned:
        raise conflict("loan already returned")

    fine = fines.fine_for(loan.due_date)
    updatedLoan = loan_repository.mark_returned(loan_id, loan.book_id, fine)

    member = member_repository.get_member(loan.member_id)
    book = book_repository.get_book(loan.book_id)
    notifications.send_email(
        member.email, "Book returned", f"You returned {book.title}. Fine: ${fines.money(fine)}"
    )
    return updatedLoan


def renew_loan(loan_id):
    loan = get_loan(loan_id)
    if loan.returned:
        raise conflict("loan already returned")

    dueDate = date.fromisoformat(loan.due_date)
    if dueDate < date.today():
        raise conflict("overdue loans cannot be renewed")
    if loan.renewals >= MAX_RENEWALS:
        raise conflict("loan was already renewed")

    updatedLoan = loan_repository.extend_loan(loan_id, (dueDate + timedelta(days=LOAN_DAYS)).isoformat())

    member = member_repository.get_member(loan.member_id)
    book = book_repository.get_book(loan.book_id)
    notifications.send_email(member.email, "Loan renewed", "You renewed " + book.title)
    return updatedLoan


def pay_fine(loan_id):
    loan = get_loan(loan_id)
    if not loan.returned:
        raise conflict("return the book before paying")
    if loan.fine <= 0 or loan.fine_paid:
        raise conflict("no fine to pay")

    updatedLoan = loan_repository.mark_fine_paid(loan_id)

    member = member_repository.get_member(loan.member_id)
    notifications.send_email(member.email, "Fine paid", f"We received ${fines.money(loan.fine)}")
    return updatedLoan

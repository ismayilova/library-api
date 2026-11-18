from datetime import date, timedelta

from repositories import book_repo, loan_repo, member_repo
from helpers import notifier
from helpers.errors import ServiceError
from helpers.validators import check, money

FINE_PER_DAY = 0.5


def days_late(due_date):
    return (date.today() - date.fromisoformat(due_date)).days


def loan_limit(member_type):
    if member_type == "staff":
        return 5
    return 3


def calculate_balance(loans):
    """Returns (amount_owed, open_loan_count) for a list of loan rows."""
    owed = 0
    open_loans = 0
    for loan in loans:
        if loan[4] == 0:
            open_loans += 1
            late = days_late(loan[3])
            if late > 0:
                owed += late * FINE_PER_DAY
        elif loan[6] == 0:
            owed += loan[5]
    return owed, open_loans


def loan_to_dict(loan):
    return {
        "id": loan[0],
        "book_id": loan[1],
        "member_id": loan[2],
        "due_date": loan[3],
        "returned": bool(loan[4]),
        "fine": money(loan[5]),
        "fine_paid": bool(loan[6]),
        "renewals": loan[7],
        "checked_out": loan[8],
    }


def list_loans(overdue_only=False):
    rows = loan_repo.find_all()
    result = []
    for loan in rows:
        current_fine = loan[5]
        late = days_late(loan[3])
        if loan[4] == 0:
            current_fine = max(0, late) * 0.50
        if overdue_only and (loan[4] == 1 or late <= 0):
            continue
        item = loan_to_dict(loan)
        item["current_fine"] = money(current_fine)
        result.append(item)
    return result


def get_loan(loan_id):
    loan = loan_repo.find_by_id(loan_id)
    if loan is None:
        raise ServiceError("loan not found", 404)
    current_fine = loan[5]
    if loan[4] == 0:
        current_fine = max(0, days_late(loan[3])) * 0.50
    item = loan_to_dict(loan)
    item["current_fine"] = money(current_fine)
    return item


def create_loan(data):
    if not data.get("book_id") or not data.get("member_id"):
        raise ServiceError("book_id and member_id are required", 400)
    if data.get("due_date") and not check(data["due_date"], "date"):
        raise ServiceError("invalid due_date", 400)

    book = book_repo.find_by_id(data["book_id"])
    if book is None:
        raise ServiceError("book not found", 404)
    member = member_repo.find_by_id(data["member_id"])
    if member is None:
        raise ServiceError("member not found", 404)
    if book[4] == 0:
        raise ServiceError("book is not available", 409)

    rows = loan_repo.find_by_member(data["member_id"])
    owed, open_loans = calculate_balance(rows)
    if owed > 0:
        raise ServiceError("member has unpaid fines", 409)
    if open_loans >= loan_limit(member[3]):
        raise ServiceError("loan limit reached", 409)

    today = date.today()
    due_date = data.get("due_date") or (today + timedelta(days=14)).isoformat()
    loan = loan_repo.create(data["book_id"], data["member_id"], due_date, today.isoformat())

    notifier.notify("checkout", book[1], member[2])
    return loan_to_dict(loan)


def return_book(loan_id):
    loan = loan_repo.find_by_id(loan_id)
    if loan is None:
        raise ServiceError("loan not found", 404)
    if loan[4] == 1:
        raise ServiceError("loan already returned", 409)

    fine = max(0, days_late(loan[3])) * FINE_PER_DAY
    loan_repo.mark_returned(loan_id, loan[1], fine)

    member = member_repo.find_by_id(loan[2])
    book = book_repo.find_by_id(loan[1])
    updated = loan_repo.find_by_id(loan_id)

    notifier.notify_return(member[2], book[1], fine)
    return loan_to_dict(updated)


def renew_loan(loan_id):
    loan = loan_repo.find_by_id(loan_id)
    if loan is None:
        raise ServiceError("loan not found", 404)
    if loan[4] == 1:
        raise ServiceError("loan already returned", 409)
    if date.fromisoformat(loan[3]) < date.today():
        raise ServiceError("overdue loans cannot be renewed", 409)
    if loan[7] >= 1:
        raise ServiceError("loan was already renewed", 409)

    new_due = (date.fromisoformat(loan[3]) + timedelta(days=14)).isoformat()
    loan_repo.renew(loan_id, new_due)

    member = member_repo.find_by_id(loan[2])
    book = book_repo.find_by_id(loan[1])
    updated = loan_repo.find_by_id(loan_id)

    notifier.notify("renew", book[1], member[2])
    return loan_to_dict(updated)


def pay_fine(loan_id):
    loan = loan_repo.find_by_id(loan_id)
    if loan is None:
        raise ServiceError("loan not found", 404)
    if loan[4] == 0:
        raise ServiceError("return the book before paying", 409)
    if loan[5] <= 0 or loan[6] == 1:
        raise ServiceError("no fine to pay", 409)

    loan_repo.mark_fine_paid(loan_id)

    member = member_repo.find_by_id(loan[2])
    updated = loan_repo.find_by_id(loan_id)

    notifier.notify_fine_paid(member[2], loan[5])
    return loan_to_dict(updated)
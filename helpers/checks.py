from datetime import date

from helpers.errors import ServiceError


def loan_limit(member_type):
    if member_type == "staff":
        return 5
    return 3


def check_book_deletable(book):
    if book[4] == 0:
        raise ServiceError("book is on loan", 409)


def check_book_available(book):
    if book[4] == 0:
        raise ServiceError("book is not available", 409)


def check_no_unpaid_fines(owed):
    if owed > 0:
        raise ServiceError("member has unpaid fines", 409)


def check_loan_limit(open_loans, member_type):
    if open_loans >= loan_limit(member_type):
        raise ServiceError("loan limit reached", 409)


def check_can_return(loan):
    if loan[4] == 1:
        raise ServiceError("loan already returned", 409)


def check_can_renew(loan):
    if loan[4] == 1:
        raise ServiceError("loan already returned", 409)
    if date.fromisoformat(loan[3]) < date.today():
        raise ServiceError("overdue loans cannot be renewed", 409)
    if loan[7] >= 1:
        raise ServiceError("loan was already renewed", 409)


def check_can_pay_fine(loan):
    if loan[4] == 0:
        raise ServiceError("return the book before paying", 409)
    if loan[5] <= 0 or loan[6] == 1:
        raise ServiceError("no fine to pay", 409)
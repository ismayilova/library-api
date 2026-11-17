from errors import error
from utils.fines import amount_owed


def loan_limit(member_type):
    return 5 if member_type == "staff" else 3


def can_borrow(member, loans):
    if amount_owed(loans) > 0:
        error("member has unpaid fines", 409)
    open_loans = sum(1 for loan in loans if not loan[4])
    if open_loans >= loan_limit(member[3]):
        error("loan limit reached", 409)
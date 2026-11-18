from repositories import loan_repo, member_repo
from services.loan_service import calculate_balance, loan_limit
from helpers.errors import ServiceError
from helpers.validators import check, money


def member_to_dict(r):
    return {"id": r[0], "name": r[1], "email": r[2], "type": r[3]}


def list_members():
    return [member_to_dict(r) for r in member_repo.find_all()]


def get_member(member_id):
    r = member_repo.find_by_id(member_id)
    if r is None:
        raise ServiceError("member not found", 404)
    return member_to_dict(r)


def create_member(data):
    if not data.get("name"):
        raise ServiceError("name is required", 400)
    if not check(data.get("email"), "email"):
        raise ServiceError("invalid email", 400)
    member_type = data.get("type", "student")
    if not check(member_type, "member_type"):
        raise ServiceError("type must be student or staff", 400)
    if member_repo.find_by_email(data["email"]) is not None:
        raise ServiceError("email already registered", 409)
    r = member_repo.create(data["name"], data["email"], member_type)
    return member_to_dict(r)


def delete_member(member_id):
    if member_repo.find_by_id(member_id) is None:
        raise ServiceError("member not found", 404)
    member_repo.delete(member_id)


def get_member_loans(member_id):
    m = member_repo.find_by_id(member_id)
    if m is None:
        raise ServiceError("member not found", 404)
    rows = loan_repo.find_by_member(member_id)
    owed, open_loans = calculate_balance(rows)
    loans = []
    for loan in rows:
        loans.append(
            {
                "id": loan[0],
                "book_id": loan[1],
                "due_date": loan[3],
                "returned": bool(loan[4]),
                "fine": money(loan[5]),
                "fine_paid": bool(loan[6]),
            }
        )
    remaining = loan_limit(m[3]) - open_loans
    return {"loans": loans, "total_owed": money(owed), "loans_remaining": remaining}
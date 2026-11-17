from repositories import members as repo
from repositories import loans
from errors import error
from utils.validation import check
from utils.fines import money, amount_owed
from utils.checks import loan_limit


def to_dict(row):
    return {"id": row[0], "name": row[1], "email": row[2], "type": row[3]}


def list_members():
    return [to_dict(row) for row in repo.all_members()]


def get_member(member_id):
    row = repo.get(member_id)
    if row is None:
        error("member not found", 404)
    return to_dict(row)


def create_member(data):
    if not data.get("name"):
        error("name is required", 400)
    if not check(data.get("email"), "email"):
        error("invalid email", 400)
    member_type = data.get("type", "student")
    if not check(member_type, "member_type"):
        error("type must be student or staff", 400)
    if repo.find_email(data["email"]):
        error("email already registered", 409)
    return to_dict(repo.add(data["name"], data["email"], member_type))


def member_loans(member_id):
    member = repo.get(member_id)
    if member is None:
        error("member not found", 404)
    rows = loans.for_member(member_id)
    items = []
    for loan in rows:
        items.append({"id": loan[0], "book_id": loan[1], "due_date": loan[3], "returned": bool(loan[4]), "fine": money(loan[5]), "fine_paid": bool(loan[6])})
    open_count = sum(1 for loan in rows if not loan[4])
    return {"loans": items, "total_owed": amount_owed(rows), "loans_remaining": loan_limit(member[3]) - open_count}
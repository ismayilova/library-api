from datetime import date, timedelta
from database import connect
from repositories import loans as repo
from repositories import books, members
from errors import error
from utils.validation import check
from utils.checks import can_borrow
from utils.fines import money, fine_for, amount_owed
from notifications import notify


def to_dict(loan, current=False):
    item = {"id": loan[0], "book_id": loan[1], "member_id": loan[2], "due_date": loan[3], "returned": bool(loan[4]), "fine": money(loan[5]), "fine_paid": bool(loan[6]), "renewals": loan[7], "checked_out": loan[8]}
    if current:
        item["current_fine"] = money(loan[5]) if loan[4] else fine_for(loan[3])
    return item


def list_loans(overdue=False):
    rows = repo.all_loans()
    if overdue:
        rows = [r for r in rows if not r[4] and date.fromisoformat(r[3]) < date.today()]
    return [to_dict(r, True) for r in rows]


def get_loan(loan_id):
    loan = repo.get(loan_id)
    if loan is None:
        error("loan not found", 404)
    return to_dict(loan, True)


def create_loan(data):
    if not data.get("book_id") or not data.get("member_id"):
        error("book_id and member_id are required", 400)
    if data.get("due_date") and not check(data["due_date"], "date"):
        error("invalid due_date", 400)
    book = books.get(data["book_id"])
    if book is None:
        error("book not found", 404)
    member = members.get(data["member_id"])
    if member is None:
        error("member not found", 404)
    if not book[4]:
        error("book is not available", 409)
    can_borrow(member, repo.for_member(member[0]))
    today = date.today()
    due = data.get("due_date") or (today + timedelta(days=14)).isoformat()
    with connect() as db:
        loan_id = repo.add(book[0], member[0], due, today.isoformat(), db)
        books.set_available(book[0], False, db)
    notify(member[2], "Book checked out", "You checked out " + book[1])
    return to_dict(repo.get(loan_id))


def return_book(loan_id):
    loan = repo.get(loan_id)
    if loan is None:
        error("loan not found", 404)
    if loan[4]:
        error("loan already returned", 409)
    fine = fine_for(loan[3])
    with connect() as db:
        repo.mark_returned(loan_id, fine, db)
        books.set_available(loan[1], True, db)
    member = members.get(loan[2])
    book = books.get(loan[1])
    notify(member[2], "Book returned", "You returned " + book[1] + ". Fine: $" + str(money(fine)))
    return to_dict(repo.get(loan_id))


def renew_loan(loan_id):
    loan = repo.get(loan_id)
    if loan is None:
        error("loan not found", 404)
    if loan[4]:
        error("loan already returned", 409)
    if date.fromisoformat(loan[3]) < date.today():
        error("overdue loans cannot be renewed", 409)
    if loan[7] >= 1:
        error("loan was already renewed", 409)
    due = (date.fromisoformat(loan[3]) + timedelta(days=14)).isoformat()
    with connect() as db:
        repo.renew(loan_id, due, db)
    member = members.get(loan[2])
    book = books.get(loan[1])
    notify(member[2], "Loan renewed", "You renewed " + book[1])
    return to_dict(repo.get(loan_id))


def pay_fine(loan_id):
    loan = repo.get(loan_id)
    if loan is None:
        error("loan not found", 404)
    if not loan[4]:
        error("return the book before paying", 409)
    if loan[5] <= 0 or loan[6]:
        error("no fine to pay", 409)
    with connect() as db:
        repo.mark_paid(loan_id, db)
    member = members.get(loan[2])
    notify(member[2], "Fine paid", "We received $" + str(money(loan[5])))
    return to_dict(repo.get(loan_id))


def overdue_report():
    items = []
    total = 0
    for row in repo.overdue_rows():
        days = (date.today() - date.fromisoformat(row[3])).days
        if days > 0:
            fine = fine_for(row[3])
            total += fine
            items.append({"loan_id": row[0], "title": row[1], "member": row[2], "days_late": days, "fine": fine})
    return {"items": items, "total_fines": money(total)}


def summary_report():
    rows = repo.all_loans()
    return {"total_books": len(books.all_books()), "on_loan": sum(1 for row in rows if not row[4]), "fines_outstanding": amount_owed(rows)}
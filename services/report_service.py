from repositories import book_repository, loan_repository
from helpers.fines import FINE_PER_DAY, calculate_fine, days_late
from helpers.validators import money


def overdue_report():
    rows = loan_repository.find_open_with_details()
    items = []
    total = 0
    for r in rows:
        late = days_late(r[3])
        if late > 0:
            fine = late * FINE_PER_DAY
            total += fine
            items.append(
                {"loan_id": r[0], "title": r[1], "member": r[2], "days_late": late, "fine": money(fine)}
            )
    return {"items": items, "total_fines": money(total)}


def summary_report():
    total_books = book_repository.count()
    rows = loan_repository.find_all()
    on_loan = 0
    outstanding = 0
    for loan in rows:
        if loan[4] == 0:
            on_loan += 1
            outstanding += calculate_fine(loan[3])
        elif loan[6] == 0:
            outstanding += loan[5]
    return {"total_books": total_books, "on_loan": on_loan, "fines_outstanding": money(outstanding)}
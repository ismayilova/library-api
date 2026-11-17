from repositories import report_repository
from repositories import book_repository
from repositories import loan_repository
from services import loan_service
from core import fines


def overdue_report():
    items = [
        {
            "loan_id": row["id"],
            "title": row["title"],
            "member": row["name"],
            "days_late": fines.days_late(row["due_date"]),
            "fine": fines.money(fines.fine_for(row["due_date"])),
        }
        for row in report_repository.list_open_loans_with_details()
        if fines.days_late(row["due_date"]) > 0
    ]
    totalFines = sum(item["fine"] for item in items)
    return {"items": items, "total_fines": fines.money(totalFines)}


def summary_report():
    loans = loan_repository.list_loans()
    return {
        "total_books": book_repository.count_books(),
        "on_loan": loan_service.count_open_loans(loans),
        "fines_outstanding": fines.money(loan_service.total_owed(loans)),
    }

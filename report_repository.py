import db


def list_open_loans_with_details():
    conn = db.connect()
    rows = conn.execute(
        """
        SELECT loans.id AS loan_id, books.title AS title, members.name AS member, loans.due_date AS due_date
        FROM loans
        JOIN books ON books.id = loans.book_id
        JOIN members ON members.id = loans.member_id
        WHERE loans.returned = 0
        """
    ).fetchall()
    conn.close()
    return rows

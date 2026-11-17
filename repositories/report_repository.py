from core import db


def list_open_loans_with_details():
    conn = db.connect()
    sql = """
        SELECT loans.id, books.title, members.name, loans.due_date
        FROM loans
        JOIN books ON books.id = loans.book_id
        JOIN members ON members.id = loans.member_id
        WHERE loans.returned = 0
    """
    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows

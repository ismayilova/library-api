import db
from db import get_connection


def find_all():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM loans").fetchall()
    conn.close()
    return rows


def find_by_id(loan_id):
    conn = get_connection()
    loan = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    conn.close()
    return loan


def find_by_member(member_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM loans WHERE member_id = ?", (member_id,)).fetchall()
    conn.close()
    return rows


def create(book_id, member_id, due_date, checked_out):
    """Inserts the loan and marks the book unavailable in one transaction."""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO loans (book_id, member_id, due_date, checked_out) VALUES (?, ?, ?, ?)",
        (book_id, member_id, due_date, checked_out),
    )
    conn.execute("UPDATE books SET available = 0 WHERE id = ?", (book_id,))
    conn.commit()
    loan = conn.execute("SELECT * FROM loans WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return loan


def mark_returned(loan_id, book_id, fine):
    """Marks the loan returned and the book available in one transaction."""
    conn = get_connection()
    conn.execute("UPDATE loans SET returned = 1, fine = ? WHERE id = ?", (fine, loan_id))
    conn.execute("UPDATE books SET available = 1 WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()


def renew(loan_id, new_due):
    conn = get_connection()
    conn.execute(
        "UPDATE loans SET due_date = ?, renewals = renewals + 1 WHERE id = ?",
        (new_due, loan_id),
    )
    conn.commit()
    conn.close()


def mark_fine_paid(loan_id):
    conn = get_connection()
    conn.execute("UPDATE loans SET fine_paid = 1 WHERE id = ?", (loan_id,))
    conn.commit()
    conn.close()


def find_open_with_details():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT loans.id, books.title, members.name, loans.due_date
        FROM loans
        JOIN books ON books.id = loans.book_id
        JOIN members ON members.id = loans.member_id
        WHERE loans.returned = 0
        """
    ).fetchall()
    conn.close()
    return rows
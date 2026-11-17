from database import connect


def all_loans():
    with connect() as db:
        return db.execute("SELECT * FROM loans").fetchall()


def get(loan_id):
    with connect() as db:
        return db.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()


def for_member(member_id):
    with connect() as db:
        return db.execute("SELECT * FROM loans WHERE member_id = ?", (member_id,)).fetchall()


def add(book_id, member_id, due_date, today, db):
    cur = db.execute("INSERT INTO loans (book_id, member_id, due_date, checked_out) VALUES (?, ?, ?, ?)", (book_id, member_id, due_date, today))
    return cur.lastrowid


def mark_returned(loan_id, fine, db):
    db.execute("UPDATE loans SET returned = 1, fine = ? WHERE id = ?", (fine, loan_id))


def renew(loan_id, due_date, db):
    db.execute("UPDATE loans SET due_date = ?, renewals = renewals + 1 WHERE id = ?", (due_date, loan_id))


def mark_paid(loan_id, db):
    db.execute("UPDATE loans SET fine_paid = 1 WHERE id = ?", (loan_id,))


def overdue_rows():
    with connect() as db:
        return db.execute("SELECT loans.id, books.title, members.name, loans.due_date FROM loans JOIN books ON books.id = loans.book_id JOIN members ON members.id = loans.member_id WHERE loans.returned = 0").fetchall()

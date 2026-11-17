from database import connect


def all_books(available_only=False):
    with connect() as db:
        if available_only:
            return db.execute("SELECT * FROM books WHERE available = 1").fetchall()
        return db.execute("SELECT * FROM books").fetchall()


def get(book_id):
    with connect() as db:
        return db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()


def add(title, author, isbn):
    with connect() as db:
        cur = db.execute("INSERT INTO books (title, author, isbn, available) VALUES (?, ?, ?, 1)", (title, author, isbn))
        new_id = cur.lastrowid
    return get(new_id)


def delete(book_id):
    with connect() as db:
        db.execute("DELETE FROM books WHERE id = ?", (book_id,))


def set_available(book_id, available, db):
    db.execute("UPDATE books SET available = ? WHERE id = ?", (int(available), book_id))

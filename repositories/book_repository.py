from core import db
from models.book import Book


def list_books(only_available):
    conn = db.connect()
    if only_available:
        rows = conn.execute("SELECT * FROM books WHERE available = 1").fetchall()
    else:
        rows = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return [Book.from_row(row) for row in rows]


def get_book(book_id):
    conn = db.connect()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    return Book.from_row(book)


def create_book(title, author, isbn):
    conn = db.connect()
    cur = conn.execute("INSERT INTO books (title, author, isbn, available) VALUES (?, ?, ?, 1)", (title, author, isbn))
    conn.commit()
    newId = cur.lastrowid
    book = conn.execute("SELECT * FROM books WHERE id = ?", (newId,)).fetchone()
    conn.close()
    return Book.from_row(book)


def delete_book(book_id):
    conn = db.connect()
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()


def count_books():
    conn = db.connect()
    count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    conn.close()
    return count

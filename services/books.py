from repositories import books as repo
from errors import error
from utils.validation import check


def to_dict(row):
    return {"id": row[0], "title": row[1], "author": row[2], "isbn": row[3], "available": bool(row[4])}


def list_books(available=False):
    return [to_dict(row) for row in repo.all_books(available)]


def get_book(book_id):
    row = repo.get(book_id)
    if row is None:
        error("book not found", 404)
    return to_dict(row)


def create_book(data):
    if not data.get("title") or not data.get("author"):
        error("title and author are required", 400)
    if not check(data.get("isbn"), "isbn"):
        error("invalid isbn", 400)
    return to_dict(repo.add(data["title"], data["author"], data["isbn"]))


def delete_book(book_id):
    book = repo.get(book_id)
    if book is None:
        error("book not found", 404)
    if not book[4]:
        error("book is on loan", 409)
    repo.delete(book_id)

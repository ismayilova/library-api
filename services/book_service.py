from repositories import book_repository
from helpers.errors import ServiceError
from helpers.validators import check

def book_to_dict(r):
    return {"id": r[0], "title": r[1], "author": r[2], "isbn": r[3], "available": bool(r[4])}


def list_books(available_only=False):
    return [book_to_dict(r) for r in book_repository.find_all(available_only)]


def get_book(book_id):
    r = book_repository.find_by_id(book_id)
    if r is None:
        raise ServiceError("book not found", 404)
    return book_to_dict(r)


def create_book(data):
    if not data.get("title") or not data.get("author"):
        raise ServiceError("title and author are required", 400)
    if not check(data.get("isbn"), "isbn"):
        raise ServiceError("invalid isbn", 400)
    r = book_repository.create(data["title"], data["author"], data["isbn"])
    return book_to_dict(r)


def delete_book(book_id):
    r = book_repository.find_by_id(book_id)
    if r is None:
        raise ServiceError("book not found", 404)
    if r[4] == 0:
        raise ServiceError("book is on loan", 409)
    book_repository.delete(book_id)
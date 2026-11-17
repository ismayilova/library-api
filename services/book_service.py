from repositories import book_repository
from core import validation
from core.errors import bad_request, not_found, conflict


def list_books(only_available):
    return book_repository.list_books(only_available)


def get_book(book_id):
    book = book_repository.get_book(book_id)
    if book is None:
        raise not_found("book not found")
    return book


def create_book(data):
    title, author, isbn = data.get("title"), data.get("author"), data.get("isbn")
    if not title or not author:
        raise bad_request("title and author are required")
    if not validation.is_valid_isbn(isbn):
        raise bad_request("invalid isbn")
    return book_repository.create_book(title, author, isbn)


def delete_book(book_id):
    if not get_book(book_id).available:
        raise conflict("book is on loan")
    book_repository.delete_book(book_id)

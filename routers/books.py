from flask import Blueprint, request, jsonify
from services import books

books_router = Blueprint("books", __name__)

@books_router.get("/books")
def list_books():
    return jsonify(books.list_books(request.args.get("available") == "true"))

@books_router.get("/books/<int:book_id>")
def get_book(book_id):
    return jsonify(books.get_book(book_id))

@books_router.post("/books")
def create_book():
    return jsonify(books.create_book(request.get_json(silent=True) or {})), 201

@books_router.delete("/books/<int:book_id>")
def delete_book(book_id):
    books.delete_book(book_id)
    return "", 204

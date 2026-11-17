import os

from flask import Flask, jsonify

from routes import book_routes, member_routes, loan_routes, report_routes
from routes.swagger import swagger_bp
from core.db import init_db
from core.errors import LibraryError

app = Flask(__name__)

for blueprint in (swagger_bp, book_routes.bp, member_routes.bp, loan_routes.bp, report_routes.bp):
    app.register_blueprint(blueprint)


@app.errorhandler(LibraryError)
def handle_library_error(error):
    return jsonify({"error": error.message}), error.status


if not os.path.exists("library.db"):
    init_db()

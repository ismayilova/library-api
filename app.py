import os
from flask import Flask
from db import init_db
from routers.books import books_bp
from routers.members import members_bp
from routers.loans import loans_bp
from routers.reports import reports_bp
from helpers.errors import ServiceError, error_response

app = Flask(__name__)

app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(loans_bp)
app.register_blueprint(reports_bp)

@app.errorhandler(ServiceError)
def handle_service_error(e):
    return error_response(e.message, e.status)

if not os.path.exists("library.db"):
    init_db()
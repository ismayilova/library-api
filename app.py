import os

from flask import Flask

from db import init_db
from errors import register_error_handlers
from routers import book_router, loan_router, member_router, report_router

app = Flask(__name__)
app.register_blueprint(book_router.bp)
app.register_blueprint(member_router.bp)
app.register_blueprint(loan_router.bp)
app.register_blueprint(report_router.bp)
register_error_handlers(app)

if not os.path.exists("library.db"):
    init_db()

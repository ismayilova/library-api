import os
from flask import Flask, jsonify
from database import init_db
from errors import ApiError
from routers.books import books_router
from routers.members import members_router
from routers.loans import loans_router

app = Flask(__name__)
app.register_blueprint(books_router)
app.register_blueprint(members_router)
app.register_blueprint(loans_router)

@app.errorhandler(ApiError)
def handle_api_error(error):
    return jsonify({"error": error.message}), error.status_code

if not os.path.exists("library.db"):
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
from flask import jsonify


class LibraryError(Exception):
    """An error the API reports to the client as {"error": message} with an HTTP status."""

    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def api_error(message, status_code):
    """Build an error with a custom message and HTTP status code. Use it with `raise`."""
    return LibraryError(message, status_code)


def bad_request(message):
    return api_error(message, 400)


def not_found(message):
    return api_error(message, 404)


def conflict(message):
    return api_error(message, 409)


def register_error_handlers(app):
    @app.errorhandler(LibraryError)
    def handle_library_error(error):
        return jsonify({"error": error.message}), error.status_code

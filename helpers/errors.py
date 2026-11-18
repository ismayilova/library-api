from flask import jsonify

class ServiceError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status

def error_response(message, status):
    return jsonify({"error": message}), status
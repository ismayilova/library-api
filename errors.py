class ApiError(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code


def error(message, status_code):
    raise ApiError(message, status_code)
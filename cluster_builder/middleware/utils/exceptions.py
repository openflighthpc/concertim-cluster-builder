
# Custom Middleware Service Exceptions

from werkzeug.exceptions import HTTPException

class MiddlewareItemConflict(HTTPException):
    pass

class MiddlewareMissingRequiredField(HTTPException):
    pass

class MiddlewareMissingRequiredArgs(HTTPException):
    def __init__(self, *args):
        self.missing = args
    def __str__(self):
        return f"Missing required arguments for call : Missing [{self.missing}]"
    


class MiddlewareServiceError(Exception):
    def __init__(self, message):
        self.message = message

class MiddlewareAuthenticationError(Exception):
    def __init__(self, message):
        self.message = message


MIDDLEWARE_SERVICE_EXCEPTIONS = [
    MiddlewareItemConflict,
    MiddlewareMissingRequiredField,
    MiddlewareMissingRequiredArgs,
    MiddlewareServiceError
]

MIDDLEWARE_AUTHENTICATION_EXCEPTIONS = [
    MiddlewareAuthenticationError
]


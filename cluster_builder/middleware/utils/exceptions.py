
# Custom Middleware Service Exceptions


class MiddlewareItemConflict(Exception):
   
    def __init__(self, message, http_status = 409):
        self.message = message
        self.http_status = http_status

class MiddlewareMissingRequiredField(Exception):
   
    def __init__(self, message, http_status = 400):
        self.message = message
        self.http_status = http_status

class MiddlewareMissingRequiredArgs(Exception):
   
    def __init__(self, message, missing = None, http_status = 400):
        self.message = message
        self.http_status = http_status
        self.missing = missing

    def __str__(self):
        return f"Missing required arguments for call : Missing [{self.missing}]"
    
class MiddlewareServiceError(Exception):

    def __init__(self, message, http_status = 502):
        self.message = message
        self.http_status = http_status

class MiddlewareInsufficientCredits(Exception):

    def __init__(self, message, http_status = 400):
        self.message = message
        self.http_status = http_status

class MiddlewareAuthenticationError(Exception):

    def __init__(self, message, http_status = 401):
        self.message = message
        self.http_status = http_status


MIDDLEWARE_EXCEPTIONS = [
    MiddlewareItemConflict,
    MiddlewareMissingRequiredField,
    MiddlewareMissingRequiredArgs,
    MiddlewareServiceError,
    MiddlewareInsufficientCredits,
    MiddlewareAuthenticationError
]



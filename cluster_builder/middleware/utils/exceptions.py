# Custom Exceptions
class MiddlewareItemConflict(Exception):
    pass

class MissingRequiredField(Exception):
    pass

class MissingRequiredArgs(Exception):
    def __init__(self, *args):
        self.missing = args
    def __str__(self):
        return f"Missing required arguments for call : Missing [{self.missing}]"
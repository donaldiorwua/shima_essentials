class OrderCreationError(Exception):
    def __init__(self, errors: dict, message: str = "Validation failed"):
        self.errors = errors
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"{self.message}: {self.errors}"
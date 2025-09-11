class ApplicationError(Exception):
    """Base application error with user-friendly messaging."""

    def __init__(
        self,
        message: str,
        user_message: str = None,
        error_code: str = None,
        status_code: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message
        self.error_code = error_code
        self.status_code = status_code

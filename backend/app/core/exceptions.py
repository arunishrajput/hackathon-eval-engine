from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BadRequestError(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnprocessableError(HTTPException):
    def __init__(self, detail: str = "Unprocessable entity"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class EvaluationError(Exception):
    """Raised when evaluation pipeline encounters an unrecoverable error."""
    def __init__(self, message: str, submission_id: str = None):
        self.message = message
        self.submission_id = submission_id
        super().__init__(message)


class IngestionError(Exception):
    """Raised during repository ingestion failures."""
    pass


class AgentError(Exception):
    """Raised when an AI agent fails to produce a result."""
    def __init__(self, agent_id: str, message: str):
        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' failed: {message}")

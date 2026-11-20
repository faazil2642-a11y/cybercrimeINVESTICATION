from fastapi import HTTPException, status


class CyberTraceException(HTTPException):
    pass


class NotFoundError(CyberTraceException):
    def __init__(self, resource: str, resource_id: str = ""):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found: {resource_id}".strip(),
        )


class AccessDeniedError(CyberTraceException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationError(CyberTraceException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class ConflictError(CyberTraceException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class AINotConfiguredError(CyberTraceException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "AI provider not configured. Set GEMINI_API_KEY in your .env file "
                "to enable RAG investigation features. Non-AI features remain available."
            ),
        )

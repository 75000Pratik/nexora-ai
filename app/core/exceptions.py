class LLMServiceError(Exception):
    """Raised when the LLM provider returns an unusable response."""

    pass


class LLMServiceTimeoutError(LLMServiceError):
    """Raised when the LLM provider request times out."""

    pass

from typing import Any, Optional


class OrouterError(Exception):
    """Base class for all errors the CLI knows how to report cleanly."""

    exit_code = 1

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigError(OrouterError):
    """Missing/invalid configuration: API key, bad flag combination."""

    exit_code = 2


class ValidationError(OrouterError):
    """Bad user input: unreadable file, undetectable type, invalid args."""

    exit_code = 2


class ApiError(OrouterError):
    """The OpenRouter API or SDK call failed."""

    exit_code = 1


class PollTimeoutError(OrouterError):
    """A --wait poll loop exceeded its timeout before the job finished."""

    exit_code = 3


class JobFailedError(OrouterError):
    """The provider reported the job as failed/cancelled/expired."""

    exit_code = 4

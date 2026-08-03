"""Stable application errors safe to present in the TUI."""


class FVNError(Exception):
    code = "FVN_ERROR"

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class DataIntegrityError(FVNError):
    code = "DATA_INTEGRITY_ERROR"


class WorkspaceLockedError(FVNError):
    code = "WORKSPACE_LOCKED"


class ProviderError(FVNError):
    code = "PROVIDER_ERROR"


class ResponseFormatError(ProviderError):
    code = "PROVIDER_RESPONSE_INVALID"


class ApplyConflictError(FVNError):
    code = "APPLY_SOURCE_CHANGED"

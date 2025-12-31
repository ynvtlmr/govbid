"""Custom exceptions for the GovBid package."""


class GovBidError(Exception):
    """Base exception for all GovBid errors."""


class SamApiError(GovBidError):
    """Base exception for SAM.gov API errors."""


class SamApiRateLimitError(SamApiError):
    """Raised when rate limit is exceeded beyond retry capacity."""


class SamApiMaxRetriesError(SamApiError):
    """Raised when max retries are exceeded."""

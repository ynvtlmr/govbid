"""GovBid - Government Contract Opportunity Pipeline.

A toolkit for discovering, analyzing, and drafting proposals for
government software contracts using AI.
"""

from .config import settings
from .exceptions import (
    GovBidError,
    SamApiError,
    SamApiMaxRetriesError,
    SamApiRateLimitError,
)
from .models import OpportunityResponse, SearchResponse
from .sam_client import SamOpportunitiesClient

__all__ = [
    # Client
    "SamOpportunitiesClient",
    # Models
    "OpportunityResponse",
    "SearchResponse",
    # Config
    "settings",
    # Exceptions
    "GovBidError",
    "SamApiError",
    "SamApiRateLimitError",
    "SamApiMaxRetriesError",
]

__version__ = "0.1.0"

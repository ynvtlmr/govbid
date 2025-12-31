"""GovBid - Government Contract Opportunity Pipeline.

A toolkit for discovering, analyzing, and drafting proposals for
government software contracts using AI.
"""

from .canada_buys import (
    fetch_raw_csv,
    filter_software_opportunities,
    parse_csv,
    run_harvester_loop,
)
from .config import settings
from .exceptions import (
    CanadaBuysError,
    CanadaBuysFetchError,
    GovBidError,
    SamApiError,
    SamApiMaxRetriesError,
    SamApiRateLimitError,
)
from .history import HistoryManager
from .models import OpportunityResponse, SearchResponse
from .sam_client import SamOpportunitiesClient

__all__ = [
    # Clients
    "SamOpportunitiesClient",
    # Canada Buys
    "fetch_raw_csv",
    "parse_csv",
    "filter_software_opportunities",
    "run_harvester_loop",
    # History
    "HistoryManager",
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
    "CanadaBuysError",
    "CanadaBuysFetchError",
]

__version__ = "0.1.0"

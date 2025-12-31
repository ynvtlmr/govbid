"""SAM.gov Opportunities API client with rate limiting and retry logic."""

import asyncio
import email.utils
import json
import logging
import os
import random
import time
from datetime import date, datetime
from typing import List, Optional

import httpx

from .config import settings
from .exceptions import SamApiMaxRetriesError, SamApiRateLimitError
from .history import HistoryManager
from .models import OpportunityResponse

logger = logging.getLogger(__name__)

# Rate limiting constants
MAX_RETRIES = 5
BASE_DELAY_SECONDS = 2.0
MIN_REQUEST_DELAY_SECONDS = 2.0
MAX_REQUEST_DELAY_SECONDS = 4.0
MAX_RATE_LIMIT_WAIT_SECONDS = 60.0

# Pagination safety limits
SAFETY_OFFSET_LIMIT = 10000


class SamOpportunitiesClient:
    """Async client for SAM.gov Get Opportunities Public API.

    This client implements rate limiting via a semaphore (sequential requests)
    and exponential backoff retry logic for 429/5xx errors.

    Usage:
        async with SamOpportunitiesClient() as client:
            opportunities = await client.search_opportunities(
                posted_from=date(2024, 1, 1),
                posted_to=date(2024, 12, 31),
                naics=["541511"],
            )
    """

    def __init__(self) -> None:
        self.api_key = settings.SAM_API_KEY
        self.base_url = settings.SAM_BASE_URL
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "GovBidToolkit/0.1.0"},
        )
        self.history_manager = HistoryManager()
        # Limit concurrent requests to avoid overwhelming the server
        # Strictly sequential to be respectful and avoid 429s
        self._semaphore = asyncio.Semaphore(1)

    async def __aenter__(self) -> "SamOpportunitiesClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context manager and close the HTTP client."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def _request_with_retry(self, url: str, params: dict) -> httpx.Response:
        """Make a GET request with rate limiting (semaphore) and retries.

        Args:
            url: The API endpoint URL.
            params: Query parameters for the request.

        Returns:
            The HTTP response object.

        Raises:
            SamApiRateLimitError: If rate limit wait time exceeds threshold.
            SamApiMaxRetriesError: If max retries are exhausted.
        """
        async with self._semaphore:
            for attempt in range(MAX_RETRIES):
                try:
                    # Add a robust random delay before every request
                    # Ensures we never exceed ~0.3-0.5 req/sec
                    await asyncio.sleep(
                        random.uniform(
                            MIN_REQUEST_DELAY_SECONDS, MAX_REQUEST_DELAY_SECONDS
                        )
                    )

                    response = await self.client.get(url, params=params)

                    if response.status_code == 429:
                        wait_time = self._parse_retry_after(response, attempt)

                        if wait_time > MAX_RATE_LIMIT_WAIT_SECONDS:
                            logger.error(
                                f"Rate limit wait time too long: {wait_time:.2f}s. "
                                "Aborting."
                            )
                            raise SamApiRateLimitError(
                                f"Rate limit exceeded. Try again after {wait_time:.0f}s"
                            )

                        logger.warning(
                            f"Rate limited (429). Waiting {wait_time:.2f}s before "
                            f"retry {attempt + 1}/{MAX_RETRIES}..."
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    return response

                except httpx.HTTPStatusError as e:
                    # Retry on server errors too
                    if e.response.status_code >= 500:
                        wait_time = BASE_DELAY_SECONDS * (2**attempt)
                        logger.warning(
                            f"Server error {e.response.status_code}. "
                            f"Retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise
                except (httpx.RequestError, httpx.TimeoutException) as e:
                    logger.warning(f"Request failed: {e}. Retrying...")
                    await asyncio.sleep(BASE_DELAY_SECONDS * (2**attempt))
                    continue

            # If we exhaust retries
            raise SamApiMaxRetriesError(f"Max retries exceeded for url: {url}")

    def _parse_retry_after(self, response: httpx.Response, attempt: int) -> float:
        """Parse the Retry-After header or calculate exponential backoff.

        Args:
            response: The 429 response object.
            attempt: Current retry attempt number (0-indexed).

        Returns:
            Wait time in seconds.
        """
        retry_after = response.headers.get("Retry-After")

        if retry_after:
            # Try parsing as seconds first
            try:
                return float(retry_after)
            except ValueError:
                pass

            # Try parsing as HTTP date
            try:
                date_obj = email.utils.parsedate_to_datetime(retry_after)
                now = datetime.now(date_obj.tzinfo)
                wait_time = (date_obj - now).total_seconds()
                return max(1.0, wait_time)  # Minimum 1 second if date is past
            except Exception as parse_err:
                logger.warning(
                    f"Failed to parse Retry-After header '{retry_after}': {parse_err}"
                )

        # Exponential backoff with jitter: 2, 4, 8, 16...
        return BASE_DELAY_SECONDS * (2**attempt) + random.uniform(0, 1)

    def _save_raw_json(self, data: dict):
        """Archive raw JSON response to disk."""
        try:
            os.makedirs(settings.SAM_RAW_DATA_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
            filename = f"sam_opps_{timestamp}.json"
            filepath = os.path.join(settings.SAM_RAW_DATA_DIR, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to archive SAM JSON: {e}")

    def _cleanup_old_archives(self):
        """Delete archived JSON files older than retention period."""
        try:
            if not os.path.exists(settings.SAM_RAW_DATA_DIR):
                return

            cutoff_time = time.time() - (settings.RETENTION_DAYS * 86400)

            for filename in os.listdir(settings.SAM_RAW_DATA_DIR):
                filepath = os.path.join(settings.SAM_RAW_DATA_DIR, filename)
                if os.path.isfile(filepath):
                    # Check modification time
                    if os.path.getmtime(filepath) < cutoff_time:
                        try:
                            os.remove(filepath)
                        except OSError as e:
                            logger.warning(
                                f"Failed to delete old archive {filename}: {e}"
                            )
        except Exception as e:
            logger.warning(f"Error during archive cleanup: {e}")

    async def search_opportunities(
        self,
        posted_from: date,
        posted_to: date,
        limit: int = 1000,
        naics: Optional[List[str]] = None,
        pscs: Optional[List[str]] = None,
    ) -> List[OpportunityResponse]:
        """Search for opportunities within a date range.

        Args:
            posted_from: Start date for posted opportunities.
            posted_to: End date for posted opportunities.
            limit: Maximum records per page (API default).
            naics: Optional list of NAICS codes to filter by.
            pscs: Optional list of PSC codes to filter by.

        Returns:
            List of unique, previously unseen opportunities.
        """
        # 1. Cleanup old history and archives
        self.history_manager.cleanup_history()
        self._cleanup_old_archives()

        base_params = {
            "api_key": self.api_key,
            "postedFrom": posted_from.strftime("%m/%d/%Y"),
            "postedTo": posted_to.strftime("%m/%d/%Y"),
            "limit": str(limit),
            "active": "yes",
        }

        tasks = []

        # Create a task for each NAICS code
        if naics:
            for code in naics:
                p = base_params.copy()
                p["ncode"] = code
                tasks.append(self._fetch_all_pages(p))

        # Create a task for each PSC code
        if pscs:
            for code in pscs:
                p = base_params.copy()
                p["ccode"] = code
                tasks.append(self._fetch_all_pages(p))

        if not tasks:
            tasks.append(self._fetch_all_pages(base_params))

        # Execute all searches
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        all_opportunities: List[OpportunityResponse] = []
        for res in results_lists:
            if isinstance(res, BaseException):
                logger.error(f"One of the search tasks failed: {res}")
                continue
            # res is now narrowed to List[OpportunityResponse]
            all_opportunities.extend(res)

        # Deduplicate within this run AND against history
        seen_ids = self.history_manager.load_seen_ids()
        # Also track what we've seen in this current run to deal with overlaps between NAICS/PSC tasks
        current_run_ids = set()

        unique_opportunities: List[OpportunityResponse] = []
        for opp in all_opportunities:
            # If we haven't seen it in history AND haven't seen it in this run
            if opp.noticeId not in seen_ids and opp.noticeId not in current_run_ids:
                unique_opportunities.append(opp)
                # Mark as seen
                current_run_ids.add(opp.noticeId)
                self.history_manager.mark_as_seen(opp.noticeId)

        return unique_opportunities

    async def _fetch_all_pages(self, params: dict) -> List[OpportunityResponse]:
        """Fetch all pages for a given set of search parameters.

        Args:
            params: Query parameters including filters.

        Returns:
            List of all opportunities across all pages.
        """
        results: List[OpportunityResponse] = []
        offset = 0
        limit = int(params["limit"])

        while True:
            current_params = params.copy()
            current_params["offset"] = str(offset)

            try:
                response = await self._request_with_retry(self.base_url, current_params)
                data = response.json()

                # Archive the raw data
                self._save_raw_json(data)

                if "opportunitiesData" not in data:
                    break

                items = data["opportunitiesData"]
                if not items:
                    break

                for item in items:
                    results.append(OpportunityResponse(**item))

                if len(items) < limit:
                    break

                offset += limit

                # Safety break
                if offset > SAFETY_OFFSET_LIMIT:
                    logger.warning(
                        f"Reached safety limit of {SAFETY_OFFSET_LIMIT} records, "
                        "stopping."
                    )
                    break

            except Exception as e:
                logger.error(f"Error fetching opportunities pages: {e}")
                # If a page fails after retries, we likely should stop this chain
                break

        return results

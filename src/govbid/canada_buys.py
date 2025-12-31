"""
Canada Buys Harvester
Fetches new tender notices from Canada Buys CSV and filters for
software engineering opportunities.
"""

import csv
import io
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import httpx

from govbid.config import settings

logger = logging.getLogger(__name__)


def fetch_raw_csv() -> Optional[str]:
    """
    Fetches the raw 'New Tender Notices' CSV content from Canada Buys.
    Returns the content string on success, None on failure.
    """
    try:
        # Add User-Agent to match typical browser or acceptable bot behavior
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
        }
        response = httpx.get(
            settings.CANADA_BUYS_CSV_URL,
            headers=headers,
            timeout=30.0,
            follow_redirects=True,
        )
        response.raise_for_status()

        # The CSV is encoded in utf-8-sig usually for Excel compatibility,
        # or just utf-8.
        return response.content.decode("utf-8-sig")

    except httpx.RequestError as e:
        logger.error(f"Error fetching Canada Buys CSV: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching Canada Buys CSV: {e}")
        return None


def parse_csv(content: str) -> List[Dict[str, str]]:
    """
    Parses CSV content into a list of dictionaries.
    """
    try:
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)
    except Exception as e:
        logger.error(f"Error parsing CSV content: {e}")
        return []


def save_raw_csv(content: str):
    """
    Saves the raw CSV content to a timestamped file.
    """
    try:
        os.makedirs(settings.RAW_DATA_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"canada_buys_tenders_{timestamp}.csv"
        filepath = os.path.join(settings.RAW_DATA_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Archived raw CSV to: {filepath}")
    except Exception as e:
        logger.error(f"Failed to archive raw CSV: {e}")


def cleanup_old_files():
    """
    Deletes files in the raw data directory older than RETENTION_DAYS.
    """
    try:
        if not os.path.exists(settings.RAW_DATA_DIR):
            return

        cutoff_time = time.time() - (settings.RETENTION_DAYS * 86400)

        for filename in os.listdir(settings.RAW_DATA_DIR):
            filepath = os.path.join(settings.RAW_DATA_DIR, filename)
            if os.path.isfile(filepath):
                file_mtime = os.path.getmtime(filepath)
                if file_mtime < cutoff_time:
                    try:
                        os.remove(filepath)
                        logger.info(f"Deleted old archive file: {filename}")
                    except OSError as e:
                        logger.warning(f"Error deleting {filename}: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup of old files: {e}")


def filter_software_opportunities(
    notices: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Filters notices for those where the UNSPSC code starts with any of the
    target prefixes.
    """
    filtered = []
    for notice in notices:
        unspsc_text = notice.get("unspsc", "")
        # The UNSPSC field can contain multiple codes separated by newlines.
        # Example: "*78101809\n*78102200"

        # We need to check if ANY of the codes match our formatting.
        codes = [code.strip().lstrip("*") for code in unspsc_text.splitlines()]

        match_found = False
        for code in codes:
            for prefix in settings.TARGET_UNSPSC_PREFIXES:
                if code.startswith(prefix):
                    filtered.append(notice)
                    match_found = True
                    break
            if match_found:
                break
    return filtered


def run_harvester_loop(interval_seconds: int = 7200):
    """
    Runs the harvester loop indefinitely.
    """
    logger.info(
        f"Starting Canada Buys Harvester. Polling every {interval_seconds} seconds."
    )
    logger.info(
        f"Archiving to {settings.RAW_DATA_DIR} "
        f"(Retention: {settings.RETENTION_DAYS} days)"
    )

    while True:
        logger.info("Starting cycle...")

        # 1. Cleanup old files
        cleanup_old_files()

        # 2. Fetch
        content = fetch_raw_csv()
        if content:
            # 3. Archive
            save_raw_csv(content)

            # 4. Parse & Process
            notices = parse_csv(content)
            logger.info(f"Fetched {len(notices)} notices.")

            opportunities = filter_software_opportunities(notices)
            logger.info(
                f"Found {len(opportunities)} software engineering opportunities."
            )

            for opp in opportunities:
                title = opp.get("title-titre-eng", "No Title")
                unspsc = opp.get("unspsc")
                url = opp.get("noticeURL-URLavis-eng", "No URL")
                logger.info(f"  - {title} (UNSPSC: {unspsc})")
                logger.info(f"    Link: {url}")
        else:
            logger.warning("Failed to fetch notices.")

        time.sleep(interval_seconds)

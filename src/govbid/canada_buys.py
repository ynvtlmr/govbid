"""
Canada Buys Harvester
Fetches new tender notices from Canada Buys CSV and filters for
software engineering opportunities.
"""

import csv
import io
import time
from typing import Dict, List

import httpx

from govbid.config import settings


def fetch_new_tender_notices() -> List[Dict[str, str]]:
    """
    Fetches the 'New Tender Notices' CSV from Canada Buys.
    Returns a list of dictionaries, where each dict represents a row.
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
        # We'll decode it and parse with csv module.
        content = response.content.decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(content))
        return list(reader)
    except httpx.RequestError as e:
        print(f"Error fetching Canada Buys CSV: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error parsing Canada Buys CSV: {e}")
        return []


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
    print(f"Starting Canada Buys Harvester. Polling every {interval_seconds} seconds.")
    while True:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fetching notices...")
        notices = fetch_new_tender_notices()
        print(f"Fetched {len(notices)} notices.")

        opportunities = filter_software_opportunities(notices)
        print(f"Found {len(opportunities)} software engineering opportunities.")

        for opp in opportunities:
            title = opp.get("title-titre-eng", "No Title")
            unspsc = opp.get("unspsc")
            url = opp.get("noticeURL-URLavis-eng", "No URL")
            print(f"  - {title} (UNSPSC: {unspsc})")
            print(f"    Link: {url}")

        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_harvester_loop()

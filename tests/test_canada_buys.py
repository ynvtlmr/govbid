import os
import time
from unittest.mock import MagicMock, patch

import httpx

from govbid.canada_buys import (
    cleanup_old_files,
    fetch_raw_csv,
    filter_software_opportunities,
    parse_csv,
    save_raw_csv,
)
from govbid.config import settings

# Mock CSV Content
# Includes headers and a mix of matching and non-matching rows.
# One matching row (8111...), one non-matching row, and one with MULTIPLE
# codes where the second one matches.
MOCK_CSV_CONTENT = """title-titre-eng,unspsc,noticeURL-URLavis-eng
"Test Software Job","*81111705","http://example.com/software"
"Test Cleaning Job","*78101809","http://example.com/cleaning"
"Another Software Job","81110000","http://example.com/software2"
"Multiline Match Job","*78101809\n*81111500","http://example.com/multiline"
"""


def test_fetch_parse_filter():
    # Mock httpx.get
    with patch("govbid.canada_buys.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_CSV_CONTENT.encode("utf-8-sig")
        mock_get.return_value = mock_response

        # 1. Test Fetch
        content = fetch_raw_csv()
        assert content == MOCK_CSV_CONTENT

        # 2. Test Parse
        notices = parse_csv(content)
        assert len(notices) == 4

        # 3. Test Filter
        # Should catch "*81111705" and "81110000"
        # Should ignore "*78101809"
        opportunities = filter_software_opportunities(notices)

        assert len(opportunities) == 3

        titles = [o["title-titre-eng"] for o in opportunities]
        assert "Test Software Job" in titles
        assert "Another Software Job" in titles
        assert "Multiline Match Job" in titles
        assert "Test Cleaning Job" not in titles


def test_fetch_error():
    with patch("govbid.canada_buys.httpx.get") as mock_get:
        mock_get.side_effect = Exception("Connection error")

        content = fetch_raw_csv()
        assert content is None


def test_fetch_request_error():
    """Test that httpx.RequestError is handled correctly."""
    with patch("govbid.canada_buys.httpx.get") as mock_get:
        mock_get.side_effect = httpx.RequestError(
            "Connection refused",
            request=httpx.Request("GET", settings.CANADA_BUYS_CSV_URL),
        )

        content = fetch_raw_csv()
        assert content is None


def test_archiving(tmp_path):
    # Override settings to use a temporary directory
    with patch.object(settings, "RAW_DATA_DIR", str(tmp_path)):
        save_raw_csv(MOCK_CSV_CONTENT)

        files = os.listdir(tmp_path)
        assert len(files) == 1
        assert files[0].startswith("canada_buys_tenders_")
        assert files[0].endswith(".csv")

        with open(tmp_path / files[0], "r", encoding="utf-8") as f:
            assert f.read() == MOCK_CSV_CONTENT


def test_cleanup(tmp_path):
    # Override settings
    with patch.object(settings, "RAW_DATA_DIR", str(tmp_path)):
        with patch.object(settings, "RETENTION_DAYS", 60):
            # Create a "fresh" file (today)
            fresh_file = tmp_path / "fresh.csv"
            fresh_file.touch()

            # Create an "old" file (61 days ago)
            # We need to manually set the mtime
            old_file = tmp_path / "old.csv"
            old_file.touch()

            old_time = time.time() - (61 * 86400)
            os.utime(old_file, (old_time, old_time))

            # Verify both exist
            assert len(os.listdir(tmp_path)) == 2

            # Run cleanup
            cleanup_old_files()

            # Verify only fresh file remains
            files = os.listdir(tmp_path)
            assert len(files) == 1
            assert "fresh.csv" in files
            assert "old.csv" not in files

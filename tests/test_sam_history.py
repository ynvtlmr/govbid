import json
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from govbid.config import settings
from govbid.history import HistoryManager
from govbid.sam_client import SamOpportunitiesClient


def test_history_manager_persistence(tmp_path):
    # Setup temp history file
    history_file = tmp_path / "test_history.jsonl"

    with patch.object(settings, "SAM_HISTORY_FILE", str(history_file)):
        manager = HistoryManager()

        # 1. Test empty load
        assert len(manager.load_seen_ids()) == 0

        # 2. Test marking as seen
        manager.mark_as_seen("notice123")
        manager.mark_as_seen("notice456")

        # 3. Test reloading
        seen_ids = manager.load_seen_ids()
        assert len(seen_ids) == 2
        assert "notice123" in seen_ids
        assert "notice456" in seen_ids


def test_history_cleanup(tmp_path):
    history_file = tmp_path / "test_history.jsonl"

    with patch.object(settings, "SAM_HISTORY_FILE", str(history_file)):
        manager = HistoryManager()

        # Write one fresh and one old entry
        fresh_entry = {"noticeId": "fresh", "timestamp": time.time()}
        old_entry = {"noticeId": "old", "timestamp": time.time() - (61 * 86400)}

        with open(history_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(fresh_entry) + "\n")
            f.write(json.dumps(old_entry) + "\n")

        assert len(manager.load_seen_ids()) == 2

        # Run cleanup
        manager.cleanup_history(retention_days=60)

        # Verify result
        seen_ids = manager.load_seen_ids()
        assert len(seen_ids) == 1
        assert "fresh" in seen_ids
        assert "old" not in seen_ids


@pytest.mark.asyncio
async def test_sam_client_archiving_and_filtering(tmp_path):
    # Mock settings
    with (
        patch.object(settings, "SAM_RAW_DATA_DIR", str(tmp_path / "raw")),
        patch.object(settings, "SAM_HISTORY_FILE", str(tmp_path / "history.jsonl")),
    ):
        client = SamOpportunitiesClient()

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "opportunitiesData": [
                {"noticeId": "opp1", "title": "Test 1", "postedDate": "2023-01-01"},
                {"noticeId": "opp2", "title": "Test 2", "postedDate": "2023-01-01"},
            ]
        }

        with patch.object(client, "_request_with_retry", return_value=mock_response):
            # First run: Should find both
            results = await client._fetch_all_pages({"limit": 10})
            assert len(results) == 2

            # Verify Archiving
            raw_files = os.listdir(tmp_path / "raw")
            assert len(raw_files) == 1
            with open(tmp_path / "raw" / raw_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data["opportunitiesData"][0]["noticeId"] == "opp1"

        client.history_manager.mark_as_seen("opp1")

        # Test deduplication by calling search_opportunities directly
        # with a mocked _fetch_all_pages that returns overlapping IDs
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "opportunitiesData": [
                {
                    "noticeId": "opp1",
                    "title": "Already Seen",
                    "postedDate": "2023-01-01",
                },
                {
                    "noticeId": "opp2",
                    "title": "New One",
                    "postedDate": "2023-01-01",
                },
                {
                    "noticeId": "opp3",
                    "title": "Also New",
                    "postedDate": "2023-01-01",
                },
            ]
        }

        from datetime import date

        with patch.object(client, "_request_with_retry", return_value=mock_response2):
            opportunities = await client.search_opportunities(
                posted_from=date(2023, 1, 1),
                posted_to=date(2023, 1, 31),
            )

            # opp1 should be filtered (already seen), opp2 and opp3 remain
            result_ids = {opp.noticeId for opp in opportunities}
            assert "opp1" not in result_ids  # Already seen
            assert "opp2" in result_ids
            assert "opp3" in result_ids
            assert len(opportunities) == 2

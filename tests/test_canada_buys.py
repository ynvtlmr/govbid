from unittest.mock import MagicMock, patch

from govbid.canada_buys import fetch_new_tender_notices, filter_software_opportunities

# Mock CSV Content
# Includes headers and a mix of matching and non-matching rows.
# One matching row (8111...) and one non-matching row.
# One matching row (8111...), one non-matching row, and one with MULTIPLE
# codes where the second one matches.
MOCK_CSV_CONTENT = """title-titre-eng,unspsc,noticeURL-URLavis-eng
"Test Software Job","*81111705","http://example.com/software"
"Test Cleaning Job","*78101809","http://example.com/cleaning"
"Another Software Job","81110000","http://example.com/software2"
"Multiline Match Job","*78101809\n*81111500","http://example.com/multiline"
"""


def test_fetch_and_filter():
    # Mock httpx.get
    with patch("govbid.canada_buys.httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = MOCK_CSV_CONTENT.encode("utf-8-sig")
        mock_get.return_value = mock_response

        # 1. Test Fetch
        notices = fetch_new_tender_notices()
        assert len(notices) == 4

        # 2. Test Filter
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

        notices = fetch_new_tender_notices()
        assert notices == []

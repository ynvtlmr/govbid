"""
History Manager for SAM.gov Opportunities
Handles persistent deduplication by tracking seen notice IDs in a JSONL file.
"""

import json
import logging
import os
import time
from typing import Optional, Set

from govbid.config import settings

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages the history of seen opportunities."""

    def __init__(self, history_file: Optional[str] = None):
        self.history_file = history_file or settings.SAM_HISTORY_FILE
        self._ensure_history_dir()

    def _ensure_history_dir(self):
        """Ensure the directory for the history file exists."""
        directory = os.path.dirname(self.history_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def load_seen_ids(self) -> Set[str]:
        """Load all seen notice IDs from the history file."""
        seen_ids = set()
        if not os.path.exists(self.history_file):
            return seen_ids

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if "noticeId" in entry:
                            seen_ids.add(entry["noticeId"])
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error loading history file: {e}")

        return seen_ids

    def mark_as_seen(self, notice_id: str):
        """Mark a notice ID as seen by appending it to the history file."""
        entry = {
            "noticeId": notice_id,
            "timestamp": time.time(),
        }
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Error writing to history file: {e}")

    def cleanup_history(self, retention_days: int = settings.RETENTION_DAYS):
        """
        Rewrite the history file, removing entries older than retention_days.
        """
        if not os.path.exists(self.history_file):
            return

        cutoff_time = time.time() - (retention_days * 86400)
        temp_file = self.history_file + ".tmp"

        try:
            kept_count = 0
            removed_count = 0

            with (
                open(self.history_file, "r", encoding="utf-8") as f_in,
                open(temp_file, "w", encoding="utf-8") as f_out,
            ):
                for line in f_in:
                    try:
                        entry = json.loads(line)
                        if entry.get("timestamp", 0) > cutoff_time:
                            f_out.write(line)
                            kept_count += 1
                        else:
                            removed_count += 1
                    except json.JSONDecodeError:
                        continue  # Skip corrupt lines

            # Replace original file with cleaned file
            os.replace(temp_file, self.history_file)
            if removed_count > 0:
                logger.info(
                    f"Cleaned up history: Removed {removed_count} old entries, "
                    f"kept {kept_count}."
                )

        except Exception as e:
            logger.error(f"Error cleaning up history: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)

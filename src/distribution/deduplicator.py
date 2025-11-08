"""Alert deduplication to prevent duplicate notifications.

This module provides file-based deduplication by checking if alert JSON files
already exist in the alerts directory.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class AlertDeduplicator:
    """Prevent duplicate alert distribution using file-based tracking.

    Checks if alert JSON file already exists to determine if alert has been
    processed before.

    Attributes:
        alert_dir: Directory where alert JSON files are saved
    """

    def __init__(self, alert_dir: Optional[Path] = None):
        """Initialize deduplicator.

        Args:
            alert_dir: Directory for alert files (defaults to config value)
        """
        if alert_dir:
            self.alert_dir = alert_dir
        else:
            settings = get_settings()
            self.alert_dir = Path(settings.get('alerts.output_dir', default='results/alerts'))

        self.alert_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"AlertDeduplicator initialized: alert_dir={self.alert_dir}")

    def is_duplicate(self, alert_id: str) -> bool:
        """Check if alert has already been processed.

        Args:
            alert_id: Alert ID (e.g., "ALERT-20211215-removal-transitory")

        Returns:
            True if alert file exists (duplicate), False otherwise (new)
        """
        alert_file = self.alert_dir / f"{alert_id}.json"
        exists = alert_file.exists()

        if exists:
            logger.debug(f"Alert {alert_id} is duplicate (file exists)")
        else:
            logger.debug(f"Alert {alert_id} is new (file doesn't exist)")

        return exists

    def should_distribute(self, alert: Dict) -> bool:
        """Determine if alert should be distributed.

        Args:
            alert: Alert dictionary with 'alert_id' key

        Returns:
            True if alert should be distributed, False if duplicate
        """
        alert_id = alert.get('alert_id')

        if not alert_id:
            logger.warning("Alert missing 'alert_id', cannot deduplicate")
            return True  # Distribute anyway to be safe

        is_dup = self.is_duplicate(alert_id)

        if is_dup:
            logger.info(f"Skipping duplicate alert: {alert_id}")
            return False

        logger.info(f"Alert {alert_id} should be distributed (not a duplicate)")
        return True

    def get_distributed_count(self) -> int:
        """Get count of alerts that have been distributed.

        Returns:
            Number of alert JSON files in alert directory
        """
        alert_files = list(self.alert_dir.glob('ALERT-*.json'))
        count = len(alert_files)

        logger.debug(f"Found {count} distributed alerts in {self.alert_dir}")
        return count

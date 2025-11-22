"""
Market data cache management utilities.

Provides cache cleanup, retention policy enforcement, and cache statistics.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class MarketDataCache:
    """
    Utility class for managing market data cache.

    Handles cache cleanup, retention policies, and cache statistics.
    The actual caching is done by individual clients (FREDClient, YahooClient).
    """

    def __init__(self, cache_dir: Path = None, retention_days: int = None):
        """
        Initialize cache manager.

        Args:
            cache_dir: Cache directory path. If None, uses config setting.
            retention_days: Number of days to retain cached data. If None, uses config.
        """
        settings = get_settings()

        if cache_dir is None:
            cache_dir = Path(settings.get(
                'market_validation.storage.cache_dir',
                default='data/market_cache'
            ))

        if retention_days is None:
            retention_days = settings.get(
                'market_validation.storage.retention_days',
                default=90
            )

        self.cache_dir = Path(cache_dir)
        self.retention_days = retention_days

        logger.info(
            f"MarketDataCache initialized: {self.cache_dir}, "
            f"retention={self.retention_days} days"
        )

    def cleanup_old_files(self) -> int:
        """
        Remove cached files older than retention period.

        Returns:
            Number of files deleted
        """
        if not self.cache_dir.exists():
            logger.warning(f"Cache directory does not exist: {self.cache_dir}")
            return 0

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        try:
            for file_path in self.cache_dir.rglob('*'):
                if file_path.is_file():
                    # Check file modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_date:
                        logger.debug(f"Deleting old cache file: {file_path}")
                        file_path.unlink()
                        deleted_count += 1

            logger.info(
                f"Cache cleanup complete: {deleted_count} files deleted "
                f"(older than {self.retention_days} days)"
            )

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

        return deleted_count

    def get_cache_stats(self) -> Dict:
        """
        Get statistics about cached data.

        Returns:
            Dictionary with cache statistics
        """
        if not self.cache_dir.exists():
            return {
                'exists': False,
                'total_files': 0,
                'total_size_mb': 0,
            }

        stats = {
            'exists': True,
            'total_files': 0,
            'total_size_mb': 0,
            'by_source': {},
        }

        try:
            # Count files and calculate sizes
            for file_path in self.cache_dir.rglob('*'):
                if file_path.is_file():
                    stats['total_files'] += 1
                    stats['total_size_mb'] += file_path.stat().st_size / (1024 * 1024)

                    # Track by source (subdirectory)
                    source = file_path.parent.name
                    if source not in stats['by_source']:
                        stats['by_source'][source] = {'files': 0, 'size_mb': 0}
                    stats['by_source'][source]['files'] += 1
                    stats['by_source'][source]['size_mb'] += file_path.stat().st_size / (1024 * 1024)

            # Round sizes
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            for source in stats['by_source']:
                stats['by_source'][source]['size_mb'] = round(
                    stats['by_source'][source]['size_mb'], 2
                )

        except Exception as e:
            logger.error(f"Error calculating cache stats: {e}")

        return stats

    def clear_cache(self, source: str = None) -> int:
        """
        Clear all cached data or specific source.

        Args:
            source: If specified, only clear this source (e.g., 'dgs2', 'vix')

        Returns:
            Number of files deleted
        """
        if not self.cache_dir.exists():
            return 0

        deleted_count = 0

        try:
            if source:
                # Clear specific source
                source_dir = self.cache_dir / source
                if source_dir.exists():
                    for file_path in source_dir.glob('*'):
                        if file_path.is_file():
                            file_path.unlink()
                            deleted_count += 1
                    logger.info(f"Cleared {deleted_count} files from {source} cache")
            else:
                # Clear all cache
                for file_path in self.cache_dir.rglob('*'):
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_count += 1
                logger.info(f"Cleared entire cache: {deleted_count} files deleted")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

        return deleted_count

    def ensure_cache_dir(self) -> Path:
        """
        Ensure cache directory exists.

        Returns:
            Path to cache directory
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir

    def get_cached_dates(self, source: str) -> List[str]:
        """
        Get list of dates that have cached data for a given source.

        Args:
            source: Source identifier (e.g., 'dgs2', 'vix', 'spy')

        Returns:
            List of date strings (YYYYMMDD format)
        """
        source_dir = self.cache_dir / source
        if not source_dir.exists():
            return []

        dates = set()
        try:
            for file_path in source_dir.glob('*'):
                if file_path.is_file():
                    # Extract date from filename (assumes format: YYYYMMDD.txt or YYYYMMDD_*.csv)
                    filename = file_path.stem
                    if '_' in filename:
                        date_part = filename.split('_')[0]
                    else:
                        date_part = filename

                    # Validate date format
                    if len(date_part) == 8 and date_part.isdigit():
                        dates.add(date_part)

            return sorted(list(dates))

        except Exception as e:
            logger.error(f"Error getting cached dates for {source}: {e}")
            return []

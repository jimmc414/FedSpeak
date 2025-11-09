"""Media data caching utilities for FedSpeak.

This module provides caching functionality for media coverage data from GDELT
and sentiment analysis results, reducing API calls and improving performance.

Cache Structure:
    data/media_cache/
    ├── gdelt/
    │   ├── 20211215_transitory.json
    │   └── ...
    ├── sentiment/
    │   ├── 20211215_transitory_finbert.json
    │   └── ...
    └── cache_index.json
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MediaDataCache:
    """Cache manager for media coverage and sentiment data.

    Provides file-based caching to:
    - Avoid redundant GDELT API calls (even though GDELT is free/unlimited)
    - Cache CPU-intensive FinBERT sentiment analysis results
    - Enable offline testing and faster repeated queries
    - Manage cache retention and cleanup

    Cache is stored as JSON files organized by source type and query parameters.
    """

    def __init__(self,
                 cache_dir: str = "data/media_cache",
                 retention_days: int = 90):
        """Initialize media data cache.

        Args:
            cache_dir: Directory for cache storage (default: data/media_cache)
            retention_days: Days to retain cached data (default: 90)
        """
        self.cache_dir = Path(cache_dir)
        self.retention_days = retention_days

        # Create cache subdirectories
        self.gdelt_dir = self.cache_dir / 'gdelt'
        self.sentiment_dir = self.cache_dir / 'sentiment'

        self.gdelt_dir.mkdir(parents=True, exist_ok=True)
        self.sentiment_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized media cache: {self.cache_dir} "
            f"(retention: {retention_days} days)"
        )

    def get_gdelt_cache(self, date: str, term: str) -> Optional[List[Dict]]:
        """Retrieve cached GDELT search results.

        Args:
            date: FOMC date (YYYYMMDD)
            term: Search term

        Returns:
            List of article dictionaries if cached, None otherwise
        """
        cache_file = self._get_gdelt_cache_path(date, term)

        if not cache_file.exists():
            logger.debug(f"GDELT cache miss: {date}_{term}")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.debug(
                f"GDELT cache hit: {date}_{term} "
                f"({len(data.get('articles', []))} articles)"
            )

            return data.get('articles', [])

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"GDELT cache read error for {cache_file}: {e}")
            return None

    def save_gdelt_cache(self, date: str, term: str, articles: List[Dict],
                         metadata: Optional[Dict] = None):
        """Save GDELT search results to cache.

        Args:
            date: FOMC date (YYYYMMDD)
            term: Search term
            articles: List of article dictionaries from GDELT
            metadata: Optional metadata (query, timestamp, etc.)
        """
        cache_file = self._get_gdelt_cache_path(date, term)

        cache_data = {
            'date': date,
            'term': term,
            'cached_at': datetime.now().isoformat(),
            'article_count': len(articles),
            'articles': articles,
            'metadata': metadata or {}
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(
                f"GDELT cache saved: {date}_{term} ({len(articles)} articles)"
            )

        except IOError as e:
            logger.error(f"GDELT cache write error for {cache_file}: {e}")

    def get_sentiment_cache(self, date: str, term: str) -> Optional[Dict]:
        """Retrieve cached sentiment analysis results.

        Args:
            date: FOMC date (YYYYMMDD)
            term: Search term

        Returns:
            Sentiment results dictionary if cached, None otherwise
        """
        cache_file = self._get_sentiment_cache_path(date, term)

        if not cache_file.exists():
            logger.debug(f"Sentiment cache miss: {date}_{term}")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.debug(f"Sentiment cache hit: {date}_{term}")

            return data

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Sentiment cache read error for {cache_file}: {e}")
            return None

    def save_sentiment_cache(self, date: str, term: str,
                             sentiment_results: Dict):
        """Save sentiment analysis results to cache.

        Args:
            date: FOMC date (YYYYMMDD)
            term: Search term
            sentiment_results: Sentiment analysis results dictionary
        """
        cache_file = self._get_sentiment_cache_path(date, term)

        cache_data = {
            'date': date,
            'term': term,
            'cached_at': datetime.now().isoformat(),
            'results': sentiment_results
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(f"Sentiment cache saved: {date}_{term}")

        except IOError as e:
            logger.error(f"Sentiment cache write error for {cache_file}: {e}")

    def cleanup_old_files(self) -> int:
        """Remove cached files older than retention period.

        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        logger.info(
            f"Cleaning cache: removing files older than {self.retention_days} days"
        )

        # Clean GDELT cache
        for cache_file in self.gdelt_dir.glob('*.json'):
            if self._is_file_old(cache_file, cutoff_date):
                cache_file.unlink()
                deleted_count += 1

        # Clean sentiment cache
        for cache_file in self.sentiment_dir.glob('*.json'):
            if self._is_file_old(cache_file, cutoff_date):
                cache_file.unlink()
                deleted_count += 1

        logger.info(f"Cache cleanup: deleted {deleted_count} old files")

        return deleted_count

    def get_cache_stats(self) -> Dict:
        """Get statistics about cached data.

        Returns:
            Dictionary with cache statistics:
            - gdelt_files: Number of GDELT cache files
            - sentiment_files: Number of sentiment cache files
            - total_size_mb: Total cache size in megabytes
            - oldest_file: Age of oldest file in days
            - newest_file: Age of newest file in days
        """
        gdelt_files = list(self.gdelt_dir.glob('*.json'))
        sentiment_files = list(self.sentiment_dir.glob('*.json'))
        all_files = gdelt_files + sentiment_files

        if not all_files:
            return {
                'gdelt_files': 0,
                'sentiment_files': 0,
                'total_size_mb': 0.0,
                'oldest_file_days': None,
                'newest_file_days': None
            }

        # Calculate total size
        total_size = sum(f.stat().st_size for f in all_files)
        total_size_mb = total_size / (1024 * 1024)

        # Find oldest and newest files
        now = datetime.now()
        file_ages = [
            (now - datetime.fromtimestamp(f.stat().st_mtime)).days
            for f in all_files
        ]

        return {
            'gdelt_files': len(gdelt_files),
            'sentiment_files': len(sentiment_files),
            'total_size_mb': round(total_size_mb, 2),
            'oldest_file_days': max(file_ages) if file_ages else None,
            'newest_file_days': min(file_ages) if file_ages else None
        }

    def clear_cache(self, source: Optional[str] = None) -> int:
        """Clear all cached data or specific source.

        Args:
            source: Cache source to clear ('gdelt', 'sentiment', or None for all)

        Returns:
            Number of files deleted
        """
        deleted_count = 0

        if source is None or source == 'gdelt':
            for cache_file in self.gdelt_dir.glob('*.json'):
                cache_file.unlink()
                deleted_count += 1

        if source is None or source == 'sentiment':
            for cache_file in self.sentiment_dir.glob('*.json'):
                cache_file.unlink()
                deleted_count += 1

        logger.info(
            f"Cache cleared: {deleted_count} files "
            f"(source: {source or 'all'})"
        )

        return deleted_count

    def _get_gdelt_cache_path(self, date: str, term: str) -> Path:
        """Get cache file path for GDELT data.

        Args:
            date: FOMC date (YYYYMMDD)
            term: Search term

        Returns:
            Path to cache file
        """
        # Sanitize term for filename
        safe_term = self._sanitize_filename(term)
        filename = f"{date}_{safe_term}.json"

        return self.gdelt_dir / filename

    def _get_sentiment_cache_path(self, date: str, term: str) -> Path:
        """Get cache file path for sentiment data.

        Args:
            date: FOMC date (YYYYMMDD)
            term: Search term

        Returns:
            Path to cache file
        """
        # Sanitize term for filename
        safe_term = self._sanitize_filename(term)
        filename = f"{date}_{safe_term}_finbert.json"

        return self.sentiment_dir / filename

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filename.

        Args:
            text: Text to sanitize

        Returns:
            Safe filename component (alphanumeric + underscore)
        """
        # Replace spaces with underscores
        safe = text.replace(' ', '_')

        # Keep only alphanumeric and underscore
        safe = ''.join(c for c in safe if c.isalnum() or c == '_')

        # Limit length
        return safe[:50].lower()

    def _is_file_old(self, file_path: Path, cutoff_date: datetime) -> bool:
        """Check if file is older than cutoff date.

        Args:
            file_path: Path to file
            cutoff_date: Cutoff datetime

        Returns:
            True if file is older than cutoff, False otherwise
        """
        try:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_mtime < cutoff_date

        except OSError:
            # If we can't get file time, consider it old
            return True

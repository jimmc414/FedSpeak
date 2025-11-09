"""MILA stance analysis caching utilities.

This module provides caching functionality for MILA stance analysis results,
minimizing API calls to Claude and enabling offline testing.

Cache Structure:
    data/mila_cache/
    ├── stance/
    │   ├── policy_statement_20211215.json
    │   ├── policy_statement_20210428.json
    │   └── ...
    └── cache_stats.json

Each cache file stores:
- Stance classification (hawkish/dovish/neutral)
- Confidence score
- Numeric score
- Explanation
- Key phrases
- Metadata (timestamp, model version)
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MILAStanceCache:
    """Cache manager for MILA stance analysis results.

    Provides file-based caching to:
    - Minimize expensive Claude API calls
    - Enable offline testing and faster repeated queries
    - Ensure consistency (statements don't change, neither should analysis)
    - Manage cache retention and cleanup

    Cache is stored as JSON files organized by document date and type.
    Since FOMC statements are immutable, cached results are valid indefinitely.
    """

    def __init__(self,
                 cache_dir: str = "data/mila_cache",
                 retention_days: int = 365):
        """Initialize MILA stance cache.

        Args:
            cache_dir: Directory for cache storage (default: data/mila_cache)
            retention_days: Days to retain cached data (default: 365, very long
                          since statements don't change)
        """
        self.cache_dir = Path(cache_dir)
        self.retention_days = retention_days

        # Create cache subdirectories
        self.stance_dir = self.cache_dir / 'stance'
        self.stance_dir.mkdir(parents=True, exist_ok=True)

        # Cache statistics tracking
        self.stats_file = self.cache_dir / 'cache_stats.json'
        self.stats = self._load_stats()

        logger.info(
            f"Initialized MILA cache: {self.cache_dir} "
            f"(retention: {retention_days} days)"
        )

    def get_stance(self, date: str, doc_type: str = 'policy_statement') -> Optional[Dict]:
        """Retrieve cached stance analysis result.

        Args:
            date: Document date (YYYYMMDD)
            doc_type: Document type (policy_statement, minutes, etc.)

        Returns:
            Stance analysis result dictionary if cached, None otherwise
        """
        cache_file = self._get_stance_cache_path(date, doc_type)

        if not cache_file.exists():
            logger.debug(f"Stance cache miss: {doc_type}_{date}")
            self.stats['misses'] = self.stats.get('misses', 0) + 1
            self._save_stats()
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.debug(f"Stance cache hit: {doc_type}_{date}")
            self.stats['hits'] = self.stats.get('hits', 0) + 1
            self._save_stats()

            # Return analysis result (remove metadata)
            return {
                'stance': data.get('stance'),
                'score': data.get('score'),
                'confidence': data.get('confidence'),
                'explanation': data.get('explanation'),
                'key_phrases': data.get('key_phrases', [])
            }

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Stance cache read error for {cache_file}: {e}")
            return None

    def save_stance(self, date: str, doc_type: str, result: Dict):
        """Save stance analysis result to cache.

        Args:
            date: Document date (YYYYMMDD)
            doc_type: Document type (policy_statement, minutes, etc.)
            result: Stance analysis result dictionary
        """
        cache_file = self._get_stance_cache_path(date, doc_type)

        # Add metadata
        cache_data = {
            **result,
            'metadata': {
                'cached_at': datetime.now().isoformat(),
                'date': date,
                'doc_type': doc_type,
                'cache_version': '1.0'
            }
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved stance to cache: {doc_type}_{date}")
            self.stats['total_entries'] = self.stats.get('total_entries', 0) + 1
            self._save_stats()

        except (IOError, OSError) as e:
            logger.error(f"Failed to save stance cache for {cache_file}: {e}")

    def _get_stance_cache_path(self, date: str, doc_type: str) -> Path:
        """Get cache file path for a stance analysis.

        Args:
            date: Document date (YYYYMMDD)
            doc_type: Document type

        Returns:
            Path to cache file
        """
        # Sanitize filename components
        date_safe = self._sanitize_filename(date)
        doc_type_safe = self._sanitize_filename(doc_type)

        filename = f"{doc_type_safe}_{date_safe}.json"
        return self.stance_dir / filename

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use in filename.

        Args:
            name: Raw string

        Returns:
            Sanitized string safe for filename
        """
        # Replace unsafe characters with underscores
        safe = name.replace('/', '_').replace('\\', '_').replace(' ', '_')
        safe = ''.join(c for c in safe if c.isalnum() or c in '_-.')
        return safe.lower()

    def _load_stats(self) -> Dict:
        """Load cache statistics from file.

        Returns:
            Statistics dictionary
        """
        if not self.stats_file.exists():
            return {
                'hits': 0,
                'misses': 0,
                'total_entries': 0,
                'created_at': datetime.now().isoformat()
            }

        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache stats: {e}")
            return {
                'hits': 0,
                'misses': 0,
                'total_entries': 0,
                'created_at': datetime.now().isoformat()
            }

    def _save_stats(self):
        """Save cache statistics to file."""
        try:
            self.stats['updated_at'] = datetime.now().isoformat()
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2)
        except (IOError, OSError) as e:
            logger.warning(f"Failed to save cache stats: {e}")

    def get_stats(self) -> Dict:
        """Get cache statistics.

        Returns:
            {
                'hits': int,
                'misses': int,
                'hit_rate': float (0.0-1.0),
                'total_entries': int,
                'cache_size_mb': float,
                'oldest_entry_days': int,
                ...
            }
        """
        hits = self.stats.get('hits', 0)
        misses = self.stats.get('misses', 0)
        total_requests = hits + misses

        hit_rate = hits / total_requests if total_requests > 0 else 0.0

        # Calculate cache size
        cache_size_bytes = sum(
            f.stat().st_size
            for f in self.stance_dir.glob('*.json')
            if f.is_file()
        )
        cache_size_mb = cache_size_bytes / (1024 * 1024)

        # Find oldest entry
        oldest_days = 0
        stance_files = list(self.stance_dir.glob('*.json'))
        if stance_files:
            oldest_file = min(stance_files, key=lambda f: f.stat().st_mtime)
            oldest_timestamp = datetime.fromtimestamp(oldest_file.stat().st_mtime)
            oldest_days = (datetime.now() - oldest_timestamp).days

        return {
            'hits': hits,
            'misses': misses,
            'hit_rate': round(hit_rate, 3),
            'total_entries': self.stats.get('total_entries', 0),
            'cache_files': len(stance_files),
            'cache_size_mb': round(cache_size_mb, 2),
            'oldest_entry_days': oldest_days,
            'retention_days': self.retention_days,
            'cache_dir': str(self.cache_dir)
        }

    def cleanup_old_entries(self) -> int:
        """Remove cache entries older than retention period.

        Returns:
            Number of entries removed
        """
        if self.retention_days <= 0:
            logger.info("Cache cleanup disabled (retention_days <= 0)")
            return 0

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0

        for cache_file in self.stance_dir.glob('*.json'):
            try:
                file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    cache_file.unlink()
                    removed_count += 1
                    logger.debug(f"Removed old cache entry: {cache_file.name}")
            except (OSError, IOError) as e:
                logger.warning(f"Failed to remove {cache_file}: {e}")

        if removed_count > 0:
            logger.info(
                f"Cleaned up {removed_count} cache entries older than "
                f"{self.retention_days} days"
            )

            # Update stats
            self.stats['total_entries'] = max(
                0,
                self.stats.get('total_entries', 0) - removed_count
            )
            self._save_stats()

        return removed_count

    def clear_cache(self) -> int:
        """Clear all cached stance analyses.

        WARNING: This removes all cached results. Use with caution.

        Returns:
            Number of entries removed
        """
        removed_count = 0

        for cache_file in self.stance_dir.glob('*.json'):
            try:
                cache_file.unlink()
                removed_count += 1
            except (OSError, IOError) as e:
                logger.warning(f"Failed to remove {cache_file}: {e}")

        logger.warning(f"Cleared all cache: {removed_count} entries removed")

        # Reset stats
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_entries': 0,
            'created_at': datetime.now().isoformat()
        }
        self._save_stats()

        return removed_count

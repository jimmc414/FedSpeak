"""GDELT Project API client for media coverage analysis.

This module provides integration with the GDELT (Global Database of Events,
Language, and Tone) Project for analyzing media coverage of FOMC language shifts.

GDELT monitors 100,000+ news sources in 65 languages globally and provides
free, unlimited API access with no authentication required.

API Documentation: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import requests
import pytz

logger = logging.getLogger(__name__)


class GDELTClient:
    """Client for GDELT Project DOC 2.0 API.

    Provides methods to search global news coverage for specific terms and
    calculate media coverage metrics around FOMC statement releases.

    Features:
    - Free, unlimited API access (no key required)
    - 100,000+ global news sources
    - Built-in tone/sentiment scores
    - Real-time updates (15-minute delay)
    - Historical data back to 2015
    """

    # GDELT DOC 2.0 API endpoint
    API_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    # Default search parameters
    DEFAULT_MAX_RECORDS = 250  # GDELT limit per query
    DEFAULT_TIMEOUT = 30  # seconds

    # High-quality financial news sources (for filtering)
    PRIORITY_SOURCES = [
        'reuters.com',
        'bloomberg.com',
        'wsj.com',
        'ft.com',
        'nytimes.com',
        'cnbc.com',
        'marketwatch.com',
        'apnews.com',
        'federalreserve.gov',
        'economist.com'
    ]

    def __init__(self,
                 rate_limit: Optional[int] = None,
                 timeout: int = DEFAULT_TIMEOUT):
        """Initialize GDELT client.

        Args:
            rate_limit: Optional rate limit (requests per second).
                       None = unlimited (GDELT has no limits)
            timeout: Request timeout in seconds (default: 30)
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.last_request_time = None

        logger.info(
            f"Initialized GDELT client (rate_limit={rate_limit}, timeout={timeout}s)"
        )

    def search(self,
               query: str,
               start_date: str,
               end_date: Optional[str] = None,
               max_records: int = DEFAULT_MAX_RECORDS,
               source_country: Optional[str] = None,
               source_language: str = "english") -> List[Dict]:
        """Search GDELT for news articles matching query in date range.

        Args:
            query: Search query (e.g., "FOMC AND transitory")
            start_date: Start datetime in format YYYYMMDDHHMMSS or YYYYMMDD
            end_date: End datetime (defaults to start_date + 24 hours)
            max_records: Maximum articles to return (default: 250, GDELT limit)
            source_country: Filter by source country code (e.g., "US")
            source_language: Filter by language (default: "english")

        Returns:
            List of article dictionaries with fields:
            - url: Article URL
            - title: Article title
            - seendate: When GDELT first saw the article (YYYYMMDDHHMMSS)
            - socialimage: Social media preview image URL
            - domain: Source domain
            - language: Article language
            - sourcecountry: Source country code
            - tone: GDELT tone score (more negative to more positive)

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        # Respect rate limit if configured
        self._apply_rate_limit()

        # Parse and validate dates
        start_dt = self._parse_date(start_date)

        if end_date:
            end_dt = self._parse_date(end_date)
        else:
            # Default: 24-hour window
            end_dt = start_dt + timedelta(hours=24)

        # Build query parameters
        params = {
            'query': query,
            'mode': 'artlist',  # Article list mode
            'format': 'json',
            'maxrecords': min(max_records, self.DEFAULT_MAX_RECORDS),
            'startdatetime': start_dt.strftime('%Y%m%d%H%M%S'),
            'enddatetime': end_dt.strftime('%Y%m%d%H%M%S'),
            'sourcelang': source_language
        }

        if source_country:
            params['sourcecountry'] = source_country

        logger.info(
            f"GDELT search: query='{query}', "
            f"window={start_dt} to {end_dt}, max={max_records}"
        )

        try:
            # Make API request
            response = requests.get(
                self.API_BASE_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract articles from response
            articles = data.get('articles', [])

            logger.info(f"GDELT returned {len(articles)} articles")

            return articles

        except requests.exceptions.Timeout:
            logger.error(f"GDELT request timeout after {self.timeout}s")
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"GDELT API error: {e}")
            raise

        except (ValueError, KeyError) as e:
            logger.error(f"GDELT response parsing error: {e}")
            return []

    def search_fomc_coverage(self,
                             term: str,
                             fomc_date: str,
                             window_hours: int = 24) -> List[Dict]:
        """Search for FOMC-related coverage of a specific term.

        Constructs a focused query combining FOMC context with the term of interest,
        and searches within a time window after the FOMC statement release.

        Args:
            term: Term to search for (e.g., "transitory", "inflation")
            fomc_date: FOMC statement date (YYYYMMDD)
            window_hours: Hours after FOMC release to search (default: 24)

        Returns:
            List of article dictionaries from GDELT search
        """
        # Build FOMC-specific query
        # Combine FOMC context with term, require policy-related keywords
        query = f'(FOMC OR "Federal Reserve") AND {term} AND (statement OR policy OR monetary)'

        # Parse FOMC date (assume 2:00 PM ET release time)
        fomc_dt = datetime.strptime(fomc_date, '%Y%m%d')
        et_tz = pytz.timezone('America/New_York')
        release_time = et_tz.localize(
            datetime(fomc_dt.year, fomc_dt.month, fomc_dt.day, 14, 0)
        )

        # Convert to UTC (GDELT uses UTC)
        release_time_utc = release_time.astimezone(pytz.utc)
        end_time_utc = release_time_utc + timedelta(hours=window_hours)

        logger.info(
            f"Searching FOMC coverage: term='{term}', "
            f"date={fomc_date}, window={window_hours}h"
        )

        # Search GDELT
        return self.search(
            query=query,
            start_date=release_time_utc.strftime('%Y%m%d%H%M%S'),
            end_date=end_time_utc.strftime('%Y%m%d%H%M%S'),
            source_language='english'
        )

    def calculate_coverage_metrics(self, articles: List[Dict]) -> Dict:
        """Calculate media coverage metrics from article list.

        Args:
            articles: List of article dictionaries from GDELT search

        Returns:
            Dictionary with metrics:
            - total_articles: Total number of articles
            - unique_sources: Number of unique source domains
            - priority_sources: Number of articles from high-quality sources
            - avg_tone: Average GDELT tone score
            - tone_std: Standard deviation of tone scores
            - sources_list: List of unique source domains
            - priority_sources_list: List of priority sources that published
        """
        if not articles:
            return {
                'total_articles': 0,
                'unique_sources': 0,
                'priority_sources': 0,
                'avg_tone': 0.0,
                'tone_std': 0.0,
                'sources_list': [],
                'priority_sources_list': []
            }

        # Extract domains
        domains = []
        for article in articles:
            domain = article.get('domain', '').lower()
            if domain:
                domains.append(domain)

        unique_sources = list(set(domains))

        # Count priority sources
        priority_found = [
            src for src in unique_sources
            if any(priority in src for priority in self.PRIORITY_SOURCES)
        ]

        # Calculate tone statistics
        tone_scores = []
        for article in articles:
            tone = article.get('tone')
            if tone is not None:
                try:
                    tone_scores.append(float(tone))
                except (ValueError, TypeError):
                    pass

        if tone_scores:
            avg_tone = sum(tone_scores) / len(tone_scores)

            # Calculate standard deviation
            variance = sum((x - avg_tone) ** 2 for x in tone_scores) / len(tone_scores)
            tone_std = variance ** 0.5
        else:
            avg_tone = 0.0
            tone_std = 0.0

        return {
            'total_articles': len(articles),
            'unique_sources': len(unique_sources),
            'priority_sources': len(priority_found),
            'avg_tone': round(avg_tone, 2),
            'tone_std': round(tone_std, 2),
            'sources_list': sorted(unique_sources),
            'priority_sources_list': sorted(priority_found)
        }

    def filter_priority_sources(self, articles: List[Dict]) -> List[Dict]:
        """Filter articles to only include high-quality news sources.

        Args:
            articles: List of article dictionaries

        Returns:
            Filtered list containing only articles from priority sources
        """
        filtered = []

        for article in articles:
            domain = article.get('domain', '').lower()

            if any(priority in domain for priority in self.PRIORITY_SOURCES):
                filtered.append(article)

        logger.debug(
            f"Filtered to priority sources: {len(filtered)}/{len(articles)} articles"
        )

        return filtered

    def get_top_articles(self, articles: List[Dict], n: int = 20) -> List[Dict]:
        """Get top N articles by relevance/prominence.

        Sorts articles by a combination of:
        1. Priority source status (high-quality sources ranked higher)
        2. Absolute tone score (stronger sentiment = more prominent)

        Args:
            articles: List of article dictionaries
            n: Number of top articles to return (default: 20)

        Returns:
            List of top N articles sorted by relevance
        """
        def article_score(article: Dict) -> float:
            """Calculate article relevance score."""
            score = 0.0

            # Priority source bonus (50 points)
            domain = article.get('domain', '').lower()
            if any(priority in domain for priority in self.PRIORITY_SOURCES):
                score += 50.0

            # Tone significance (0-50 points based on absolute tone)
            tone = article.get('tone')
            if tone is not None:
                try:
                    # Higher absolute tone = more prominent coverage
                    score += min(abs(float(tone)), 50.0)
                except (ValueError, TypeError):
                    pass

            return score

        # Sort by score (descending)
        sorted_articles = sorted(
            articles,
            key=article_score,
            reverse=True
        )

        return sorted_articles[:n]

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object.

        Accepts formats: YYYYMMDD, YYYYMMDDHHMMSS

        Args:
            date_str: Date string

        Returns:
            datetime object (naive, assumes UTC)

        Raises:
            ValueError: If date format is invalid
        """
        date_str = str(date_str).strip()

        if len(date_str) == 8:
            # YYYYMMDD
            return datetime.strptime(date_str, '%Y%m%d')
        elif len(date_str) == 14:
            # YYYYMMDDHHMMSS
            return datetime.strptime(date_str, '%Y%m%d%H%M%S')
        else:
            raise ValueError(
                f"Invalid date format: {date_str}. "
                "Expected YYYYMMDD or YYYYMMDDHHMMSS"
            )

    def _apply_rate_limit(self):
        """Apply rate limiting if configured."""
        if self.rate_limit is None:
            return

        if self.last_request_time is not None:
            # Calculate minimum time between requests
            min_interval = 1.0 / self.rate_limit

            # Calculate time since last request
            elapsed = time.time() - self.last_request_time

            # Sleep if needed
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self.last_request_time = time.time()

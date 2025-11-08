"""RSS feed monitoring for Federal Reserve FOMC policy statements.

This module provides real-time monitoring of the Federal Reserve's monetary policy
press releases RSS feed to detect new FOMC policy statements.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import feedparser
import requests
from bs4 import BeautifulSoup

from src.config.settings import get_settings
from src.exceptions import DataError

logger = logging.getLogger(__name__)


class RSSMonitor:
    """Monitor Federal Reserve RSS feed for new FOMC policy statements.

    Polls the Fed's monetary policy press releases RSS feed, identifies new
    policy statements, and tracks which statements have been processed.

    Attributes:
        feed_url: URL of the Fed's RSS feed
        processed_statements: Set of statement dates already processed
        data_dir: Directory to save processed statement texts
    """

    def __init__(self, feed_url: Optional[str] = None, data_dir: Optional[Path] = None):
        """Initialize RSS monitor.

        Args:
            feed_url: RSS feed URL (defaults to config value)
            data_dir: Directory for processed statements (defaults to config value)
        """
        settings = get_settings()

        self.feed_url = feed_url or settings.get(
            'monitoring.rss_feed_url',
            default='https://www.federalreserve.gov/feeds/press_monetary.xml'
        )

        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = settings.get_path('corpus.data_dir', default='data')
            self.data_dir = self.data_dir / settings.get(
                'corpus.processed_subdir',
                default='processed'
            )

        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Track processed statements to avoid reprocessing
        self.processed_statements: set = set()
        self._load_processed_statements()

        logger.info(f"RSSMonitor initialized: feed={self.feed_url}, data_dir={self.data_dir}")

    def _load_processed_statements(self) -> None:
        """Load list of already processed policy statements from data directory."""
        # Check existing policy statement files
        statement_files = list(self.data_dir.glob('policy_statement_*.txt'))

        for file_path in statement_files:
            # Skip .html.txt duplicates
            if file_path.name.endswith('.html.txt'):
                continue

            # Extract date from filename: policy_statement_20211215.txt -> 20211215
            date_match = re.search(r'policy_statement_(\d{8})\.txt', file_path.name)
            if date_match:
                self.processed_statements.add(date_match.group(1))

        logger.info(f"Loaded {len(self.processed_statements)} processed statements from {self.data_dir}")

    def check_feed(self) -> List[Dict[str, str]]:
        """Check RSS feed for new FOMC policy statements.

        Returns:
            List of new statement dictionaries with keys:
                - 'title': Statement title
                - 'link': URL to statement
                - 'published': Publication date (ISO format)
                - 'date': Statement date (YYYYMMDD format)

        Raises:
            DataError: If RSS feed cannot be fetched or parsed
        """
        logger.info(f"Checking RSS feed: {self.feed_url}")

        try:
            feed = feedparser.parse(self.feed_url)

            if feed.bozo:
                # feedparser sets bozo=1 if there are parsing issues
                logger.warning(f"RSS feed parsing issue: {feed.bozo_exception}")

            if not feed.entries:
                logger.warning("RSS feed returned no entries")
                return []

            logger.info(f"RSS feed returned {len(feed.entries)} entries")

        except Exception as e:
            raise DataError(f"Failed to fetch RSS feed: {e}") from e

        # Filter for FOMC policy statements
        new_statements = []

        for entry in feed.entries:
            # Check if entry is a policy statement
            if not self._is_policy_statement(entry):
                continue

            # Extract statement date from title or link
            statement_date = self._extract_statement_date(entry)
            if not statement_date:
                logger.warning(f"Could not extract date from entry: {entry.get('title', 'no title')}")
                continue

            # Check if already processed
            if statement_date in self.processed_statements:
                logger.debug(f"Statement {statement_date} already processed, skipping")
                continue

            # New statement found
            new_statement = {
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'date': statement_date
            }

            new_statements.append(new_statement)
            logger.info(f"New statement found: {statement_date} - {new_statement['title']}")

        logger.info(f"Found {len(new_statements)} new policy statements")
        return new_statements

    def _is_policy_statement(self, entry: feedparser.FeedParserDict) -> bool:
        """Check if RSS entry is a FOMC policy statement.

        Args:
            entry: RSS feed entry

        Returns:
            True if entry is a policy statement, False otherwise
        """
        title = entry.get('title', '').lower()
        link = entry.get('link', '').lower()

        # Look for "fomc" and "statement" in title
        if 'fomc' in title and 'statement' in title:
            return True

        # Look for policy statement URL pattern
        if 'monetary' in link and '.htm' in link:
            # Federal Reserve policy statement URLs: .../monetary20211215a.htm
            if re.search(r'monetary\d{8}[a-z]\.htm', link):
                return True

        return False

    def _extract_statement_date(self, entry: feedparser.FeedParserDict) -> Optional[str]:
        """Extract statement date in YYYYMMDD format from RSS entry.

        Args:
            entry: RSS feed entry

        Returns:
            Statement date in YYYYMMDD format, or None if not found
        """
        link = entry.get('link', '')

        # Try to extract from URL pattern: .../monetary20211215a.htm
        date_match = re.search(r'monetary(\d{8})[a-z]\.htm', link)
        if date_match:
            return date_match.group(1)

        # Try to extract from published date
        published = entry.get('published', '')
        if published:
            try:
                # Parse various date formats
                pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')
                return pub_date.strftime('%Y%m%d')
            except ValueError:
                pass

        return None

    def download_statement(self, statement: Dict[str, str]) -> Path:
        """Download and save policy statement text.

        Args:
            statement: Statement dictionary with 'link' and 'date' keys

        Returns:
            Path to saved statement text file

        Raises:
            DataError: If statement cannot be downloaded or parsed
        """
        url = statement['link']
        date = statement['date']

        logger.info(f"Downloading statement {date} from {url}")

        try:
            settings = get_settings()
            timeout = settings.get('download.timeout_seconds', default=30)
            user_agent = settings.get('download.user_agent', default='FedSpeak/1.0 (Academic Research)')

            headers = {'User-Agent': user_agent}
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

        except requests.RequestException as e:
            raise DataError(f"Failed to download statement from {url}: {e}") from e

        # Parse HTML and extract text
        try:
            soup = BeautifulSoup(response.content, 'lxml')

            # Federal Reserve statement pages typically have content in main div
            content_div = soup.find('div', {'id': 'content'}) or soup.find('div', {'class': 'col-xs-12'})

            if content_div:
                text = content_div.get_text(separator='\n', strip=True)
            else:
                # Fallback: get all text
                text = soup.get_text(separator='\n', strip=True)

            if not text or len(text) < 100:
                raise DataError(f"Extracted text too short ({len(text)} chars), likely parsing error")

        except Exception as e:
            raise DataError(f"Failed to parse statement HTML: {e}") from e

        # Save to file
        output_file = self.data_dir / f'policy_statement_{date}.txt'
        output_file.write_text(text, encoding='utf-8')

        # Mark as processed
        self.processed_statements.add(date)

        logger.info(f"Saved statement to {output_file} ({len(text)} chars)")
        return output_file

    def process_new_statements(self) -> List[str]:
        """Check feed and download all new statements.

        Returns:
            List of statement dates (YYYYMMDD format) that were newly downloaded
        """
        new_statements = self.check_feed()

        downloaded_dates = []

        for statement in new_statements:
            try:
                self.download_statement(statement)
                downloaded_dates.append(statement['date'])
            except DataError as e:
                logger.error(f"Failed to download statement {statement['date']}: {e}")
                continue

        return downloaded_dates

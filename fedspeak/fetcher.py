"""
Document fetcher module for FedSpeak.
Downloads FOMC minutes and statements from federalreserve.gov.

Based on:
- Document 01 URL patterns and availability findings
- Architecture Section 3.1 (Document Fetcher design)
- Requirements REQ-DA-001 to REQ-DA-010
"""

import requests
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """Result of document download operation."""
    success: bool
    doc_type: str
    date: str
    filepath: Optional[Path] = None
    file_size: int = 0
    url: str = ""
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


class DocumentFetcher:
    """
    Fetches Federal Reserve documents.

    URL patterns work from 2008+ (Document 01 finding).
    Pre-2008 documents return 404 errors.
    """

    def __init__(self, config: Dict):
        """
        Initialize fetcher with configuration.

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.output_dir = Path(config['corpus']['data_dir']) / config['corpus']['raw_subdir']
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create session with user agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config['download']['user_agent']
        })

        self.url_templates = config['url_templates']
        self.delay = config['download']['delay_seconds']
        self.max_retries = config['download']['retry_attempts']
        self.timeout = config['download']['timeout_seconds']
        self.backoff_base = config['download']['backoff_base']

        logger.info(f"DocumentFetcher initialized. Output: {self.output_dir}")

    def download_document(self, doc_type: str, date: str) -> DownloadResult:
        """
        Download single document with retry logic.

        Args:
            doc_type: 'policy_statement' or 'fomc_minutes'
            date: Date in YYYYMMDD format (e.g., '20211215')

        Returns:
            DownloadResult with status and metadata
        """
        # Construct URL
        url = self._construct_url(doc_type, date)

        # Construct filepath
        filepath = self.output_dir / f"{doc_type}_{date}.html"

        logger.info(f"Downloading {doc_type} for {date}")

        # Retry loop with exponential backoff
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)

                if response.status_code == 200:
                    # Success - save file
                    filepath.write_bytes(response.content)
                    file_size = len(response.content)

                    logger.info(f"✓ Downloaded {filepath.name} ({file_size} bytes)")

                    # Rate limiting - respectful delay
                    time.sleep(self.delay)

                    return DownloadResult(
                        success=True,
                        doc_type=doc_type,
                        date=date,
                        filepath=filepath,
                        file_size=file_size,
                        url=url,
                        timestamp=datetime.now()
                    )

                elif response.status_code == 404:
                    # Document doesn't exist (not an error for pre-2008 docs)
                    logger.warning(f"404 Not Found: {url}")
                    return DownloadResult(
                        success=False,
                        doc_type=doc_type,
                        date=date,
                        url=url,
                        error="404 Not Found - document may not exist",
                        timestamp=datetime.now()
                    )

                else:
                    # Other HTTP error
                    response.raise_for_status()

            except requests.exceptions.Timeout:
                wait_time = self.backoff_base * (2 ** (attempt - 1))
                logger.warning(f"Timeout on attempt {attempt}/{self.max_retries}, "
                             f"retrying in {wait_time}s")
                if attempt < self.max_retries:
                    time.sleep(wait_time)
                else:
                    return DownloadResult(
                        success=False,
                        doc_type=doc_type,
                        date=date,
                        url=url,
                        error=f"Timeout after {self.max_retries} attempts",
                        timestamp=datetime.now()
                    )

            except requests.exceptions.RequestException as e:
                wait_time = self.backoff_base * (2 ** (attempt - 1))
                logger.warning(f"Request error on attempt {attempt}/{self.max_retries}: {e}")
                if attempt < self.max_retries:
                    time.sleep(wait_time)
                else:
                    return DownloadResult(
                        success=False,
                        doc_type=doc_type,
                        date=date,
                        url=url,
                        error=f"Request failed: {str(e)}",
                        timestamp=datetime.now()
                    )

        # Should not reach here, but handle gracefully
        return DownloadResult(
            success=False,
            doc_type=doc_type,
            date=date,
            url=url,
            error="Unknown error",
            timestamp=datetime.now()
        )

    def download_batch(self,
                      doc_type: str,
                      start_date: datetime,
                      end_date: datetime) -> List[DownloadResult]:
        """
        Download multiple documents within date range.

        Note: FOMC meets approximately 8 times per year on irregular schedule.
        This method attempts downloads for likely meeting dates.

        Args:
            doc_type: 'policy_statement' or 'fomc_minutes'
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of DownloadResult objects
        """
        results = []

        # Generate candidate dates (approximate FOMC schedule)
        # In production, parse calendar from federalreserve.gov/monetarypolicy/fomccalendars.htm
        candidate_dates = self._generate_fomc_dates(start_date, end_date)

        logger.info(f"Batch download: {len(candidate_dates)} candidate dates")

        for date_str in candidate_dates:
            result = self.download_document(doc_type, date_str)
            results.append(result)

            # Save metadata
            self._save_metadata(result)

        successful = sum(1 for r in results if r.success)
        logger.info(f"Batch complete: {successful}/{len(results)} successful")

        return results

    def _construct_url(self, doc_type: str, date: str) -> str:
        """Construct document URL from template."""
        template = self.url_templates.get(doc_type)
        if not template:
            raise ValueError(f"Unknown document type: {doc_type}")

        return template.format(date=date)

    def _generate_fomc_dates(self,
                            start_date: datetime,
                            end_date: datetime) -> List[str]:
        """
        Generate candidate FOMC meeting dates.

        Simplified version - assumes 8 meetings per year.
        Production version should parse actual calendar.
        """
        dates = []

        # Typical FOMC schedule: Jan/Feb, Mar, Apr/May, Jun, Jul, Sep, Oct/Nov, Dec
        # Approximate as every 6 weeks
        current = start_date
        while current <= end_date:
            dates.append(current.strftime('%Y%m%d'))
            # Next meeting ~6 weeks later
            import datetime as dt
            current = current + dt.timedelta(days=42)

        return dates

    def _save_metadata(self, result: DownloadResult):
        """Save download metadata to JSON file."""
        metadata_dir = Path(self.config['corpus']['data_dir']) / self.config['corpus']['metadata_subdir']
        metadata_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = metadata_dir / 'download_log.json'

        # Load existing metadata
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = []

        # Append new result
        metadata.append({
            'doc_type': result.doc_type,
            'date': result.date,
            'success': result.success,
            'filepath': str(result.filepath) if result.filepath else None,
            'file_size': result.file_size,
            'url': result.url,
            'error': result.error,
            'timestamp': result.timestamp.isoformat() if result.timestamp else None
        })

        # Save updated metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)


# Example usage
if __name__ == '__main__':
    # Simple test
    import yaml

    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    fetcher = DocumentFetcher(config)

    # Download December 2021 statement (transitory removal)
    result = fetcher.download_document('policy_statement', '20211215')

    if result.success:
        print(f"✓ Downloaded: {result.filepath}")
    else:
        print(f"✗ Failed: {result.error}")

#!/usr/bin/env python3
"""
FedSpeak Document Downloader
Downloads Federal Reserve communications for corpus analysis.
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class FedDocDownloader:
    """Downloads and organizes Federal Reserve documents."""

    BASE_URL = "https://www.federalreserve.gov"

    # URL templates for different document types
    URL_TEMPLATES = {
        'fomc_minutes': '/monetarypolicy/fomcminutes{date}.htm',
        'policy_statement': '/newsevents/pressreleases/monetary{date}a.htm',
        'beige_book': '/monetarypolicy/beigebook{date}.htm',
        'press_transcript': '/mediacenter/files/FOMCpresconf{date}.pdf'
    }

    def __init__(self, output_dir: str = "data/raw"):
        """Initialize downloader with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Academic Research Bot)'
        })

    def download_document(
        self,
        doc_type: str,
        date: str,
        title: str = ""
    ) -> Dict[str, any]:
        """
        Download a single Fed document.

        Args:
            doc_type: Type of document (fomc_minutes, policy_statement, etc.)
            date: Date in YYYYMMDD format
            title: Optional title for metadata

        Returns:
            Dictionary with download metadata
        """
        # Format URL based on document type
        url_path = self.URL_TEMPLATES.get(doc_type)
        if not url_path:
            raise ValueError(f"Unknown document type: {doc_type}")

        url = self.BASE_URL + url_path.format(date=date)

        # Determine file extension
        ext = '.pdf' if doc_type == 'press_transcript' else '.html'

        # Create filename
        filename = f"{doc_type}_{date}{ext}"
        filepath = self.output_dir / filename

        metadata = {
            'doc_type': doc_type,
            'date': date,
            'formatted_date': self._format_date(date),
            'url': url,
            'filename': filename,
            'title': title,
            'download_timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'file_size': None,
            'error': None
        }

        try:
            print(f"Downloading {doc_type} from {date}...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Save the file
            with open(filepath, 'wb') as f:
                f.write(response.content)

            metadata['status'] = 'success'
            metadata['file_size'] = len(response.content)
            print(f"  ✓ Saved to {filepath} ({len(response.content):,} bytes)")

            # Be respectful - add delay between requests
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            metadata['status'] = 'failed'
            metadata['error'] = str(e)
            print(f"  ✗ Failed: {e}")

        self.metadata.append(metadata)
        return metadata

    def download_batch(self, documents: List[Dict[str, str]]):
        """
        Download multiple documents.

        Args:
            documents: List of dicts with 'doc_type', 'date', and optional 'title'
        """
        print(f"\nDownloading {len(documents)} documents...")
        print("=" * 60)

        for doc in documents:
            self.download_document(
                doc_type=doc['doc_type'],
                date=doc['date'],
                title=doc.get('title', '')
            )

        print("\n" + "=" * 60)
        print(f"Download complete: {self._get_success_count()} successful, "
              f"{self._get_failed_count()} failed")

    def save_metadata(self, filepath: str = "data/raw/download_metadata.json"):
        """Save download metadata to JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        print(f"\nMetadata saved to {filepath}")

    def _format_date(self, date: str) -> str:
        """Convert YYYYMMDD to readable format."""
        try:
            dt = datetime.strptime(date, '%Y%m%d')
            return dt.strftime('%B %d, %Y')
        except ValueError:
            return date

    def _get_success_count(self) -> int:
        """Count successful downloads."""
        return sum(1 for m in self.metadata if m['status'] == 'success')

    def _get_failed_count(self) -> int:
        """Count failed downloads."""
        return sum(1 for m in self.metadata if m['status'] == 'failed')


def get_sample_documents() -> List[Dict[str, str]]:
    """
    Define sample documents for corpus analysis.
    Based on Document 01 plan: ~25 documents across different eras.
    """
    documents = []

    # FOMC Minutes: 3 per decade (12 total)
    # 1990s
    documents.extend([
        {'doc_type': 'fomc_minutes', 'date': '19931116', 'title': 'Nov 1993 Minutes'},
        {'doc_type': 'fomc_minutes', 'date': '19950201', 'title': 'Feb 1995 Minutes'},
        {'doc_type': 'fomc_minutes', 'date': '19990330', 'title': 'Mar 1999 Minutes'},
    ])

    # 2000s
    documents.extend([
        {'doc_type': 'fomc_minutes', 'date': '20010130', 'title': 'Jan 2001 Minutes'},
        {'doc_type': 'fomc_minutes', 'date': '20050630', 'title': 'Jun 2005 Minutes'},
        {'doc_type': 'fomc_minutes', 'date': '20081216', 'title': 'Dec 2008 Minutes (Financial Crisis)'},
    ])

    # 2010s
    documents.extend([
        {'doc_type': 'fomc_minutes', 'date': '20101214', 'title': 'Dec 2010 Minutes (QE Era)'},
        {'doc_type': 'fomc_minutes', 'date': '20131218', 'title': 'Dec 2013 Minutes (Taper Tantrum)'},
        {'doc_type': 'fomc_minutes', 'date': '20180926', 'title': 'Sep 2018 Minutes (Normalization)'},
    ])

    # 2020s
    documents.extend([
        {'doc_type': 'fomc_minutes', 'date': '20200429', 'title': 'Apr 2020 Minutes (COVID Response)'},
        {'doc_type': 'fomc_minutes', 'date': '20210728', 'title': 'Jul 2021 Minutes (Transitory Inflation)'},
        {'doc_type': 'fomc_minutes', 'date': '20230201', 'title': 'Feb 2023 Minutes (Tightening Cycle)'},
    ])

    # Policy Statements: 6 spanning 2000-2025
    documents.extend([
        {'doc_type': 'policy_statement', 'date': '20030625', 'title': 'Jun 2003 Statement'},
        {'doc_type': 'policy_statement', 'date': '20081216', 'title': 'Dec 2008 Statement (ZIRP)'},
        {'doc_type': 'policy_statement', 'date': '20130918', 'title': 'Sep 2013 Statement'},
        {'doc_type': 'policy_statement', 'date': '20181219', 'title': 'Dec 2018 Statement'},
        {'doc_type': 'policy_statement', 'date': '20210616', 'title': 'Jun 2021 Statement'},
        {'doc_type': 'policy_statement', 'date': '20230322', 'title': 'Mar 2023 Statement'},
    ])

    # Beige Book: 3 from different eras
    documents.extend([
        {'doc_type': 'beige_book', 'date': '200501', 'title': 'Jan 2005 Beige Book'},
        {'doc_type': 'beige_book', 'date': '201503', 'title': 'Mar 2015 Beige Book'},
        {'doc_type': 'beige_book', 'date': '202301', 'title': 'Jan 2023 Beige Book'},
    ])

    # Press Conference Transcripts: 4 from 2011-2025
    # Note: These are PDFs and may have different availability
    documents.extend([
        {'doc_type': 'press_transcript', 'date': '20130619', 'title': 'Jun 2013 Press Conference'},
        {'doc_type': 'press_transcript', 'date': '20161214', 'title': 'Dec 2016 Press Conference'},
        {'doc_type': 'press_transcript', 'date': '20200429', 'title': 'Apr 2020 Press Conference'},
        {'doc_type': 'press_transcript', 'date': '20230322', 'title': 'Mar 2023 Press Conference'},
    ])

    return documents


def main():
    """Main execution function."""
    print("FedSpeak Document Downloader")
    print("=" * 60)

    # Initialize downloader
    downloader = FedDocDownloader(output_dir="data/raw")

    # Get sample documents
    documents = get_sample_documents()

    print(f"\nPreparing to download {len(documents)} sample documents:")
    print(f"  - FOMC Minutes: 12")
    print(f"  - Policy Statements: 6")
    print(f"  - Beige Book Reports: 3")
    print(f"  - Press Transcripts: 4")
    print(f"  - Total: 25 documents\n")

    # Download all documents
    downloader.download_batch(documents)

    # Save metadata
    downloader.save_metadata()

    print("\n✓ Download process complete!")


if __name__ == "__main__":
    main()

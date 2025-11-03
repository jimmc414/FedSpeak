#!/usr/bin/env python3
"""
FedSpeak Text Extraction and Analysis
Extracts text from downloaded Fed documents and performs corpus analysis.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

import pdfplumber
from bs4 import BeautifulSoup
import pandas as pd


class FedDocExtractor:
    """Extracts and analyzes text from Federal Reserve documents."""

    def __init__(self, input_dir: str = "data/raw", output_dir: str = "data/processed"):
        """Initialize extractor with input and output directories."""
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.extraction_results = []
        self.text_stats = []

    def extract_html(self, filepath: Path) -> Dict[str, any]:
        """
        Extract text from HTML document.

        Returns dict with:
        - text: extracted text
        - word_count: number of words
        - structure: identified structural elements
        - success: True/False
        - error: error message if failed
        """
        result = {
            'filename': filepath.name,
            'format': 'html',
            'success': False,
            'text': '',
            'word_count': 0,
            'structure': {},
            'error': None
        }

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'lxml')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Identify structure
            result['structure'] = self._analyze_html_structure(soup)

            # Extract main content
            # Try multiple approaches for different Fed website versions

            # Modern format (2013+): Look for article div
            main_content = soup.find('div', {'id': 'article'})

            # Older format: Look for leftText div
            if not main_content:
                main_content = soup.find('div', {'id': 'leftText'})

            # Alternative: Look for generalContentText
            if not main_content:
                main_content = soup.find('div', {'id': 'generalContentText'})

            # Fallback to body
            if not main_content:
                main_content = soup.body

            if main_content:
                # Get text
                text = main_content.get_text(separator='\n', strip=True)

                # Clean up whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = re.sub(r' +', ' ', text)

                result['text'] = text
                result['word_count'] = len(text.split())
                result['success'] = True
            else:
                result['error'] = "Could not find main content"

        except Exception as e:
            result['error'] = str(e)

        return result

    def extract_pdf(self, filepath: Path) -> Dict[str, any]:
        """
        Extract text from PDF document.

        Returns dict with same structure as extract_html.
        """
        result = {
            'filename': filepath.name,
            'format': 'pdf',
            'success': False,
            'text': '',
            'word_count': 0,
            'structure': {},
            'error': None
        }

        try:
            with pdfplumber.open(filepath) as pdf:
                # Extract metadata
                result['structure']['num_pages'] = len(pdf.pages)
                result['structure']['metadata'] = pdf.metadata

                # Extract text from all pages
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                # Combine text
                text = '\n\n'.join(text_parts)

                # Clean up
                text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

                result['text'] = text
                result['word_count'] = len(text.split())
                result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def _analyze_html_structure(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Analyze structural elements of HTML document."""
        structure = {}

        # Find title
        title_tag = soup.find('title')
        if title_tag:
            structure['title'] = title_tag.get_text(strip=True)

        # Find headings
        headings = []
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                headings.append({
                    'level': level,
                    'text': heading.get_text(strip=True)
                })
        structure['headings'] = headings[:10]  # First 10 headings

        # Find tables
        tables = soup.find_all('table')
        structure['num_tables'] = len(tables)

        # Find lists
        lists = soup.find_all(['ul', 'ol'])
        structure['num_lists'] = len(lists)

        return structure

    def extract_all(self) -> pd.DataFrame:
        """Extract text from all documents in input directory."""
        print("Extracting text from all documents...")
        print("=" * 60)

        # Get all HTML and PDF files
        html_files = list(self.input_dir.glob('*.html'))
        pdf_files = list(self.input_dir.glob('*.pdf'))

        print(f"Found {len(html_files)} HTML and {len(pdf_files)} PDF files\n")

        # Extract from HTML files
        for filepath in sorted(html_files):
            print(f"Extracting {filepath.name}...")
            result = self.extract_html(filepath)
            self.extraction_results.append(result)

            if result['success']:
                print(f"  ✓ Extracted {result['word_count']:,} words")
                # Save extracted text
                self._save_text(result)
            else:
                print(f"  ✗ Failed: {result['error']}")

        # Extract from PDF files
        for filepath in sorted(pdf_files):
            print(f"Extracting {filepath.name}...")
            result = self.extract_pdf(filepath)
            self.extraction_results.append(result)

            if result['success']:
                print(f"  ✓ Extracted {result['word_count']:,} words from {result['structure']['num_pages']} pages")
                # Save extracted text
                self._save_text(result)
            else:
                print(f"  ✗ Failed: {result['error']}")

        print("\n" + "=" * 60)
        print(f"Extraction complete: {self._count_successful()} successful, "
              f"{self._count_failed()} failed")

        return self._create_results_dataframe()

    def _save_text(self, result: Dict[str, any]):
        """Save extracted text to file."""
        output_file = self.output_dir / f"{result['filename']}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['text'])

    def _count_successful(self) -> int:
        """Count successful extractions."""
        return sum(1 for r in self.extraction_results if r['success'])

    def _count_failed(self) -> int:
        """Count failed extractions."""
        return sum(1 for r in self.extraction_results if not r['success'])

    def _create_results_dataframe(self) -> pd.DataFrame:
        """Create pandas DataFrame with extraction results."""
        data = []
        for result in self.extraction_results:
            # Parse document type from filename
            filename = result['filename']
            doc_type = filename.split('_')[0] + '_' + filename.split('_')[1] if '_' in filename else 'unknown'

            # Parse date
            date_match = re.search(r'(\d{8})', filename)
            date = date_match.group(1) if date_match else 'unknown'

            data.append({
                'filename': filename,
                'doc_type': doc_type.replace('.html', '').replace('.pdf', ''),
                'date': date,
                'format': result['format'],
                'success': result['success'],
                'word_count': result['word_count'],
                'error': result['error']
            })

        return pd.DataFrame(data)

    def analyze_text_statistics(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Compute text statistics grouped by document type."""
        print("\n" + "=" * 60)
        print("Text Statistics Analysis")
        print("=" * 60)

        # Filter successful extractions
        success_df = df[df['success'] == True].copy()

        if len(success_df) == 0:
            print("No successful extractions to analyze!")
            return {}

        # Overall statistics
        print(f"\nOverall Statistics:")
        print(f"  Total documents: {len(success_df)}")
        print(f"  Total words: {success_df['word_count'].sum():,}")
        print(f"  Average words per document: {success_df['word_count'].mean():.0f}")
        print(f"  Min words: {success_df['word_count'].min():,}")
        print(f"  Max words: {success_df['word_count'].max():,}")
        print(f"  Median words: {success_df['word_count'].median():.0f}")

        # Statistics by document type
        print(f"\nStatistics by Document Type:")
        print("-" * 60)

        stats_by_type = success_df.groupby('doc_type')['word_count'].agg([
            ('count', 'count'),
            ('min', 'min'),
            ('max', 'max'),
            ('median', 'median'),
            ('mean', 'mean')
        ]).round(0)

        print(stats_by_type.to_string())

        # Statistics by format
        print(f"\nStatistics by Format:")
        print("-" * 60)

        stats_by_format = success_df.groupby('format')['word_count'].agg([
            ('count', 'count'),
            ('min', 'min'),
            ('max', 'max'),
            ('median', 'median'),
            ('mean', 'mean')
        ]).round(0)

        print(stats_by_format.to_string())

        return {
            'by_type': stats_by_type,
            'by_format': stats_by_format
        }

    def save_results(self, df: pd.DataFrame, stats: Dict[str, pd.DataFrame]):
        """Save analysis results to files."""
        # Save extraction results as CSV
        results_file = self.output_dir / 'extraction_results.csv'
        df.to_csv(results_file, index=False)
        print(f"\n✓ Results saved to {results_file}")

        # Save extraction details as JSON
        details_file = self.output_dir / 'extraction_details.json'
        with open(details_file, 'w') as f:
            json.dump(self.extraction_results, f, indent=2, default=str)
        print(f"✓ Detailed results saved to {details_file}")

        # Save statistics
        if stats:
            stats_file = self.output_dir / 'text_statistics.json'
            stats_data = {
                'by_type': stats['by_type'].to_dict(),
                'by_format': stats['by_format'].to_dict()
            }
            with open(stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2)
            print(f"✓ Statistics saved to {stats_file}")

    def sample_document_structure(self, num_samples: int = 3) -> List[Dict[str, any]]:
        """Return structural analysis of sample documents."""
        samples = []

        # Get first few successful extractions
        for result in self.extraction_results:
            if result['success'] and len(samples) < num_samples:
                # Get first 500 chars of text as preview
                preview = result['text'][:500] + '...' if len(result['text']) > 500 else result['text']

                samples.append({
                    'filename': result['filename'],
                    'format': result['format'],
                    'word_count': result['word_count'],
                    'structure': result['structure'],
                    'preview': preview
                })

        return samples


def main():
    """Main execution function."""
    print("FedSpeak Text Extraction and Analysis")
    print("=" * 60)

    # Initialize extractor
    extractor = FedDocExtractor(input_dir="data/raw", output_dir="data/processed")

    # Extract all documents
    results_df = extractor.extract_all()

    # Analyze statistics
    stats = extractor.analyze_text_statistics(results_df)

    # Save results
    extractor.save_results(results_df, stats)

    # Show sample structures
    print("\n" + "=" * 60)
    print("Sample Document Structures")
    print("=" * 60)

    samples = extractor.sample_document_structure(num_samples=3)
    for i, sample in enumerate(samples, 1):
        print(f"\nSample {i}: {sample['filename']}")
        print(f"  Format: {sample['format']}")
        print(f"  Word Count: {sample['word_count']:,}")
        print(f"  Structure: {json.dumps(sample['structure'], indent=4)}")
        print(f"  Preview:\n{sample['preview']}\n")

    print("\n✓ Analysis complete!")


if __name__ == "__main__":
    main()

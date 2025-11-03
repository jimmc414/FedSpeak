"""
Command-line interface for FedSpeak.

Based on:
- Architecture Section 3.6 (CLI design)
- Requirements REQ-INT-001, REQ-INT-002
"""

import argparse
import logging
import sys
import yaml
from pathlib import Path
from datetime import datetime

from fedspeak.fetcher import DocumentFetcher
from fedspeak.extractor import TextExtractor
from fedspeak.analyzer import LanguageAnalyzer
from fedspeak.detector import ShiftDetector
from fedspeak.alerter import AlertGenerator


def setup_logging(level='INFO'):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_config(config_path='config/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def cmd_download(args, config):
    """Download Fed documents."""
    print(f"\n[DOWNLOAD] Starting: {args.start_date} to {args.end_date or 'present'}")

    fetcher = DocumentFetcher(config)

    start = datetime.strptime(args.start_date, '%Y-%m-%d')
    end = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else datetime.now()

    # Download policy statements
    print("\n[DOWNLOAD] Fetching policy statements...")
    results_stmt = fetcher.download_batch('policy_statement', start, end)
    successful_stmt = sum(1 for r in results_stmt if r.success)
    print(f"  >> Downloaded {successful_stmt}/{len(results_stmt)} statements")

    # Download minutes (if requested)
    if not args.statements_only:
        print("\n[DOWNLOAD] Fetching FOMC minutes...")
        results_min = fetcher.download_batch('fomc_minutes', start, end)
        successful_min = sum(1 for r in results_min if r.success)
        print(f"  >> Downloaded {successful_min}/{len(results_min)} minutes")

    print(f"\n[SUCCESS] Download complete!")


def cmd_extract(args, config):
    """Extract text from downloaded documents."""
    print(f"\n[EXTRACT] Processing documents...")

    extractor = TextExtractor(config)

    raw_dir = Path(config['corpus']['data_dir']) / config['corpus']['raw_subdir']
    processed_dir = Path(config['corpus']['data_dir']) / config['corpus']['processed_subdir']
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Find HTML files
    html_files = list(raw_dir.glob('*.html'))
    print(f"Found {len(html_files)} HTML files")

    # Extract each file
    successful = 0
    for filepath in html_files:
        try:
            # Determine doc type from filename
            doc_type = 'fomc_minutes' if 'minutes' in filepath.name else 'policy_statement'

            # Extract
            result = extractor.extract(filepath, doc_type)

            if result.success:
                # Save extracted text
                output_path = processed_dir / f"{filepath.stem}.txt"
                output_path.write_text(result.text)
                successful += 1
                print(f"  [OK] {filepath.name} -> {result.word_count} words")
            else:
                print(f"  [FAIL] {filepath.name}: {result.error}")

        except Exception as e:
            print(f"  [ERROR] {filepath.name}: {e}")

    print(f"\n[SUCCESS] Extraction complete: {successful}/{len(html_files)} successful")


def cmd_analyze(args, config):
    """Analyze corpus for language shifts."""
    print(f"\n[ANALYZE] Processing corpus for language shifts...")

    # Analyze
    analyzer = LanguageAnalyzer(config)
    processed_dir = Path(config['corpus']['data_dir']) / config['corpus']['processed_subdir']
    time_series = analyzer.analyze_corpus(processed_dir)

    print(f"  Analyzed {len(time_series)} observations")

    # Save metrics
    metadata_dir = Path(config['corpus']['data_dir']) / config['corpus']['metadata_subdir']
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = metadata_dir / 'keyword_metrics.csv'
    analyzer.save_metrics(time_series, metrics_path)
    print(f"  >> Metrics saved: {metrics_path}")

    # Detect shifts
    detector = ShiftDetector(config)
    shifts = detector.detect_shifts(time_series)
    print(f"\n[DETECTION] Found {len(shifts)} language shifts:")

    for shift in shifts:
        print(f"  * {shift.shift_type.upper()}: '{shift.word}' on {shift.date.date()}")

    # Generate alerts
    if shifts:
        print(f"\n[ALERTS] Generating alert files...")
        alerter = AlertGenerator(config)

        for shift in shifts:
            alert = alerter.generate_alert(shift, time_series)
            alerter.save_alert(alert)
            print(f"  >> {alert['alert_id']}")

    print(f"\n[SUCCESS] Analysis complete!")


def cmd_report(args, config):
    """Generate summary report."""
    print(f"\n[REPORT] Generating summary...")

    # Load metrics
    metadata_dir = Path(config['corpus']['data_dir']) / config['corpus']['metadata_subdir']
    metrics_path = metadata_dir / 'keyword_metrics.csv'

    if not metrics_path.exists():
        print(f"[ERROR] No metrics found. Run 'analyze' first.")
        return

    import pandas as pd
    metrics = pd.read_csv(metrics_path)

    # Summary statistics
    print(f"\n[SUMMARY] Corpus Statistics:")
    print(f"  Documents analyzed: {metrics['doc_id'].nunique()}")
    print(f"  Keywords tracked: {metrics['word'].nunique()}")
    print(f"  Date range: {metrics['date'].min()} to {metrics['date'].max()}")

    # Top keywords
    print(f"\n[KEYWORDS] Most Frequent Terms:")
    top_words = metrics.groupby('word')['count'].sum().sort_values(ascending=False).head(10)
    for word, count in top_words.items():
        print(f"  {word}: {int(count)} total occurrences")

    print(f"\n[SUCCESS] Report complete!")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='FedSpeak - Federal Reserve Language Shift Detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download 2021 documents
  fedspeak download --start-date 2021-01-01 --end-date 2021-12-31

  # Extract text from downloaded files
  fedspeak extract

  # Analyze for language shifts
  fedspeak analyze

  # Generate summary report
  fedspeak report
        """
    )

    parser.add_argument('--config', default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Download command
    download_parser = subparsers.add_parser('download', help='Download Fed documents')
    download_parser.add_argument('--start-date', required=True,
                                help='Start date (YYYY-MM-DD)')
    download_parser.add_argument('--end-date',
                                help='End date (YYYY-MM-DD), default: today')
    download_parser.add_argument('--statements-only', action='store_true',
                                help='Download only policy statements (not minutes)')

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract text from documents')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze corpus for shifts')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate summary report')

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Load config
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"❌ Config file not found: {args.config}")
        sys.exit(1)

    # Execute command
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'download':
            cmd_download(args, config)
        elif args.command == 'extract':
            cmd_extract(args, config)
        elif args.command == 'analyze':
            cmd_analyze(args, config)
        elif args.command == 'report':
            cmd_report(args, config)
    except Exception as e:
        logging.error(f"Command failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

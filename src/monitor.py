"""Real-time monitoring orchestration for FOMC policy statement shifts.

This module coordinates RSS feed monitoring, shift detection, and alert distribution
for Federal Reserve FOMC policy statements.
"""

import logging
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime

from src.monitoring import RSSMonitor
from src.core import ImprovedDetector
from src.distribution import AlertDeduplicator, EmailSender
from src.validation import MarketValidator
from src.config import setup_logging
from src.config.settings import get_settings
from src.exceptions import DataError, DetectionError

logger = logging.getLogger(__name__)


class FOMCMonitor:
    """Orchestrate monitoring, detection, and alert distribution.

    Workflow:
    1. Check RSS feed for new statements
    2. Download new statements
    3. Run shift detection on configured terms
    4. Generate and distribute alerts for detected shifts
    """

    def __init__(self):
        """Initialize FOMC monitor."""
        self.settings = get_settings()
        self.rss_monitor = RSSMonitor()
        self.detector = ImprovedDetector()

        # Phase 4B: Alert distribution components
        self.deduplicator = AlertDeduplicator()
        self.email_sender = EmailSender()

        # Phase 5: Market validation component
        try:
            self.market_validator = MarketValidator()
            market_validation_enabled = self.market_validator.enabled
        except Exception as e:
            logger.warning(f"Market validation initialization failed: {e}")
            logger.warning("Continuing without market validation")
            self.market_validator = None
            market_validation_enabled = False

        # Load configured terms to monitor
        self.monitored_terms = self._load_monitored_terms()

        # Alert output directory
        self.alert_dir = Path(self.settings.get('alerts.output_dir', default='results/alerts'))
        self.alert_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"FOMCMonitor initialized. Monitoring {len(self.monitored_terms)} terms")
        logger.info(f"Email distribution: {'enabled' if self.email_sender.enabled else 'disabled'}")
        logger.info(f"Market validation: {'enabled' if market_validation_enabled else 'disabled'}")

    def _load_monitored_terms(self) -> List[str]:
        """Load list of terms to monitor from config.

        Returns:
            List of term strings to monitor
        """
        keywords = self.settings.get('keywords', default=[])

        # Filter to enabled high/medium priority keywords
        monitored = []
        for kw in keywords:
            if kw.get('enabled', True):
                priority = kw.get('priority', 'medium')
                if priority in ['high', 'medium']:
                    monitored.append(kw['word'])

        if not monitored:
            logger.warning("No monitored terms configured, using default: 'transitory'")
            monitored = ['transitory']

        return monitored

    def _load_all_statements(self) -> tuple[List[str], Dict[str, str]]:
        """Load all policy statements from processed directory.

        Returns:
            Tuple of (dates, texts) where:
                dates: List of statement dates in YYYYMMDD format
                texts: Dict mapping date to statement text
        """
        data_dir = self.rss_monitor.data_dir

        # Get all policy statement files
        all_files = sorted(data_dir.glob('policy_statement_*.txt'))
        statement_files = [f for f in all_files if not f.name.endswith('.html.txt')]

        dates = []
        texts = {}

        for file_path in statement_files:
            # Extract date from filename
            date_str = file_path.stem.replace('policy_statement_', '')

            # Read text content
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            dates.append(date_str)
            texts[date_str] = text

        logger.info(f"Loaded {len(dates)} policy statements from {data_dir}")
        return dates, texts

    def _format_alert_text(self, alert: Dict) -> str:
        """Format alert as human-readable text.

        Args:
            alert: Alert dictionary

        Returns:
            Formatted text string
        """
        text = f"""
{'='*70}
  FEDSPEAK LANGUAGE SHIFT DETECTED
{'='*70}

Term: "{alert['term']}"
Shift Type: {alert['shift_type'].upper()}
Document: policy_statement - {alert['document']['date']}
Confidence: {alert['confidence'].upper()}

Change:
  {alert['change']['change_description']}

Timestamp: {alert['timestamp']}
Alert ID: {alert['alert_id']}

{'='*70}
"""
        return text

    def check_once(self) -> List[Dict]:
        """Check RSS feed once and process any new statements.

        Returns:
            List of alerts generated
        """
        logger.info("=== Starting FOMC Monitor Check ===")

        # Check for new statements
        try:
            new_dates = self.rss_monitor.process_new_statements()

            if not new_dates:
                logger.info("No new statements found")
                return []

            logger.info(f"Downloaded {len(new_dates)} new statements: {new_dates}")

        except DataError as e:
            logger.error(f"Failed to check RSS feed: {e}")
            return []

        # Run detection on all statements (including new ones)
        alerts = []

        try:
            dates, texts = self._load_all_statements()

            for term in self.monitored_terms:
                logger.info(f"Running detection for term: '{term}'")

                try:
                    detections = self.detector.detect_shift(term, dates, texts)

                    # Filter to only detections from new statements
                    new_detections = [d for d in detections if d['date'] in new_dates]

                    if new_detections:
                        logger.info(f"Found {len(new_detections)} shifts for '{term}' in new statements")

                        for detection in new_detections:
                            # Create alert structure
                            alert = {
                                'alert_id': f"ALERT-{detection['date']}-{detection['shift_type']}-{term.replace(' ', '_')}",
                                'timestamp': datetime.now().isoformat(),
                                'shift_type': detection['shift_type'],
                                'term': term,
                                'document': {
                                    'date': detection['date'],
                                    'doc_type': 'policy_statement'
                                },
                                'change': {
                                    'previous_avg': detection['prev_avg'],
                                    'current_count': detection['curr_count'],
                                    'change_description': f"{detection['prev_avg']:.1f} → {detection['curr_count']}"
                                },
                                'confidence': detection['confidence'],
                                'detection_metadata': detection
                            }

                            # Phase 5: Market validation
                            if self.market_validator and self.market_validator.enabled:
                                try:
                                    market_validation = self.market_validator.validate_shift(
                                        date=detection['date'],
                                        term=term,
                                        shift_type=detection['shift_type']
                                    )
                                    tier_num, tier_name = self.market_validator.determine_tier(
                                        detection['confidence'],
                                        market_validation['validated']
                                    )

                                    # Add market validation fields to alert
                                    alert['market_validation'] = market_validation
                                    alert['tier'] = tier_num
                                    alert['tier_name'] = tier_name
                                    alert['confidence_original'] = detection['confidence']
                                    alert['confidence_adjusted'] = tier_name

                                    logger.info(
                                        f"Market validation: {market_validation['validated']} "
                                        f"(score: {market_validation['market_score']:.2f}, tier: {tier_num})"
                                    )
                                except Exception as e:
                                    logger.warning(f"Market validation failed for {alert['alert_id']}: {e}")
                                    # Continue without market validation
                                    alert['market_validation'] = None
                                    alert['tier'] = 2  # Default to Tier 2 (statistical only)
                                    alert['tier_name'] = 'tier_2'
                            else:
                                # Market validation disabled
                                alert['market_validation'] = None
                                alert['tier'] = 2  # Default to Tier 2
                                alert['tier_name'] = 'tier_2'

                            # Check for duplicate
                            if not self.deduplicator.should_distribute(alert):
                                logger.info(f"Skipping duplicate alert: {alert['alert_id']}")
                                continue

                            # Save alert files
                            alert_file = self.alert_dir / f"{alert['alert_id']}.json"
                            alert_file.write_text(json.dumps(alert, indent=2), encoding='utf-8')

                            text_file = self.alert_dir / f"{alert['alert_id']}.txt"
                            text_content = self._format_alert_text(alert)
                            text_file.write_text(text_content, encoding='utf-8')

                            logger.info(f"Saved alert to {alert_file}")

                            # Distribute via email if enabled
                            try:
                                if self.email_sender.send_alert(alert):
                                    logger.info(f"Email sent for alert: {alert['alert_id']}")
                            except Exception as e:
                                logger.error(f"Failed to send email for {alert['alert_id']}: {e}")
                                # Continue - don't let email failure stop processing

                            alerts.append({
                                'term': term,
                                'detection': detection,
                                'alert': alert,
                                'alert_file': str(alert_file)
                            })

                except DetectionError as e:
                    logger.error(f"Detection failed for term '{term}': {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to load statements or run detection: {e}")
            return alerts

        logger.info(f"=== Check Complete: {len(alerts)} alerts generated ===")
        return alerts

    def run_continuous(self, interval_seconds: int = 300):
        """Run monitoring continuously at specified interval.

        Args:
            interval_seconds: Seconds between checks (default: 300 = 5 minutes)
        """
        logger.info(f"Starting continuous monitoring (check every {interval_seconds}s)")
        logger.info(f"Monitoring terms: {', '.join(self.monitored_terms)}")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                try:
                    alerts = self.check_once()

                    if alerts:
                        logger.info(f"Generated {len(alerts)} alerts this cycle")
                        logger.info(f"Alerts distributed: {len([a for a in alerts if 'alert' in a])}")

                except Exception as e:
                    logger.error(f"Error during monitoring cycle: {e}")
                    logger.exception(e)

                # Wait before next check
                logger.info(f"Waiting {interval_seconds} seconds until next check...")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user (Ctrl+C)")
            sys.exit(0)


def main():
    """CLI entry point for monitor."""
    import argparse

    parser = argparse.ArgumentParser(description='FOMC Policy Statement Monitor')
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously (default: check once)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds for continuous mode (default: 300)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level, log_to_console=True, log_to_file=True)

    # Create monitor
    monitor = FOMCMonitor()

    # Run in requested mode
    if args.continuous:
        monitor.run_continuous(interval_seconds=args.interval)
    else:
        alerts = monitor.check_once()
        print(f"\n{'='*70}")
        print(f"  Check Complete: {len(alerts)} alerts generated")
        print(f"{'='*70}\n")

        if alerts:
            print("Alerts:")
            for alert in alerts:
                print(f"  - {alert['term']}: {alert['detection']['shift_type']} on {alert['detection']['date']}")
                print(f"    File: {alert['alert_file']}")

        sys.exit(0)


if __name__ == '__main__':
    main()

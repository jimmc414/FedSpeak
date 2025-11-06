"""
Alert generation module for FedSpeak.
Creates formatted alerts when language shifts detected.

Based on:
- Document 03 Section 6.3 (alert format)
- Architecture Section 3.5 (Alert Generator design)
- Requirements REQ-AG-001 to REQ-AG-008
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from fedspeak.detector import Shift

logger = logging.getLogger(__name__)


class AlertGenerator:
    """
    Generates formatted alerts for detected shifts.

    Includes:
    - Historical context from keyword catalog
    - Evidence (previous occurrences, timeline)
    - Multiple output formats (JSON, text, HTML)
    """

    def __init__(self, config: Dict):
        """
        Initialize alert generator.

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config

        # Build context catalog from keywords
        self.context_catalog = self._build_context_catalog(config['keywords'])

        self.output_dir = Path(config['alerts']['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.viz_dir = Path(config['alerts']['visualization_dir'])
        self.viz_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"AlertGenerator initialized. Output: {self.output_dir}")

    def _build_context_catalog(self, keywords: List[Dict]) -> Dict[str, Dict]:
        """Build context lookup from keywords config."""
        catalog = {}

        for kw in keywords:
            catalog[kw['word']] = {
                'type': kw.get('type', 'unknown'),
                'context': kw.get('context', ''),
                'shift_id': kw.get('shift_id', ''),
                'significance': kw.get('significance', ''),
                'priority': kw.get('priority', 'medium')
            }

        return catalog

    def generate_alert(self,
                      shift: Shift,
                      time_series: pd.DataFrame) -> Dict:
        """
        Generate alert from shift detection.

        Args:
            shift: Detected Shift object
            time_series: Full time-series for evidence gathering

        Returns:
            Alert dictionary
        """
        logger.info(f"Generating alert for {shift.shift_type}: '{shift.word}'")

        # Get context from catalog
        context = self.context_catalog.get(shift.word, {})

        # Gather evidence
        evidence = self._gather_evidence(shift, time_series)

        # Generate visualization
        viz_path = self._create_timeline_visualization(shift, time_series)

        # Build alert structure
        alert = {
            'alert_id': f"ALERT-{shift.date.strftime('%Y%m%d')}-{shift.shift_type}-{shift.word.replace(' ', '_')}",
            'timestamp': datetime.now().isoformat(),
            'shift_type': shift.shift_type,
            'word': shift.word,
            'document': {
                'doc_id': shift.doc_id,
                'doc_type': shift.doc_type,
                'date': shift.date.strftime('%Y-%m-%d')
            },
            'change': {
                'previous_count': shift.previous_count,
                'current_count': shift.current_count,
                'change_description': f"{shift.previous_count:.1f} → {shift.current_count}"
            },
            'context': {
                'category': context.get('context', 'unknown'),
                'shift_id': context.get('shift_id', ''),
                'significance': context.get('significance', ''),
                'priority': context.get('priority', 'medium')
            },
            'evidence': evidence,
            'confidence': shift.confidence,
            'visualization': str(viz_path) if viz_path else None
        }

        # Add synonym details if available
        if shift.synonym_details:
            alert['synonym_details'] = shift.synonym_details
            # Add synonym breakdown to change section
            alert['change']['synonym_breakdown'] = shift.synonym_details.get('synonym_counts', {})

        return alert

    def _gather_evidence(self, shift: Shift, time_series: pd.DataFrame) -> Dict:
        """
        Gather evidence for shift.

        For emergence: Show first occurrences
        For removal: Show previous occurrences and sustained absence
        """
        # Filter to this word
        word_data = time_series[time_series['word'] == shift.word].copy()
        word_data = word_data.sort_values('date')

        evidence = {}

        if shift.shift_type == 'emergence':
            # Show that word was absent before
            prior_docs = word_data[word_data['date'] < shift.date]
            evidence['prior_occurrences'] = len(prior_docs[prior_docs['count'] > 0])
            evidence['first_occurrence'] = True

        elif shift.shift_type == 'removal':
            # Show previous occurrences
            prior_docs = word_data[word_data['date'] < shift.date]
            prev_occurrences = prior_docs[prior_docs['count'] > 0]

            evidence['previous_occurrences'] = [
                {
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'count': int(row['count']),
                    'doc_id': str(row['doc_id'])
                }
                for _, row in prev_occurrences.tail(5).iterrows()
            ]

            # Check sustained absence
            future_docs = word_data[word_data['date'] > shift.date].head(3)
            evidence['sustained_absence'] = bool(all(future_docs['count'] == 0))
            evidence['next_3_docs_count'] = int(future_docs['count'].sum())

        return evidence

    def _create_timeline_visualization(self,
                                      shift: Shift,
                                      time_series: pd.DataFrame) -> Optional[Path]:
        """
        Create timeline chart showing word frequency over time.

        Args:
            shift: Shift to visualize
            time_series: Full time-series data

        Returns:
            Path to saved PNG file
        """
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 6))

            # Check if we have synonym data to visualize
            if shift.synonym_details and 'primary_word' in time_series.columns:
                # Filter to primary word (all synonyms + group)
                primary_word = shift.synonym_details['primary_word']
                word_data = time_series[time_series['primary_word'] == primary_word].copy()

                if len(word_data) == 0:
                    return None

                # Plot individual synonyms (dotted lines)
                individual_synonyms = word_data[word_data['is_group'] == False]
                for synonym in shift.synonym_details.get('synonym_counts', {}).keys():
                    syn_data = individual_synonyms[individual_synonyms['word'] == synonym].sort_values('date')
                    if len(syn_data) > 0:
                        ax.plot(syn_data['date'], syn_data['count'],
                               linestyle=':', linewidth=1.5, marker='.',
                               markersize=5, alpha=0.7, label=f"'{synonym}'")

                # Plot group total (bold line)
                group_data = word_data[word_data['is_group'] == True].sort_values('date')
                if len(group_data) > 0:
                    ax.plot(group_data['date'], group_data['count'],
                           linewidth=3, marker='o', markersize=8,
                           color='#2E86AB', label=f"'{primary_word}' GROUP TOTAL")

            else:
                # Standard visualization (no synonyms)
                word_data = time_series[time_series['word'] == shift.word].copy()
                word_data = word_data.sort_values('date')

                if len(word_data) == 0:
                    return None

                ax.plot(word_data['date'], word_data['count'],
                       marker='o', linewidth=2, markersize=8,
                       label=f"'{shift.word}' count")

            # Mark shift date
            ax.axvline(shift.date, color='red', linestyle='--',
                      linewidth=2, label=f'{shift.shift_type.capitalize()} detected')

            # Formatting
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Count per Document', fontsize=12)
            title_word = shift.synonym_details['primary_word'] if shift.synonym_details else shift.word
            ax.set_title(f"FedSpeak: '{title_word}' Frequency Timeline\n"
                        f"{shift.shift_type.capitalize()} on {shift.date.date()}",
                        fontsize=14, fontweight='bold')

            ax.legend(fontsize=9, loc='best')
            ax.grid(True, alpha=0.3)

            # Format x-axis dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.xticks(rotation=45)

            plt.tight_layout()

            # Save figure
            filename = f"{shift.word.replace(' ', '_')}_timeline.png"
            filepath = self.viz_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"Saved visualization: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to create visualization: {e}")
            return None

    def format_alert_text(self, alert: Dict) -> str:
        """
        Format alert as human-readable text.

        Args:
            alert: Alert dictionary

        Returns:
            Formatted text string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("  FEDSPEAK LANGUAGE SHIFT DETECTED")
        lines.append("=" * 70)
        lines.append("")

        # Header
        word_display = f"\"{alert['word']}\""
        if 'synonym_details' in alert:
            word_display += " (synonym group)"
        lines.append(f"Word: {word_display}")
        lines.append(f"Shift Type: {alert['shift_type'].upper()}")
        lines.append(f"Document: {alert['document']['doc_type']} - {alert['document']['date']}")
        lines.append(f"Confidence: {alert['confidence'].upper()}")
        lines.append("")

        # Change
        lines.append("Change:")
        lines.append(f"  {alert['change']['change_description']}")

        # Synonym breakdown if available
        if 'synonym_breakdown' in alert['change'] and alert['change']['synonym_breakdown']:
            lines.append("")
            lines.append("  Synonym Usage:")
            for syn_word, syn_count in alert['change']['synonym_breakdown'].items():
                lines.append(f"    - {syn_word}: {syn_count} occurrence{'s' if syn_count != 1 else ''}")

        lines.append("")

        # Context
        if alert['context']['significance']:
            lines.append("Historical Significance:")
            for line in alert['context']['significance'].split('\n'):
                lines.append(f"  {line}")
            lines.append("")

        # Evidence
        lines.append("Evidence:")
        if 'previous_occurrences' in alert['evidence']:
            lines.append(f"  Previous occurrences: {len(alert['evidence']['previous_occurrences'])}")
            for occ in alert['evidence']['previous_occurrences'][-3:]:
                lines.append(f"    - {occ['date']}: count={occ['count']}")

        if 'sustained_absence' in alert['evidence']:
            sustained = "Yes" if alert['evidence']['sustained_absence'] else "No"
            lines.append(f"  Sustained absence: {sustained}")

        lines.append("")

        # Visualization
        if alert['visualization']:
            lines.append(f"Timeline: {alert['visualization']}")

        lines.append("")
        lines.append("=" * 70)

        return '\n'.join(lines)

    def save_alert(self, alert: Dict):
        """
        Save alert to disk in configured formats.

        Args:
            alert: Alert dictionary
        """
        # JSON format
        json_path = self.output_dir / f"{alert['alert_id']}.json"
        with open(json_path, 'w') as f:
            json.dump(alert, f, indent=2)
        logger.info(f"Saved alert (JSON): {json_path}")

        # Text format
        if 'text' in self.config['alerts']['output_formats']:
            text_path = self.output_dir / f"{alert['alert_id']}.txt"
            text_content = self.format_alert_text(alert)
            text_path.write_text(text_content)
            logger.info(f"Saved alert (text): {text_path}")


# Example usage
if __name__ == '__main__':
    import yaml
    from fedspeak.detector import Shift

    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    alerter = AlertGenerator(config)

    # Create sample shift
    shift = Shift(
        shift_type='removal',
        word='transitory',
        date=pd.Timestamp('2021-12-15'),
        doc_id='policy_statement_20211215',
        doc_type='policy_statement',
        previous_count=1.0,
        current_count=0,
        confidence='high'
    )

    # Load time-series
    ts = pd.read_csv('data/metadata/keyword_metrics.csv')
    ts['date'] = pd.to_datetime(ts['date'])

    # Generate alert
    alert = alerter.generate_alert(shift, ts)

    # Save alert
    alerter.save_alert(alert)

    print("\nAlert generated:")
    print(alerter.format_alert_text(alert))

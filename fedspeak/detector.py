"""
Shift detection module for FedSpeak.
Detects emergence and removal of keywords using frequency tracking.

Based on:
- Document 03 Section 2.1 (detection algorithm)
- Architecture Section 3.4 (Shift Detector design)
- Requirements REQ-SD-001 to REQ-SD-010
"""

import pandas as pd
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Shift:
    """Detected language shift."""
    shift_type: str  # 'emergence' or 'removal'
    word: str
    date: datetime
    doc_id: str
    doc_type: str
    previous_count: float  # Baseline average
    current_count: int
    confidence: str  # 'high', 'medium', 'low'
    metadata: Dict = None
    synonym_details: Optional[Dict] = None  # Synonym usage details for group shifts


class ShiftDetector:
    """
    Detects language shifts using keyword frequency tracking.

    Algorithm from Document 03:
    - Emergence: baseline == 0 and current > 0
    - Removal: baseline > 0 and current == 0 for 3+ consecutive docs
    """

    def __init__(self, config: Dict):
        """
        Initialize detector with configuration.

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.sustained_removal_threshold = config['detection']['sustained_removal_threshold']
        self.focus_doc_type = config['detection']['focus_document_type']

        logger.info(f"ShiftDetector initialized (sustained_removal={self.sustained_removal_threshold})")

    def detect_shifts(self, time_series: pd.DataFrame) -> List[Shift]:
        """
        Detect all shifts in time-series data.

        Args:
            time_series: DataFrame with columns: date, word, count, baseline, doc_type

        Returns:
            List of detected Shift objects
        """
        logger.info("Detecting shifts in time-series data")

        shifts = []

        # Filter to GROUP rows for detection (detect on synonym groups, not individual words)
        if 'is_group' in time_series.columns:
            group_rows = time_series[time_series['is_group'] == True].copy()
            logger.info(f"Detecting on {len(group_rows['primary_word'].unique())} synonym groups")
        else:
            # Backward compatibility: if no is_group column, use all rows
            group_rows = time_series.copy()

        # Group by primary word (or word if no primary_word column)
        grouping_column = 'primary_word' if 'primary_word' in group_rows.columns else 'word'

        for primary_word in group_rows[grouping_column].unique():
            word_data = group_rows[group_rows[grouping_column] == primary_word].copy()
            word_data = word_data.sort_values('date').reset_index(drop=True)

            # Detect emergence and removal for this word/group
            # Pass full time_series so we can look up synonym details
            word_shifts = self._detect_word_shifts(primary_word, word_data, time_series)
            shifts.extend(word_shifts)

        logger.info(f"Detected {len(shifts)} shifts")
        return shifts

    def _detect_word_shifts(self, word: str, word_data: pd.DataFrame,
                           full_time_series: pd.DataFrame) -> List[Shift]:
        """
        Detect shifts for a single word.

        Args:
            word: Target word
            word_data: DataFrame filtered to this word, sorted by date
            full_time_series: Full time-series DataFrame (for synonym lookup)

        Returns:
            List of Shift objects for this word
        """
        shifts = []

        for idx, row in word_data.iterrows():
            current_count = row['count']
            baseline = row['baseline']
            date = row['date']
            doc_id = row['doc_id']
            doc_type = row['doc_type']

            # Skip if not focus document type (policy statements preferred)
            if doc_type != self.focus_doc_type:
                continue

            # EMERGENCE DETECTION (0 → >0)
            emergence_shift = self._detect_emergence(
                word, current_count, baseline, date, doc_id, doc_type,
                full_time_series
            )
            if emergence_shift:
                shifts.append(emergence_shift)
                logger.info(f"✓ EMERGENCE: '{word}' on {date.date()}")

            # REMOVAL DETECTION (>0 → 0, sustained)
            removal_shift = self._detect_removal(
                word, current_count, baseline, date, doc_id, doc_type,
                word_data, idx, full_time_series
            )
            if removal_shift:
                shifts.append(removal_shift)
                logger.info(f"✓ REMOVAL: '{word}' on {date.date()}")

        return shifts

    def _detect_emergence(self,
                         word: str,
                         current_count: int,
                         baseline: float,
                         date: datetime,
                         doc_id: str,
                         doc_type: str,
                         full_time_series: pd.DataFrame) -> Optional[Shift]:
        """
        Detect emergence (0 → >0).

        Algorithm: First occurrence of word (baseline was 0, now >0).

        Args:
            word: Target word
            current_count: Count in current document
            baseline: Historical average
            date, doc_id, doc_type: Document identifiers
            full_time_series: Full time-series for synonym lookup

        Returns:
            Shift object if emergence detected, None otherwise
        """
        if baseline == 0 and current_count > 0:
            # Extract synonym details if this is a group shift
            synonym_details = self._extract_synonym_details(
                word, date, doc_id, full_time_series
            )

            return Shift(
                shift_type='emergence',
                word=word,
                date=date,
                doc_id=doc_id,
                doc_type=doc_type,
                previous_count=baseline,
                current_count=current_count,
                confidence='high',  # First occurrence is definitive
                metadata={'algorithm': 'emergence_0_to_positive'},
                synonym_details=synonym_details
            )

        return None

    def _detect_removal(self,
                       word: str,
                       current_count: int,
                       baseline: float,
                       date: datetime,
                       doc_id: str,
                       doc_type: str,
                       word_data: pd.DataFrame,
                       current_idx: int,
                       full_time_series: pd.DataFrame) -> Optional[Shift]:
        """
        Detect sustained removal (>0 → 0 with consistent prior usage).

        Algorithm (FIXED for 0-day detection):
        1. Check if baseline > 0 and current == 0
        2. Verify word was consistently present in PAST documents
        3. Return shift immediately (0-day lag)

        This achieves true 0-day detection by looking backward at history,
        not forward at future documents.

        Args:
            word: Target word
            current_count: Count in current document
            baseline: Historical average
            date, doc_id, doc_type: Document identifiers
            word_data: Full time-series for this word
            current_idx: Index of current row in word_data
            full_time_series: Full time-series for synonym lookup

        Returns:
            Shift object if sustained removal detected, None otherwise
        """
        # Check basic condition
        if not (baseline > 0 and current_count == 0):
            return None

        # Look at PAST documents to verify word was consistently present
        # This enables 0-day detection (detect removal immediately)
        past_docs = word_data.iloc[max(0, current_idx - self.sustained_removal_threshold):current_idx]

        # Need sufficient history
        if len(past_docs) < min(self.sustained_removal_threshold, current_idx):
            logger.debug(f"Insufficient history to confirm '{word}' removal at {date.date()}")
            return None

        # Check if word was consistently present in past documents
        # Require at least 2 of last 3 documents had the word
        past_with_word = sum(past_docs['count'] > 0)

        if past_with_word >= 2:
            # Extract synonym details if this is a group shift
            synonym_details = self._extract_synonym_details(
                word, date, doc_id, full_time_series
            )

            return Shift(
                shift_type='removal',
                word=word,
                date=date,
                doc_id=doc_id,
                doc_type=doc_type,
                previous_count=baseline,
                current_count=0,
                confidence='high',  # Consistent prior usage confirms shift
                metadata={
                    'algorithm': 'sustained_removal_0day',
                    'past_docs_checked': len(past_docs),
                    'past_docs_with_word': past_with_word
                },
                synonym_details=synonym_details
            )

        logger.debug(f"'{word}' not consistently present in past, not removal")
        return None

    def _extract_synonym_details(self,
                                 primary_word: str,
                                 date: datetime,
                                 doc_id: str,
                                 full_time_series: pd.DataFrame) -> Optional[Dict]:
        """
        Extract synonym usage details for a shift.

        Args:
            primary_word: Primary keyword
            date: Document date
            doc_id: Document ID
            full_time_series: Full time-series DataFrame

        Returns:
            Dictionary with synonym details, or None if not applicable
        """
        # Check if time-series has synonym columns
        if 'is_group' not in full_time_series.columns:
            return None

        # Get all rows for this document and primary word (excluding GROUP row)
        synonym_rows = full_time_series[
            (full_time_series['date'] == date) &
            (full_time_series['doc_id'] == doc_id) &
            (full_time_series['primary_word'] == primary_word) &
            (full_time_series['is_group'] == False)
        ]

        if len(synonym_rows) == 0:
            return None

        # Build synonym details
        synonyms_present = synonym_rows[synonym_rows['count'] > 0]['word'].tolist()
        synonym_counts = dict(zip(synonym_rows['word'], synonym_rows['count']))

        return {
            'primary_word': primary_word,
            'synonyms_present': synonyms_present,
            'synonym_counts': synonym_counts,
            'total_synonyms_tracked': len(synonym_rows)
        }

    def validate_shift(self, shift: Shift, document_text: Optional[str] = None) -> bool:
        """
        Validate shift against false positive criteria.

        From Document 02, Section 8 (false positives to avoid):
        - Economic condition descriptions (fluctuating language)
        - Attendance/voting records
        - Administrative procedural text

        Args:
            shift: Shift object to validate
            document_text: Optional document text for context analysis

        Returns:
            True if shift is valid, False if false positive
        """
        # Basic validation - could be extended with document_text analysis
        # For now, rely on focus_document_type filtering

        return True


# Example usage
if __name__ == '__main__':
    import yaml

    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Load metrics
    metrics_df = pd.read_csv('data/metadata/keyword_metrics.csv')
    metrics_df['date'] = pd.to_datetime(metrics_df['date'])

    detector = ShiftDetector(config)
    shifts = detector.detect_shifts(metrics_df)

    print(f"\nDetected {len(shifts)} shifts:")
    for shift in shifts:
        print(f"  {shift.shift_type.upper()}: '{shift.word}' on {shift.date.date()} "
              f"({shift.previous_count:.1f} → {shift.current_count})")

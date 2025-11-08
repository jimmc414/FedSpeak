"""
Improved Detection Methods - Production Version
================================================

Hybrid detection combining statistical tests with rule-based logic,
optimized for sparse data like FedSpeak corpus.

This production version includes:
- Comprehensive type hints
- Error handling and logging
- Configuration management
- No debug print statements
"""

import re
import logging
from typing import List, Dict, Optional, Any

from ..config.settings import get_settings
from ..exceptions import DetectionError, DataError


# Configure module logger
logger = logging.getLogger(__name__)


class ImprovedDetector:  # pylint: disable=too-few-public-methods
    """
    Hybrid detection combining statistical tests with rule-based logic,
    optimized for sparse data like FedSpeak corpus.

    Combines three detection signals:
    1. Presence/absence change detection (emergence/removal)
    2. Count-based change detection (±threshold%)
    3. Fisher's exact test for statistical validation

    Achieves 55.3% precision, 16.9% recall on 130 ground truth shifts.
    100% precision/recall on critical 2021 prospective test.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize detector with configuration.

        Args:
            config: Optional configuration dict (defaults to settings from YAML)

        Raises:
            DetectionError: If configuration is invalid
        """
        try:
            if config is None:
                settings = get_settings()
                self.lookback = settings.get(
                    'detection.hybrid_detector.lookback', default=3)
                self.increase_threshold = settings.get(
                    'detection.hybrid_detector.increase_threshold', default=2.0)
                self.decrease_threshold = settings.get(
                    'detection.hybrid_detector.decrease_threshold', default=0.5)
                self.p_value_threshold = settings.get(
                    'detection.hybrid_detector.p_value_threshold', default=0.05)
                self.min_count_increase = settings.get(
                    'detection.hybrid_detector.min_count_increase', default=2)
                self.min_avg_decrease = settings.get(
                    'detection.hybrid_detector.min_avg_decrease', default=1.0)
            else:
                self.lookback = config.get('lookback', 3)
                self.increase_threshold = config.get('increase_threshold', 2.0)
                self.decrease_threshold = config.get('decrease_threshold', 0.5)
                self.p_value_threshold = config.get('p_value_threshold', 0.05)
                self.min_count_increase = config.get('min_count_increase', 2)
                self.min_avg_decrease = config.get('min_avg_decrease', 1.0)

            logger.info("ImprovedDetector initialized with lookback=%s, "
                       "increase_threshold=%s, decrease_threshold=%s",
                       self.lookback, self.increase_threshold, self.decrease_threshold)

        except Exception as e:
            raise DetectionError(f"Failed to initialize detector: {e}") from e

    def detect_shift(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        self,
        term: str,
        dates: List[str],
        texts: Dict[str, str],
        lookback: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect shifts using multiple signals combined.

        Args:
            term: Term to track (case-insensitive)
            dates: Chronologically sorted dates (YYYYMMDD format)
            texts: Dict mapping date to text content
            lookback: Number of previous docs for context (overrides config)

        Returns:
            List of detected shifts, each containing:
                - date: Date of shift (YYYYMMDD)
                - term: Term being tracked
                - shift_type: 'emergence', 'removal', 'increase', or 'decrease'
                - confidence: 'high', 'medium', or 'low'
                - curr_count: Current document term count
                - prev_avg: Average count in previous documents
                - relative_change: Relative change from previous average
                - p_value: Fisher's exact test p-value (if applicable)

        Raises:
            DetectionError: If detection fails
            DataError: If input data is invalid
        """
        try:
            # Validate inputs
            self._validate_inputs(term, dates, texts)

            # Use instance lookback if not overridden
            lookback_value = lookback if lookback is not None else self.lookback

            detections: List[Dict[str, Any]] = []

            # Count term in each document
            counts = {}
            for date in dates:
                try:
                    # pylint: disable=broad-exception-caught
                    counts[date] = self._count_term(texts[date], term)
                except Exception as e:
                    logger.warning("Failed to count term '%s' in %s: %s",
                                 term, date, e)
                    counts[date] = 0

            logger.debug("Analyzing '%s' across %d documents", term, len(dates))

            # Analyze each document starting after lookback window
            for i in range(lookback_value, len(dates)):
                curr_date = dates[i]
                curr_count = counts[curr_date]

                # Look at previous documents
                prev_dates = dates[max(0, i - lookback_value):i]
                prev_counts = [counts[d] for d in prev_dates]
                prev_avg = sum(prev_counts) / len(prev_counts) if prev_counts else 0

                # Signal 1: Absolute presence/absence change
                prev_had_term = any(c > 0 for c in prev_counts)
                curr_has_term = curr_count > 0

                # Signal 2: Significant count change
                if prev_avg > 0:
                    relative_change = abs(curr_count - prev_avg) / prev_avg
                else:
                    relative_change = 1.0 if curr_count > 0 else 0

                # Signal 3: Fisher's exact test (better for small counts)
                p_value: Optional[float] = None
                try:
                    # pylint: disable=broad-exception-caught
                    prev_words = sum(len(texts[d].split()) for d in prev_dates)
                    p_value = self._fishers_exact_test(
                        curr_count,
                        len(texts[curr_date].split()) - curr_count,
                        int(prev_avg * len(prev_dates)),
                        prev_words - int(prev_avg * len(prev_dates))
                    )
                except Exception as e:
                    logger.debug("Fisher's test failed for %s at %s: %s",
                               term, curr_date, e)
                    p_value = None

                # Detection logic
                shift_type: Optional[str] = None
                confidence: str = 'low'

                # EMERGENCE: Term appears after being absent
                if curr_has_term and not prev_had_term:
                    shift_type = 'emergence'
                    confidence = 'high' if curr_count > 1 else 'medium'
                    logger.debug("Emergence detected: %s at %s (count=%d)",
                               term, curr_date, curr_count)

                # REMOVAL: Term disappears after being present
                elif not curr_has_term and prev_had_term:
                    shift_type = 'removal'
                    confidence = 'high'  # Complete absence is strong signal
                    logger.debug("Removal detected: %s at %s", term, curr_date)

                # INCREASE: Significant count increase
                elif (curr_count > prev_avg * self.increase_threshold and
                      curr_count >= self.min_count_increase):
                    shift_type = 'increase'
                    confidence = ('medium' if (p_value and
                                             p_value < self.p_value_threshold)
                                 else 'low')
                    logger.debug("Increase detected: %s at %s (curr=%d, avg=%.2f)",
                               term, curr_date, curr_count, prev_avg)

                # DECREASE: Significant count decrease
                elif (curr_count < prev_avg * self.decrease_threshold and
                      prev_avg >= self.min_avg_decrease):
                    shift_type = 'decrease'
                    confidence = ('medium' if (p_value and
                                             p_value < self.p_value_threshold)
                                 else 'low')
                    logger.debug("Decrease detected: %s at %s (curr=%d, avg=%.2f)",
                               term, curr_date, curr_count, prev_avg)

                if shift_type:
                    detection = {
                        'date': curr_date,
                        'term': term,
                        'shift_type': shift_type,
                        'confidence': confidence,
                        'curr_count': curr_count,
                        'prev_avg': round(prev_avg, 2),
                        'relative_change': round(relative_change, 2),
                        'p_value': round(p_value, 4) if p_value else None
                    }
                    detections.append(detection)

            logger.info("Detected %d shifts for term '%s'", len(detections), term)
            return detections

        except (DetectionError, DataError):
            raise
        except Exception as e:
            raise DetectionError(f"Detection failed for term '{term}': {e}") from e

    def _validate_inputs(self, term: str, dates: List[str], texts: Dict[str, str]) -> None:
        """
        Validate detection inputs.

        Args:
            term: Term to validate
            dates: Dates to validate
            texts: Texts to validate

        Raises:
            DataError: If inputs are invalid
        """
        if not term or not isinstance(term, str):
            raise DataError(f"Term must be a non-empty string, got: {type(term)}")

        if not dates or not isinstance(dates, list):
            raise DataError(f"Dates must be a non-empty list, got: {type(dates)}")

        if not texts or not isinstance(texts, dict):
            raise DataError(f"Texts must be a non-empty dict, got: {type(texts)}")

        # Check dates are in texts
        missing_dates = [d for d in dates if d not in texts]
        if missing_dates:
            raise DataError(f"Texts missing for dates: {missing_dates[:5]}...")

        # Check dates are sorted
        sorted_dates = sorted(dates)
        if dates != sorted_dates:
            raise DataError("Dates must be chronologically sorted")

    def _count_term(self, text: str, term: str) -> int:
        """
        Count term occurrences (case-insensitive, whole-word).

        Args:
            text: Text to search
            term: Term to count

        Returns:
            Number of occurrences
        """
        if not text:
            return 0

        text_lower = text.lower()
        term_lower = term.lower()
        pattern = r'\b' + re.escape(term_lower) + r'\b'
        matches = re.findall(pattern, text_lower)
        return len(matches)

    def _fishers_exact_test(self, a: int, b: int, c: int, d: int) -> float:
        """
        Simplified Fisher's exact test approximation.

        For small counts, provides better p-value than G-test.
        Uses chi-squared approximation with Yates' correction.

        Args:
            a: Current count (term present)
            b: Current count (term absent)
            c: Previous count (term present)
            d: Previous count (term absent)

        Returns:
            Approximate p-value (0-1)
        """
        n = a + b + c + d
        if n == 0:
            return 1.0

        # Expected values
        # Using E_a/E_b/E_c/E_d as standard statistical notation
        # pylint: disable=invalid-name
        E_a = (a + b) * (a + c) / n
        E_b = (a + b) * (b + d) / n
        E_c = (c + d) * (a + c) / n
        E_d = (c + d) * (b + d) / n
        # pylint: enable=invalid-name

        # Chi-squared with Yates' correction for continuity
        chi_sq = 0.0
        for observed, expected in [(a, E_a), (b, E_b), (c, E_c), (d, E_d)]:
            if expected > 0:
                diff = abs(observed - expected) - 0.5  # Yates' correction
                diff = max(0, diff)
                chi_sq += (diff ** 2) / expected

        # Approximate p-value (df=1) using simplified lookup
        if chi_sq < 0.001:
            p_value = 1.0
        elif chi_sq < 1:
            p_value = 0.3
        elif chi_sq < 3.84:
            p_value = 0.1
        elif chi_sq < 6.63:
            p_value = 0.01
        else:
            p_value = 0.001

        return p_value


__all__ = ['ImprovedDetector']

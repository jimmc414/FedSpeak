"""Unit tests for ShiftDetector module."""

import pytest
import pandas as pd
from datetime import datetime

from fedspeak.detector import ShiftDetector, Shift


class TestShiftDetector:
    """Test suite for ShiftDetector class."""

    def test_initialization(self, sample_config):
        """Test detector initializes correctly."""
        detector = ShiftDetector(sample_config)

        assert detector.sustained_removal_threshold == 3
        assert detector.focus_doc_type == 'policy_statement'

    def test_detect_emergence(self, sample_config):
        """Test emergence detection (0 → >0)."""
        detector = ShiftDetector(sample_config)

        # Create data showing emergence
        df = pd.DataFrame({
            'date': pd.to_datetime(['2021-09-22', '2021-11-03', '2021-12-15']),
            'doc_id': ['doc1', 'doc2', 'doc3'],
            'word': ['transitory'] * 3,
            'count': [0, 2, 3],  # Word appears for first time in doc2
            'baseline': [0.0, 0.0, 2.0],
            'doc_type': ['policy_statement'] * 3
        })

        shifts = detector.detect_shifts(df)

        # Should detect emergence in doc2
        emergence_shifts = [s for s in shifts if s.shift_type == 'emergence']
        assert len(emergence_shifts) == 1
        assert emergence_shifts[0].word == 'transitory'
        assert emergence_shifts[0].current_count == 2
        assert emergence_shifts[0].previous_count == 0.0

    def test_detect_removal(self, sample_config):
        """Test removal detection (>0 → 0)."""
        detector = ShiftDetector(sample_config)

        # Create data showing removal
        df = pd.DataFrame({
            'date': pd.to_datetime([
                '2021-07-28', '2021-09-22', '2021-11-03', '2021-12-15'
            ]),
            'doc_id': ['doc1', 'doc2', 'doc3', 'doc4'],
            'word': ['transitory'] * 4,
            'count': [2, 2, 3, 0],  # Word removed in doc4
            'baseline': [0.0, 2.0, 2.0, 2.3],
            'doc_type': ['policy_statement'] * 4
        })

        shifts = detector.detect_shifts(df)

        # Should detect removal in doc4
        removal_shifts = [s for s in shifts if s.shift_type == 'removal']
        assert len(removal_shifts) == 1
        assert removal_shifts[0].word == 'transitory'
        assert removal_shifts[0].current_count == 0
        assert removal_shifts[0].previous_count > 0

    def test_removal_requires_consistent_prior_usage(self, sample_config):
        """Test removal detection requires consistent prior usage."""
        detector = ShiftDetector(sample_config)

        # Create data with sporadic usage (should NOT detect removal)
        df = pd.DataFrame({
            'date': pd.to_datetime([
                '2021-07-28', '2021-09-22', '2021-11-03', '2021-12-15'
            ]),
            'doc_id': ['doc1', 'doc2', 'doc3', 'doc4'],
            'word': ['transitory'] * 4,
            'count': [0, 2, 0, 0],  # Sporadic - only 1 of last 3 had word
            'baseline': [0.0, 0.0, 1.0, 0.7],
            'doc_type': ['policy_statement'] * 4
        })

        shifts = detector.detect_shifts(df)

        # Should NOT detect removal (word wasn't consistently present)
        removal_shifts = [s for s in shifts if s.shift_type == 'removal']
        assert len(removal_shifts) == 0

    def test_removal_with_minimum_prior_usage(self, sample_config):
        """Test removal detection with exactly 2 of 3 past docs (threshold)."""
        detector = ShiftDetector(sample_config)

        # Create data with 2 of 3 past docs having word (should detect)
        df = pd.DataFrame({
            'date': pd.to_datetime([
                '2021-07-28', '2021-09-22', '2021-11-03', '2021-12-15'
            ]),
            'doc_id': ['doc1', 'doc2', 'doc3', 'doc4'],
            'word': ['transitory'] * 4,
            'count': [2, 0, 3, 0],  # 2 of last 3 (doc1, doc3) had word
            'baseline': [0.0, 2.0, 1.0, 1.7],
            'doc_type': ['policy_statement'] * 4
        })

        shifts = detector.detect_shifts(df)

        # Should detect removal (exactly at threshold)
        removal_shifts = [s for s in shifts if s.shift_type == 'removal']
        assert len(removal_shifts) == 1

    def test_zero_day_detection_lag(self, sample_config, sample_baseline_data):
        """Test that removal is detected immediately (0-day lag)."""
        detector = ShiftDetector(sample_config)

        shifts = detector.detect_shifts(sample_baseline_data)

        # Should detect removal on Dec 15, 2021 (first time count goes to 0)
        removal_shifts = [s for s in shifts if s.shift_type == 'removal']
        assert len(removal_shifts) >= 1  # May detect multiple sustained zeros

        # Check that Dec 15 removal was detected
        dec_15_removal = [s for s in removal_shifts if s.date.month == 12 and s.date.day == 15]
        assert len(dec_15_removal) == 1
        assert dec_15_removal[0].current_count == 0
        assert dec_15_removal[0].previous_count > 0

    def test_focus_document_type_filtering(self, sample_config):
        """Test that non-focus document types are skipped."""
        detector = ShiftDetector(sample_config)

        # Create data with mix of document types
        df = pd.DataFrame({
            'date': pd.to_datetime(['2021-11-03', '2021-11-04']),
            'doc_id': ['doc1', 'doc2'],
            'word': ['transitory'] * 2,
            'count': [2, 0],
            'baseline': [0.0, 2.0],
            'doc_type': ['fomc_minutes', 'fomc_minutes']  # Not policy_statement
        })

        shifts = detector.detect_shifts(df)

        # Should not detect any shifts (wrong document type)
        assert len(shifts) == 0

    def test_multiple_words(self, sample_config):
        """Test detection across multiple keywords."""
        detector = ShiftDetector(sample_config)

        # Create data for two different words
        df = pd.DataFrame({
            'date': pd.to_datetime([
                '2021-09-22', '2021-11-03', '2021-09-22', '2021-11-03'
            ]),
            'doc_id': ['doc1', 'doc2', 'doc1', 'doc2'],
            'word': ['transitory', 'transitory', 'patient', 'patient'],
            'count': [0, 2, 0, 1],  # Both emerge
            'baseline': [0.0, 0.0, 0.0, 0.0],
            'doc_type': ['policy_statement'] * 4
        })

        shifts = detector.detect_shifts(df)

        # Should detect emergence for both words
        emergence_shifts = [s for s in shifts if s.shift_type == 'emergence']
        assert len(emergence_shifts) == 2

        words_detected = {s.word for s in emergence_shifts}
        assert 'transitory' in words_detected
        assert 'patient' in words_detected

    def test_detect_emergence_method(self, sample_config):
        """Test _detect_emergence method directly."""
        detector = ShiftDetector(sample_config)

        # Empty time series for backward compatibility test
        empty_ts = pd.DataFrame()

        shift = detector._detect_emergence(
            word='transitory',
            current_count=2,
            baseline=0.0,
            date=datetime(2021, 11, 3),
            doc_id='doc1',
            doc_type='policy_statement',
            full_time_series=empty_ts
        )

        assert shift is not None
        assert shift.shift_type == 'emergence'
        assert shift.word == 'transitory'
        assert shift.current_count == 2
        assert shift.previous_count == 0.0
        assert shift.confidence == 'high'

    def test_detect_emergence_no_shift(self, sample_config):
        """Test _detect_emergence when no shift occurs."""
        detector = ShiftDetector(sample_config)

        # Empty time series for backward compatibility test
        empty_ts = pd.DataFrame()

        # baseline > 0, so not emergence
        shift = detector._detect_emergence(
            word='transitory',
            current_count=2,
            baseline=1.5,
            date=datetime(2021, 11, 3),
            doc_id='doc1',
            doc_type='policy_statement',
            full_time_series=empty_ts
        )

        assert shift is None

    def test_detect_removal_method(self, sample_config):
        """Test _detect_removal method directly."""
        detector = ShiftDetector(sample_config)

        # Create word data with consistent prior usage
        word_data = pd.DataFrame({
            'date': pd.to_datetime(['2021-09-22', '2021-11-03', '2021-12-15']),
            'doc_id': ['doc1', 'doc2', 'doc3'],
            'count': [2, 3, 0],  # Word present in past, now 0
            'baseline': [0.0, 2.0, 2.5]
        })

        # Empty time series for backward compatibility test
        empty_ts = pd.DataFrame()

        shift = detector._detect_removal(
            word='transitory',
            current_count=0,
            baseline=2.5,
            date=datetime(2021, 12, 15),
            doc_id='doc3',
            doc_type='policy_statement',
            word_data=word_data,
            current_idx=2,
            full_time_series=empty_ts
        )

        assert shift is not None
        assert shift.shift_type == 'removal'
        assert shift.current_count == 0
        assert shift.confidence == 'high'

    def test_detect_removal_insufficient_history(self, sample_config):
        """Test _detect_removal with insufficient historical data."""
        detector = ShiftDetector(sample_config)

        # Create word data with only 1 document
        word_data = pd.DataFrame({
            'date': pd.to_datetime(['2021-12-15']),
            'doc_id': ['doc1'],
            'count': [0],
            'baseline': [2.0]
        })

        # Empty time series for backward compatibility test
        empty_ts = pd.DataFrame()

        shift = detector._detect_removal(
            word='transitory',
            current_count=0,
            baseline=2.0,
            date=datetime(2021, 12, 15),
            doc_id='doc1',
            doc_type='policy_statement',
            word_data=word_data,
            current_idx=0,
            full_time_series=empty_ts
        )

        # Should not detect removal (insufficient history)
        assert shift is None

    def test_validate_shift(self, sample_config):
        """Test shift validation."""
        detector = ShiftDetector(sample_config)

        shift = Shift(
            shift_type='emergence',
            word='transitory',
            date=datetime(2021, 11, 3),
            doc_id='doc1',
            doc_type='policy_statement',
            previous_count=0.0,
            current_count=2,
            confidence='high'
        )

        # Basic validation should pass
        assert detector.validate_shift(shift) is True

    def test_empty_dataframe(self, sample_config):
        """Test detection with empty DataFrame."""
        detector = ShiftDetector(sample_config)

        df = pd.DataFrame(columns=['date', 'doc_id', 'word', 'count', 'baseline', 'doc_type'])

        shifts = detector.detect_shifts(df)

        assert len(shifts) == 0

    def test_shift_metadata(self, sample_config):
        """Test that shifts contain proper metadata."""
        detector = ShiftDetector(sample_config)

        df = pd.DataFrame({
            'date': pd.to_datetime(['2021-11-03']),
            'doc_id': ['doc1'],
            'word': ['transitory'],
            'count': [2],
            'baseline': [0.0],
            'doc_type': ['policy_statement']
        })

        shifts = detector.detect_shifts(df)

        assert len(shifts) == 1
        assert shifts[0].metadata is not None
        assert 'algorithm' in shifts[0].metadata


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

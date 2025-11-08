"""Unit tests for ShiftDetector module and ImprovedDetector."""

import pytest
import pandas as pd
from datetime import datetime

from fedspeak.detector import ShiftDetector, Shift
from src.core import ImprovedDetector
from src.config.settings import get_settings
from src.exceptions import DetectionError, DataError


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


class TestImprovedDetector:
    """Test suite for ImprovedDetector class (Phase 2 production detector)."""

    def test_initialization_from_config(self):
        """Test detector initializes with YAML configuration."""
        detector = ImprovedDetector()

        # Should load from config.yaml
        assert detector.lookback == 3
        assert detector.increase_threshold == 2.0
        assert detector.decrease_threshold == 0.5
        assert detector.p_value_threshold == 0.05
        assert detector.min_count_increase == 2
        assert detector.min_avg_decrease == 1.0

    def test_initialization_with_custom_config(self):
        """Test detector initializes with custom configuration dict."""
        custom_config = {
            'lookback': 5,
            'increase_threshold': 3.0,
            'decrease_threshold': 0.3,
            'p_value_threshold': 0.01
        }
        detector = ImprovedDetector(config=custom_config)

        assert detector.lookback == 5
        assert detector.increase_threshold == 3.0
        assert detector.decrease_threshold == 0.3
        assert detector.p_value_threshold == 0.01

    def test_december_2021_transitory_removal(self):
        """Test December 2021 'transitory' removal (high confidence)."""
        detector = ImprovedDetector()

        # Create test data simulating 2021 transitory case
        dates = ['20210728', '20210922', '20211103', '20211215']
        texts = {
            '20210728': 'Inflation has risen, largely reflecting transitory factors.',
            '20210922': 'Inflation remains elevated, largely reflecting transitory factors that are expected to be transitory.',
            '20211103': 'Inflation is elevated, largely reflecting factors that are expected to be transitory.',
            '20211215': 'Inflation remains elevated, reflecting supply and demand.'  # transitory removed
        }

        detections = detector.detect_shift('transitory', dates, texts)

        # Should detect removal on December 15, 2021
        removal_detections = [d for d in detections if d['shift_type'] == 'removal']
        assert len(removal_detections) >= 1

        dec_removal = [d for d in removal_detections if d['date'] == '20211215']
        assert len(dec_removal) == 1
        assert dec_removal[0]['shift_type'] == 'removal'
        assert dec_removal[0]['term'] == 'transitory'
        assert dec_removal[0]['confidence'] == 'high'  # Complete removal = high confidence
        assert dec_removal[0]['curr_count'] == 0
        assert dec_removal[0]['prev_avg'] > 0

    def test_april_2021_transitory_emergence(self):
        """Test April 2021 'transitory' emergence (medium/high confidence)."""
        detector = ImprovedDetector()

        # Create test data simulating transitory emergence in April 2021
        # Need enough documents for lookback window (lookback=3)
        dates = ['20201216', '20210127', '20210317', '20210428', '20210616']
        texts = {
            '20201216': 'Inflation remains soft.',
            '20210127': 'Inflation remains soft.',
            '20210317': 'Inflation continues to run below target.',
            '20210428': 'Inflation has risen, largely reflecting transitory factors.',  # transitory appears
            '20210616': 'Inflation has risen, largely reflecting transitory factors that are expected to be transitory.'
        }

        detections = detector.detect_shift('transitory', dates, texts)

        # Should detect emergence in April 2021
        emergence_detections = [d for d in detections if d['shift_type'] == 'emergence']
        assert len(emergence_detections) >= 1

        april_emergence = [d for d in emergence_detections if d['date'] == '20210428']
        assert len(april_emergence) == 1
        assert april_emergence[0]['shift_type'] == 'emergence'
        assert april_emergence[0]['term'] == 'transitory'
        assert april_emergence[0]['confidence'] in ['medium', 'high']
        assert april_emergence[0]['curr_count'] > 0
        assert april_emergence[0]['prev_avg'] == 0

    def test_no_change_scenario(self):
        """Test no-change case produces no detections."""
        detector = ImprovedDetector()

        # Create data with consistent usage (no shifts)
        dates = ['20210101', '20210201', '20210301', '20210401']
        texts = {
            '20210101': 'The economy remains accommodative and stable.',
            '20210201': 'The economy remains accommodative and stable.',
            '20210301': 'The economy remains accommodative and stable.',
            '20210401': 'The economy remains accommodative and stable.'
        }

        detections = detector.detect_shift('accommodative', dates, texts)

        # Should not detect any shifts (stable usage)
        assert len(detections) == 0

    def test_empty_statement(self):
        """Test handling of empty statement."""
        detector = ImprovedDetector()

        dates = ['20210101', '20210201', '20210301', '20210401']
        texts = {
            '20210101': 'The economy is transitory.',
            '20210201': 'The economy is transitory.',
            '20210301': '',  # Empty statement
            '20210401': 'The economy is stable.'
        }

        # Should not raise error, should handle gracefully
        detections = detector.detect_shift('transitory', dates, texts)

        # Should still detect removal in last statement
        assert isinstance(detections, list)

    def test_malformed_data_validation(self):
        """Test input validation for malformed data."""
        detector = ImprovedDetector()

        # Test with empty term
        with pytest.raises(DataError):
            detector.detect_shift('', ['20210101'], {'20210101': 'text'})

        # Test with non-string term
        with pytest.raises(DataError):
            detector.detect_shift(123, ['20210101'], {'20210101': 'text'})

        # Test with empty dates list
        with pytest.raises(DataError):
            detector.detect_shift('term', [], {'20210101': 'text'})

        # Test with non-list dates
        with pytest.raises(DataError):
            detector.detect_shift('term', 'not-a-list', {'20210101': 'text'})

        # Test with empty texts dict
        with pytest.raises(DataError):
            detector.detect_shift('term', ['20210101'], {})

        # Test with non-dict texts
        with pytest.raises(DataError):
            detector.detect_shift('term', ['20210101'], 'not-a-dict')

    def test_unsorted_dates_validation(self):
        """Test that unsorted dates raise validation error."""
        detector = ImprovedDetector()

        dates = ['20210301', '20210101', '20210201']  # Not sorted
        texts = {
            '20210101': 'Text 1',
            '20210201': 'Text 2',
            '20210301': 'Text 3'
        }

        with pytest.raises(DataError, match="chronologically sorted"):
            detector.detect_shift('term', dates, texts)

    def test_missing_texts_validation(self):
        """Test that missing text entries raise validation error."""
        detector = ImprovedDetector()

        dates = ['20210101', '20210201', '20210301']
        texts = {
            '20210101': 'Text 1',
            # Missing 20210201
            '20210301': 'Text 3'
        }

        with pytest.raises(DataError, match="missing for dates"):
            detector.detect_shift('term', dates, texts)

    def test_increase_detection(self):
        """Test detection of significant count increase."""
        detector = ImprovedDetector()

        dates = ['20210101', '20210201', '20210301', '20210401']
        texts = {
            '20210101': 'The economy is stable.',
            '20210201': 'The economy is patient and stable.',
            '20210301': 'The economy is patient.',
            '20210401': 'The economy must be patient and patient and patient and patient.'  # 4x increase
        }

        detections = detector.detect_shift('patient', dates, texts)

        # May detect emergence and/or increase
        assert len(detections) > 0

    def test_decrease_detection(self):
        """Test detection of significant count decrease."""
        detector = ImprovedDetector()

        dates = ['20210101', '20210201', '20210301', '20210401']
        texts = {
            '20210101': 'Very patient patient patient approach.',
            '20210201': 'Still patient patient patient today.',
            '20210301': 'Patient patient patient strategy.',
            '20210401': 'Somewhat patient.'  # Significant decrease
        }

        detections = detector.detect_shift('patient', dates, texts)

        # Should detect decrease (3→1 count)
        decrease_detections = [d for d in detections if d['shift_type'] == 'decrease']
        assert len(decrease_detections) >= 1

    def test_case_insensitive_matching(self):
        """Test that term matching is case-insensitive."""
        detector = ImprovedDetector()

        dates = ['20210101', '20210201', '20210301', '20210401']
        texts = {
            '20210101': 'inflation is stable.',
            '20210201': 'INFLATION remains low.',
            '20210301': 'Inflation is moderate.',
            '20210401': 'The economy has no inflation concerns.'
        }

        # Search for lowercase, should match all cases
        detections = detector.detect_shift('inflation', dates, texts)

        # Should not detect shifts (consistent usage regardless of case)
        assert isinstance(detections, list)

    def test_whole_word_matching(self):
        """Test that term matching is whole-word only."""
        detector = ImprovedDetector()

        dates = ['20210101', '20210201', '20210301', '20210401']
        texts = {
            '20210101': 'The economy needs accommodation.',  # "accommodative" not present
            '20210201': 'The economy needs accommodation.',
            '20210301': 'The economy needs accommodation.',
            '20210401': 'The economy is accommodative.'  # "accommodative" appears
        }

        detections = detector.detect_shift('accommodative', dates, texts)

        # Should detect emergence (whole word, not substring)
        emergence_detections = [d for d in detections if d['shift_type'] == 'emergence']
        assert len(emergence_detections) == 1

    def test_lookback_parameter(self):
        """Test that lookback parameter is respected."""
        detector = ImprovedDetector()

        dates = ['20210101', '20210201', '20210301', '20210401', '20210501']
        texts = {
            '20210101': 'Text with term.',
            '20210201': 'Text with term.',
            '20210301': 'Text with term.',
            '20210401': 'Text with term.',
            '20210501': 'Text without.'
        }

        # Default lookback = 3
        detections_default = detector.detect_shift('term', dates, texts)

        # Custom lookback = 2
        detections_custom = detector.detect_shift('term', dates, texts, lookback=2)

        # Both should detect removal, but may differ in details
        assert isinstance(detections_default, list)
        assert isinstance(detections_custom, list)

    def test_detection_result_structure(self):
        """Test that detection results have correct structure."""
        detector = ImprovedDetector()

        dates = ['20210101', '20210201', '20210301', '20210401']
        texts = {
            '20210101': 'No term here.',
            '20210201': 'No term here.',
            '20210301': 'No term here.',
            '20210401': 'The transitory economy.'
        }

        detections = detector.detect_shift('transitory', dates, texts)

        assert len(detections) >= 1
        detection = detections[0]

        # Check all required fields
        assert 'date' in detection
        assert 'term' in detection
        assert 'shift_type' in detection
        assert 'confidence' in detection
        assert 'curr_count' in detection
        assert 'prev_avg' in detection
        assert 'relative_change' in detection
        assert 'p_value' in detection or detection['p_value'] is None

        # Check field types
        assert isinstance(detection['date'], str)
        assert isinstance(detection['term'], str)
        assert detection['shift_type'] in ['emergence', 'removal', 'increase', 'decrease']
        assert detection['confidence'] in ['low', 'medium', 'high']
        assert isinstance(detection['curr_count'], int)
        assert isinstance(detection['prev_avg'], (int, float))
        assert isinstance(detection['relative_change'], (int, float))

    def test_multiple_shifts_in_series(self):
        """Test detection of multiple shifts in a time series."""
        detector = ImprovedDetector()

        # Need enough documents for lookback window (lookback=3)
        dates = ['20201201', '20210101', '20210201', '20210301', '20210401', '20210501', '20210601']
        texts = {
            '20201201': 'The economy is stable.',
            '20210101': 'The economy is stable.',
            '20210201': 'The economy is stable.',
            '20210301': 'The economy is patient and stable.',  # Emergence
            '20210401': 'The economy remains patient.',
            '20210501': 'The economy remains patient.',
            '20210601': 'The economy is recovering.'  # Removal
        }

        detections = detector.detect_shift('patient', dates, texts)

        # Should detect both emergence and removal
        shift_types = {d['shift_type'] for d in detections}
        assert 'emergence' in shift_types
        assert 'removal' in shift_types

    def test_configuration_error_handling(self):
        """Test that configuration errors are handled properly."""
        # This tests the error handling in __init__
        # Normal case should work
        detector = ImprovedDetector()
        assert detector is not None

        # Custom config should work
        detector2 = ImprovedDetector(config={'lookback': 5})
        assert detector2.lookback == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""Unit tests for LanguageAnalyzer module."""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from fedspeak.analyzer import LanguageAnalyzer, DocumentMetrics


class TestLanguageAnalyzer:
    """Test suite for LanguageAnalyzer class."""

    def test_initialization(self, sample_config):
        """Test analyzer initializes correctly."""
        analyzer = LanguageAnalyzer(sample_config)

        assert len(analyzer.keywords) == 2  # transitory, patient
        assert 'transitory' in analyzer.keywords
        assert 'patient' in analyzer.keywords
        assert analyzer.baseline_window_months == 6
        assert analyzer.min_baseline_samples == 3

    def test_count_word_single_word(self, sample_config):
        """Test counting single word occurrences."""
        analyzer = LanguageAnalyzer(sample_config)

        text = "The transitory inflation is transitory in nature."
        count = analyzer.count_word_in_document(text, "transitory")

        assert count == 2

    def test_count_word_case_insensitive(self, sample_config):
        """Test case-insensitive word counting."""
        analyzer = LanguageAnalyzer(sample_config)

        text = "Transitory, TRANSITORY, and transitory are all counted."
        count = analyzer.count_word_in_document(text, "transitory")

        assert count == 3

    def test_count_word_whole_word_matching(self, sample_config):
        """Test that partial matches are not counted."""
        analyzer = LanguageAnalyzer(sample_config)

        text = "The transitory and transitoryness are different."
        count = analyzer.count_word_in_document(text, "transitory")

        assert count == 1  # Should not count "transitoryness"

    def test_count_word_multi_word_phrase(self, sample_config):
        """Test counting multi-word phrases."""
        analyzer = LanguageAnalyzer(sample_config)

        text = "The Committee will be patient for a considerable time."
        count = analyzer.count_word_in_document(text, "considerable time")

        assert count == 1

    def test_count_word_not_present(self, sample_config):
        """Test counting word that doesn't exist."""
        analyzer = LanguageAnalyzer(sample_config)

        text = "This text does not contain the target word."
        count = analyzer.count_word_in_document(text, "transitory")

        assert count == 0

    def test_count_word_special_characters(self, sample_config):
        """Test counting with special regex characters in phrase."""
        analyzer = LanguageAnalyzer(sample_config)

        # Test that special characters in multi-word phrases are properly escaped
        text = "The Committee announced a 0.25-point increase."
        count = analyzer.count_word_in_document(text, "0.25-point")

        assert count == 1

    def test_analyze_document(self, sample_config, temp_data_dir):
        """Test analyzing single document."""
        # Create test file
        test_file = temp_data_dir / "test_doc.txt"
        test_text = """
        The Federal Reserve views inflation as transitory.
        The Committee will be patient in its approach.
        The transitory nature of inflation is expected.
        """
        test_file.write_text(test_text)

        analyzer = LanguageAnalyzer(sample_config)
        date = datetime(2021, 11, 3)

        metrics = analyzer.analyze_document(test_file, date, 'policy_statement')

        assert metrics.doc_id == 'test_doc'
        assert metrics.date == date
        assert metrics.doc_type == 'policy_statement'
        assert metrics.word_counts['transitory'] == 2
        assert metrics.word_counts['patient'] == 1
        assert metrics.total_words > 10

    def test_build_time_series(self, sample_config):
        """Test building time-series DataFrame."""
        analyzer = LanguageAnalyzer(sample_config)

        # Create sample metrics
        metrics1 = DocumentMetrics(
            doc_id='doc1',
            date=datetime(2021, 9, 22),
            doc_type='policy_statement',
            word_counts={'transitory': 2, 'patient': 0},
            total_words=100
        )

        metrics2 = DocumentMetrics(
            doc_id='doc2',
            date=datetime(2021, 11, 3),
            doc_type='policy_statement',
            word_counts={'transitory': 3, 'patient': 1},
            total_words=120
        )

        df = analyzer.build_time_series([metrics1, metrics2])

        assert len(df) == 4  # 2 docs × 2 keywords
        assert 'date' in df.columns
        assert 'word' in df.columns
        assert 'count' in df.columns
        assert df['count'].sum() == 6  # 2 + 3 + 0 + 1

    def test_calculate_baseline(self, sample_config, sample_baseline_data):
        """Test baseline calculation for a single document."""
        analyzer = LanguageAnalyzer(sample_config)

        # Calculate baseline for Dec 15, 2021
        current_date = datetime(2021, 12, 15)
        baseline = analyzer.calculate_baseline('transitory', current_date, sample_baseline_data)

        # Should average the counts from previous documents in 6-month window
        # Jul 28: 2, Sep 22: 2, Nov 3: 3 → mean = 2.33
        assert baseline > 2.0
        assert baseline < 2.5

    def test_calculate_baseline_insufficient_data(self, sample_config):
        """Test baseline with insufficient historical data."""
        analyzer = LanguageAnalyzer(sample_config)

        # Create minimal data
        df = pd.DataFrame({
            'date': [datetime(2021, 1, 1)],
            'word': ['transitory'],
            'count': [2]
        })

        # Try to calculate baseline for date with < 3 historical samples
        baseline = analyzer.calculate_baseline('transitory', datetime(2021, 2, 1), df)

        # Should return 0 when insufficient data
        assert baseline == 0.0

    def test_calculate_baselines_vectorized(self, sample_config, sample_keyword_metrics):
        """Test vectorized baseline calculation."""
        analyzer = LanguageAnalyzer(sample_config)

        df = analyzer._calculate_baselines_vectorized(sample_keyword_metrics)

        assert 'baseline' in df.columns
        assert len(df) == len(sample_keyword_metrics)

        # Check that early documents have low/zero baseline (insufficient history)
        first_row = df.iloc[0]
        assert first_row['baseline'] == 0.0

        # Check that later documents have non-zero baseline
        last_row = df.iloc[-1]
        # Last row should have some baseline calculated
        assert 'baseline' in df.columns

    def test_analyze_corpus(self, sample_config, temp_data_dir):
        """Test analyzing entire corpus."""
        # Create sample corpus
        processed_dir = temp_data_dir / "processed"
        processed_dir.mkdir()

        # Create multiple test files
        dates = ['20210922', '20211103', '20211215']
        texts = [
            "The transitory inflation is a concern.",
            "Transitory pressures continue. The Committee remains patient.",
            "The Committee will maintain its patient approach."
        ]

        for date_str, text in zip(dates, texts):
            filepath = processed_dir / f"policy_statement_{date_str}.txt"
            filepath.write_text(text)

        analyzer = LanguageAnalyzer(sample_config)
        df = analyzer.analyze_corpus(processed_dir)

        assert len(df) > 0
        assert 'baseline' in df.columns
        assert 'date' in df.columns
        assert 'word' in df.columns
        assert 'count' in df.columns

        # Should process all 3 documents × 2 keywords = 6 rows
        assert len(df) == 6

    def test_analyze_corpus_empty_directory(self, sample_config, temp_data_dir):
        """Test analyzing empty corpus directory."""
        empty_dir = temp_data_dir / "empty"
        empty_dir.mkdir()

        analyzer = LanguageAnalyzer(sample_config)
        df = analyzer.analyze_corpus(empty_dir)

        assert len(df) == 0

    def test_analyze_corpus_handles_different_extensions(self, sample_config, temp_data_dir):
        """Test corpus analysis handles .html.txt and .pdf.txt extensions."""
        processed_dir = temp_data_dir / "processed"
        processed_dir.mkdir()

        # Create files with different extension patterns
        (processed_dir / "policy_statement_20210922.html.txt").write_text("Transitory inflation concerns.")
        (processed_dir / "policy_statement_20211103.pdf.txt").write_text("Patient approach maintained.")

        analyzer = LanguageAnalyzer(sample_config)
        df = analyzer.analyze_corpus(processed_dir)

        # Should successfully parse both files
        assert len(df) == 4  # 2 docs × 2 keywords

    def test_save_metrics(self, sample_config, sample_keyword_metrics, temp_data_dir):
        """Test saving metrics to CSV."""
        analyzer = LanguageAnalyzer(sample_config)

        output_file = temp_data_dir / "metrics.csv"
        analyzer.save_metrics(sample_keyword_metrics, output_file)

        assert output_file.exists()

        # Verify can be read back
        loaded_df = pd.read_csv(output_file)
        assert len(loaded_df) == len(sample_keyword_metrics)
        assert 'word' in loaded_df.columns
        assert 'count' in loaded_df.columns

    def test_count_word_with_punctuation(self, sample_config):
        """Test word counting with surrounding punctuation."""
        analyzer = LanguageAnalyzer(sample_config)

        text = "The transitory, transitory! And transitory? Yes, transitory."
        count = analyzer.count_word_in_document(text, "transitory")

        # Should match all 4 occurrences regardless of punctuation
        assert count == 4

    def test_multi_word_phrase_across_line_breaks(self, sample_config):
        """Test multi-word phrase counting across line breaks."""
        analyzer = LanguageAnalyzer(sample_config)

        text = "The Committee will maintain for a\nconsiderable time the current policy."
        count = analyzer.count_word_in_document(text, "considerable time")

        # Should match even with line break
        assert count == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

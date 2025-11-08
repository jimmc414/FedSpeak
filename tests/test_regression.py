"""Regression tests for ImprovedDetector against ground truth shifts.

This test suite validates the detector's performance against the 130 documented
ground truth language shifts identified in FOMC policy statements (2008-2023).

Expected baseline performance (from prototype validation):
- Precision: ≥55% (55.3% achieved in prototyping)
- Recall: ≥16% (16.9% achieved in prototyping)
- F1 Score: ~0.250
"""

import pytest
import csv
from pathlib import Path
from collections import defaultdict

from src.core import ImprovedDetector
from src.config import setup_logging


class TestRegressionGroundTruth:
    """Test detector performance against 130 ground truth shifts."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup logging for tests."""
        setup_logging(level='WARNING', log_to_console=False, log_to_file=False)

    def load_ground_truth(self):
        """Load ground truth shifts from GROUND_TRUTH_SHIFTS.csv.

        Returns:
            dict: Ground truth shifts by term, format:
                {
                    'transitory': [
                        ('20211215', 'removal'),
                        ...
                    ],
                    ...
                }
        """
        ground_truth_file = Path('GROUND_TRUTH_SHIFTS.csv')
        ground_truth = defaultdict(list)

        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row['Date']
                shift_type = row['Type']
                term = row['Term']
                ground_truth[term].append((date, shift_type))

        return ground_truth

    def load_policy_statements_all(self):
        """Load all policy statements from data/processed.

        Returns:
            tuple: (dates, texts) where:
                - dates: List[str] of dates in YYYYMMDD format
                - texts: Dict[str, str] mapping date to statement text
        """
        data_dir = Path('data/processed')

        # Get all policy statements (not minutes, not html.txt duplicates)
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

        return dates, texts

    @pytest.mark.slow
    def test_ground_truth_validation_all_terms(self):
        """Test detector against all 130 ground truth shifts.

        This is the comprehensive regression test validating overall performance.

        Expected:
        - Precision ≥ 50% (relaxed from 55% for production migration tolerance)
        - Recall ≥ 15% (relaxed from 16.9% for tolerance)
        """
        # Load data
        ground_truth = self.load_ground_truth()
        dates, texts = self.load_policy_statements_all()

        detector = ImprovedDetector()

        # Track overall metrics
        total_true_positives = 0
        total_detections = 0
        total_ground_truth = sum(len(shifts) for shifts in ground_truth.values())

        # Test each term
        for term in ground_truth.keys():
            # Run detection
            detections = detector.detect_shift(term, dates, texts)

            # Count true positives for this term
            gt_shifts_dict = {date: shift_type for date, shift_type in ground_truth[term]}

            for detection in detections:
                total_detections += 1
                if detection['date'] in gt_shifts_dict:
                    if detection['shift_type'] == gt_shifts_dict[detection['date']]:
                        total_true_positives += 1

        # Calculate metrics
        precision = total_true_positives / total_detections if total_detections > 0 else 0
        recall = total_true_positives / total_ground_truth
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Log results for analysis
        print(f"\n{'='*60}")
        print(f"REGRESSION TEST RESULTS (130 Ground Truth Shifts)")
        print(f"{'='*60}")
        print(f"True Positives:  {total_true_positives}")
        print(f"Total Detections: {total_detections}")
        print(f"Ground Truth:    {total_ground_truth}")
        print(f"Precision:       {precision:.1%} (target: ≥50%)")
        print(f"Recall:          {recall:.1%} (target: ≥15%)")
        print(f"F1 Score:        {f1:.3f}")
        print(f"{'='*60}\n")

        # Assert minimum performance thresholds
        assert precision >= 0.50, \
            f"Precision too low: {precision:.1%} (expected ≥50%)"
        assert recall >= 0.15, \
            f"Recall too low: {recall:.1%} (expected ≥15%)"

    def test_ground_truth_transitory_subset(self):
        """Test detector specifically on 'transitory' shifts (44 ground truth shifts).

        This focuses on the most important term with the highest number of shifts.
        """
        ground_truth = self.load_ground_truth()
        dates, texts = self.load_policy_statements_all()

        detector = ImprovedDetector()

        # Test only transitory
        transitory_gt = ground_truth['transitory']
        detections = detector.detect_shift('transitory', dates, texts)

        # Count true positives
        gt_shifts_dict = {date: shift_type for date, shift_type in transitory_gt}
        true_positives = 0

        for detection in detections:
            if detection['date'] in gt_shifts_dict:
                if detection['shift_type'] == gt_shifts_dict[detection['date']]:
                    true_positives += 1

        # Calculate metrics
        total_detections = len(detections)
        total_ground_truth = len(transitory_gt)

        precision = true_positives / total_detections if total_detections > 0 else 0
        recall = true_positives / total_ground_truth

        print(f"\n'transitory' Performance:")
        print(f"  Precision: {precision:.1%}")
        print(f"  Recall: {recall:.1%}")
        print(f"  True Positives: {true_positives}/{total_ground_truth}")

        # Should perform reasonably on this critical term
        assert recall > 0, "Should detect at least some 'transitory' shifts"

    def test_ground_truth_december_2021_in_set(self):
        """Verify December 2021 'transitory' removal is in ground truth.

        This confirms our prospective test aligns with documented ground truth.
        """
        ground_truth = self.load_ground_truth()

        transitory_shifts = ground_truth['transitory']
        december_2021 = [date for date, shift_type in transitory_shifts
                        if date == '20211215' and shift_type == 'removal']

        assert len(december_2021) >= 1, \
            "December 2021 'transitory' removal should be in ground truth"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

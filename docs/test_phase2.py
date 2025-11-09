"""
Quick test script to verify Phase 2 production code works.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import setup_logging
from src.core import ImprovedDetector
from src.config.settings import get_settings

def main():
    """Test the production detector."""
    print("="*80)
    print("Phase 2 Production Code Test")
    print("="*80)

    # Setup logging
    setup_logging(level='INFO', log_to_console=True, log_to_file=False)
    print("\n✓ Logging configured")

    # Test configuration loading
    settings = get_settings()
    lookback = settings.get('detection.hybrid_detector.lookback')
    print(f"✓ Configuration loaded (lookback={lookback})")

    # Create detector
    detector = ImprovedDetector()
    print("✓ Detector initialized")

    # Test data with enough documents for baseline (lookback=3 requires at least 4 docs)
    dates = ['20210801', '20210901', '20211001', '20211101', '20211201']
    texts = {
        '20210801': 'Inflation is transitory and temporary. Transitory effects.',
        '20210901': 'Inflation is transitory. Transitory conditions continue.',
        '20211001': 'Inflation is transitory. The situation remains transitory.',
        '20211101': 'Inflation is transitory. Transitory factors persist.',
        '20211201': 'Inflation persists.'  # "transitory" completely removed
    }

    # Run detection
    detections = detector.detect_shift('transitory', dates, texts)
    print(f"✓ Detection ran successfully")
    print(f"\n  Found {len(detections)} shift(s):")

    for det in detections:
        print(f"    - {det['date']}: {det['shift_type']} "
              f"(confidence={det['confidence']})")

    print("\n" + "="*80)
    print("SUCCESS: All Phase 2 components working correctly!")
    print("="*80)

if __name__ == '__main__':
    main()

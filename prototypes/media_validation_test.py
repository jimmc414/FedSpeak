"""Media Validation Proof of Concept - December 2021 "Transitory" Removal.

This script demonstrates media coverage validation on the December 15, 2021 FOMC
statement where the Fed famously dropped the word "transitory" from their
inflation language.

Expected Result:
- High media coverage (100+ articles)
- Diverse sources (30+ unique outlets)
- Negative sentiment (hawkish shift)
- Media validation: TRUE

Note: Requires transformers and torch packages (pip install transformers torch)
Note: GDELT API requires no authentication (completely free)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.media_validator import MediaValidator


def main():
    """Test media validation on December 2021 transitory removal."""

    print("=" * 80)
    print("Media Validation Proof of Concept")
    print("Testing: December 15, 2021 - 'Transitory' Removal")
    print("=" * 80)
    print()

    # Initialize media validator
    print("Initializing media validator (loading FinBERT model)...")
    print("Note: First run will download ~400MB model (one-time)")
    print()

    try:
        validator = MediaValidator()
    except Exception as e:
        print(f"❌ Failed to initialize media validator: {e}")
        print()
        print("Troubleshooting:")
        print("1. Install dependencies: pip install transformers torch")
        print("2. Check internet connection (for model download)")
        print("3. Ensure sufficient disk space (~1GB for model)")
        return

    print("✅ Media validator initialized")
    print()

    # Test parameters
    date = "20211215"
    term = "transitory"
    shift_type = "removal"

    print(f"Validating shift:")
    print(f"  Date: {date} (December 15, 2021)")
    print(f"  Term: '{term}'")
    print(f"  Type: {shift_type}")
    print()

    # Run validation
    print("Fetching GDELT coverage data...")
    print("(This may take 10-30 seconds)")
    print()

    try:
        result = validator.validate_shift(date, term, shift_type)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return

    # Display results
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()

    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return

    # Validation status
    validated = result['validated']
    status_symbol = "✅" if validated else "❌"

    print(f"{status_symbol} Validated: {validated}")
    print(f"   Media Score: {result['media_score']:.4f} (threshold: {validator.min_score})")
    print(f"   Indicators Triggered: {result['indicators_triggered']}/3")
    print()

    # Coverage metrics
    print("Coverage Metrics:")
    print(f"  Articles: {result['coverage_volume']} (threshold: {validator.coverage_threshold})")
    signal_coverage = "✅" if result['signals']['coverage_volume'] else "❌"
    print(f"    {signal_coverage} Coverage signal: {result['signals']['coverage_volume']}")

    print(f"  Unique Sources: {result['source_diversity']} (threshold: {validator.diversity_threshold})")
    signal_diversity = "✅" if result['signals']['source_diversity'] else "❌"
    print(f"    {signal_diversity} Diversity signal: {result['signals']['source_diversity']}")
    print()

    # Sentiment analysis
    print("Sentiment Analysis:")
    print(f"  GDELT Tone: {result['gdelt_tone_avg']}")
    print(f"  FinBERT Sentiment: {result['finbert_sentiment_avg']:.4f}")
    print(f"  Hybrid Score: {result['hybrid_sentiment']:.4f} (threshold: ±{validator.sentiment_threshold})")
    print(f"  Sentiment Label: {result['sentiment_label']}")
    signal_sentiment = "✅" if result['signals']['sentiment_significance'] else "❌"
    print(f"    {signal_sentiment} Sentiment signal: {result['signals']['sentiment_significance']}")
    print()

    # Top sources
    if result.get('top_sources'):
        print("Top News Sources:")
        for source in result['top_sources'][:5]:
            print(f"  - {source}")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    summary = validator.get_validation_summary(result)
    print(summary)
    print()

    # Interpretation
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print()

    if validated:
        print("✅ Media coverage CONFIRMS the language shift")
        print("   - Significant media attention to the change")
        print("   - Coverage from diverse, authoritative sources")
        print("   - Sentiment indicates market-moving significance")
        print()
        print("This shift would be classified as TIER 1 (if market also validates)")
    else:
        print("❌ Media coverage does NOT confirm the language shift")
        print("   - Insufficient coverage or source diversity")
        print("   - OR weak sentiment reaction")
        print()
        print("This suggests the shift may not be as significant as detected")

    print()
    print("=" * 80)


if __name__ == '__main__':
    main()

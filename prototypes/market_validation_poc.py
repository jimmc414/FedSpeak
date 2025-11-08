#!/usr/bin/env python3
"""
Proof of Concept: Market Data Validation

Tests market validation on the December 15, 2021 "transitory" removal.
This was a critical shift where the Fed dropped the word "transitory" from
FOMC statements, signaling a major policy pivot on inflation.

Expected Result:
- Market should show strong reaction (treasury yields up, VIX spike, S&P volatility)
- Validation should return validated=True
- This demonstrates the market validation system works as intended

Prerequisites:
1. Install dependencies: pip install fredapi yfinance pytz
2. Obtain FREE FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
3. Set environment variable: export FRED_API_KEY="your_key_here"

Usage:
    python prototypes/market_validation_poc.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.market_validator import MarketValidator
from src.config.settings import get_settings


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_fred_api_key():
    """Check if FRED API key is set."""
    api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        print_section("FRED API KEY REQUIRED")
        print("\nYou need a FREE FRED API key to run this test.")
        print("\nSteps to obtain:")
        print("1. Visit: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("2. Click 'Request API Key'")
        print("3. Create free account (takes 2 minutes)")
        print("4. Copy your API key")
        print("\nThen set environment variable:")
        print("   export FRED_API_KEY='your_key_here'")
        print("\nOr add to ~/.bashrc:")
        print("   echo 'export FRED_API_KEY=\"your_key_here\"' >> ~/.bashrc")
        print("   source ~/.bashrc")
        sys.exit(1)

    print(f"✓ FRED API key found: {api_key[:8]}...")
    return api_key


def test_december_2021_transitory():
    """
    Test December 15, 2021 'transitory' removal.

    This is the most significant Fed communication shift in recent years.
    The Fed dropped "transitory" from FOMC statements after using it for
    8 months (April-November 2021) to describe inflation.

    Expected market reaction:
    - Treasury yields: Should increase (expectations of rate hikes)
    - VIX: Should spike (uncertainty about policy path)
    - S&P 500: Likely down or volatile
    """
    print_section("PROOF OF CONCEPT: December 2021 'Transitory' Removal")

    print("\nContext:")
    print("- Date: December 15, 2021")
    print("- Shift: Removal of word 'transitory' from FOMC statement")
    print("- Significance: Fed acknowledged inflation NOT temporary")
    print("- Impact: Signaled imminent rate hikes (started March 2022)")

    print("\nInitializing Market Validator...")
    try:
        validator = MarketValidator()
        print("✓ MarketValidator initialized")
    except Exception as e:
        print(f"✗ Failed to initialize validator: {e}")
        return False

    # Test date
    test_date = "20211215"  # December 15, 2021

    print(f"\nFetching market data for {test_date}...")
    print("(This may take 10-15 seconds on first run, then cached)")

    try:
        result = validator.validate_shift(
            date=test_date,
            term="transitory",
            shift_type="removal"
        )

        print("\n" + "-" * 70)
        print("VALIDATION RESULTS")
        print("-" * 70)

        # Overall validation
        validated = result.get('validated', False)
        score = result.get('market_score', 0)
        triggered = result.get('indicators_triggered', 0)

        status_symbol = "✓" if validated else "✗"
        print(f"\n{status_symbol} Validated: {validated}")
        print(f"  Market Score: {score:.3f} (threshold: {validator.min_score})")
        print(f"  Indicators Triggered: {triggered}/4 (minimum: {validator.min_indicators})")

        # Individual indicators
        print("\nIndividual Indicators:")
        print("-" * 70)

        dgs2 = result.get('treasury_2yr_change')
        dgs10 = result.get('treasury_10yr_change')
        vix = result.get('vix_change')
        sp500 = result.get('sp500_change')
        signals = result.get('signals', {})

        # Treasury 2-year
        if dgs2 is not None:
            signal = "✓ TRIGGERED" if signals.get('treasury_2yr') else "✗ Not triggered"
            print(f"  2-Year Treasury: {dgs2:+.2f} bps {signal}")
            print(f"    (threshold: ±{validator.treasury_2yr_threshold} bps)")
        else:
            print(f"  2-Year Treasury: No data available")

        # Treasury 10-year
        if dgs10 is not None:
            signal = "✓ TRIGGERED" if signals.get('treasury_10yr') else "✗ Not triggered"
            print(f"  10-Year Treasury: {dgs10:+.2f} bps {signal}")
            print(f"    (threshold: ±{validator.treasury_10yr_threshold} bps)")
        else:
            print(f"  10-Year Treasury: No data available")

        # VIX
        if vix is not None:
            signal = "✓ TRIGGERED" if signals.get('vix') else "✗ Not triggered"
            print(f"  VIX Volatility: {vix:+.2f}% {signal}")
            print(f"    (threshold: +{validator.vix_threshold}%)")
        else:
            print(f"  VIX Volatility: No data available")

        # S&P 500
        if sp500 is not None:
            signal = "✓ TRIGGERED" if signals.get('sp500') else "✗ Not triggered"
            print(f"  S&P 500 (SPY): {sp500:+.2f}% {signal}")
            print(f"    (threshold: ±{validator.sp500_threshold}%)")
        else:
            print(f"  S&P 500: No data available")

        # Summary
        summary = validator.get_validation_summary(result)
        print("\nSummary:")
        print(f"  {summary}")

        # Tier determination
        print("\nAlert Tier Assignment:")
        stat_confidence = "high"  # December 2021 was detected with high confidence
        tier_num, tier_name = validator.determine_tier(stat_confidence, validated)
        print(f"  Statistical Confidence: {stat_confidence}")
        print(f"  Market Validated: {validated}")
        print(f"  → Tier: {tier_num} ({tier_name})")

        if tier_num == 1:
            print("     (Highest quality: both statistical and market evidence)")
        elif tier_num == 2:
            print("     (Statistical evidence only, no market confirmation)")
        else:
            print("     (Low confidence, informational only)")

        print("\n" + "=" * 70)

        if validated:
            print("✓ PROOF OF CONCEPT SUCCESSFUL")
            print("\nThe market validation system correctly identified market")
            print("reaction to the December 2021 'transitory' removal.")
            print("\nNext steps:")
            print("- Run full backtest on 130 ground truth shifts")
            print("- Integrate into production monitoring system")
        else:
            print("⚠ UNEXPECTED RESULT")
            print("\nThe December 2021 shift was NOT market-validated.")
            print("This could mean:")
            print("1. Thresholds are too strict (need tuning)")
            print("2. Market data unavailable for this date")
            print("3. Weekend/holiday (markets closed)")
            print("\nCheck individual indicators above for details.")

        print("=" * 70 + "\n")

        return validated

    except Exception as e:
        print(f"\n✗ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  FedSpeak Phase 5: Market Validation Proof of Concept")
    print("=" * 70)

    # Check API key
    check_fred_api_key()

    # Run test
    success = test_december_2021_transitory()

    # Exit code
    sys.exit(0 if success else 1)

"""
FedSpeak - Federal Reserve Language Shift Detection
====================================================

Production system for prospective detection of significant language shifts
in FOMC policy statements.

Usage:
    from src.core import ImprovedDetector
    from src.config import setup_logging, get_settings

    setup_logging(level='INFO')
    detector = ImprovedDetector()
    shifts = detector.detect_shift(term, dates, texts)
"""

__version__ = '1.0.0'
__author__ = 'FedSpeak Development Team'

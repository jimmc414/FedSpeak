"""Monitoring package for FOMC statement detection.

This package provides real-time monitoring of Federal Reserve FOMC statements
through RSS feed polling and automated shift detection.
"""

from src.monitoring.rss_monitor import RSSMonitor

__all__ = ['RSSMonitor']

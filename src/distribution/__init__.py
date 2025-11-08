"""Alert distribution package.

This package provides alert distribution services including email delivery
and deduplication to prevent duplicate notifications.
"""

from src.distribution.deduplicator import AlertDeduplicator
from src.distribution.email_sender import EmailSender

__all__ = ['AlertDeduplicator', 'EmailSender']

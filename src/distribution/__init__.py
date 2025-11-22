"""Alert distribution package.

This package provides alert distribution services including email delivery
and deduplication to prevent duplicate notifications.
"""

from .deduplicator import AlertDeduplicator
from .email_sender import EmailSender

__all__ = ['AlertDeduplicator', 'EmailSender']

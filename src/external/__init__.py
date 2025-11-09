"""External data sources package for FedSpeak.

This package provides integration with external data sources for
validation and enrichment of FOMC language shift detection.

Phase 6: Media Coverage & Multi-Signal Validation
- GDELT Project for news coverage analysis
- Media cache for storing and managing article data
"""

from src.external.gdelt_client import GDELTClient
from src.external.media_cache import MediaDataCache

__all__ = [
    'GDELTClient',
    'MediaDataCache',
]

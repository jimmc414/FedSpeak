"""
Exploration module for FedSpeak.

This module provides Word2Vec-based semantic exploration tools for
analyzing Federal Reserve policy language and discovering term relationships.

Phase 7: Word2Vec Exploration Dashboard
- Word2Vec model loading and similarity queries
- Policy proximity scoring
- Interactive exploration dashboard
"""

from .word2vec_service import Word2VecExplorer
from .policy_proximity import PolicyProximityScorer

__all__ = [
    'Word2VecExplorer',
    'PolicyProximityScorer',
]

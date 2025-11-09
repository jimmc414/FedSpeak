"""
Word2Vec Exploration Service for FedSpeak.

Provides semantic similarity queries and exploration tools using a Word2Vec model
trained on Federal Reserve policy statements.

Author: Phase 7 Implementation
Date: November 8, 2025
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from gensim.models import Word2Vec
from collections import Counter

logger = logging.getLogger(__name__)


class Word2VecExplorer:
    """
    Word2Vec exploration service for semantic similarity analysis.

    This class provides methods for querying a Word2Vec model trained on FOMC
    policy statements to discover semantic relationships between terms.
    """

    # Singleton pattern - model loaded once and reused
    _instance = None
    _model = None
    _model_path = None

    def __new__(cls, model_path: Optional[str] = None):
        """Singleton pattern to ensure model is loaded only once."""
        if cls._instance is None:
            cls._instance = super(Word2VecExplorer, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize Word2Vec explorer.

        Args:
            model_path: Path to Word2Vec model file. If None, uses default location.
        """
        # Only initialize once
        if Word2VecExplorer._model is not None:
            return

        # Determine model path
        if model_path is None:
            # Default: prototypes/results/fed_word2vec.model
            project_root = Path(__file__).parent.parent.parent
            model_path = project_root / 'prototypes' / 'results' / 'fed_word2vec.model'

        self.model_path = Path(model_path)
        Word2VecExplorer._model_path = self.model_path

        # Load model
        try:
            logger.info(f"Loading Word2Vec model from {self.model_path}")
            Word2VecExplorer._model = Word2Vec.load(str(self.model_path))
            self.wv = Word2VecExplorer._model.wv
            logger.info(f"Model loaded successfully. Vocabulary: {len(self.wv):,} words")
        except FileNotFoundError:
            logger.error(f"Word2Vec model not found at {self.model_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to load Word2Vec model: {e}")
            raise

    @property
    def model(self):
        """Get the loaded Word2Vec model."""
        return Word2VecExplorer._model

    def check_word_exists(self, word: str) -> bool:
        """
        Check if a word exists in the vocabulary.

        Args:
            word: Word to check (case-insensitive)

        Returns:
            True if word exists in vocabulary, False otherwise
        """
        word_lower = word.lower()

        # Check both with and without underscores for multi-word phrases
        word_with_underscores = word_lower.replace(' ', '_')

        return word_lower in self.wv or word_with_underscores in self.wv

    def normalize_word(self, word: str) -> str:
        """
        Normalize word for lookup in vocabulary.

        Handles:
        - Case normalization (lowercase)
        - Space-to-underscore conversion for multi-word phrases

        Args:
            word: Word to normalize

        Returns:
            Normalized word that exists in vocabulary

        Raises:
            KeyError: If word not found in vocabulary
        """
        word_lower = word.lower()

        # Try original (lowercased)
        if word_lower in self.wv:
            return word_lower

        # Try with underscores
        word_with_underscores = word_lower.replace(' ', '_')
        if word_with_underscores in self.wv:
            return word_with_underscores

        # Word not found
        raise KeyError(f"Word '{word}' not found in vocabulary")

    def get_similar_terms(self, word: str, topn: int = 10) -> Dict:
        """
        Find most similar terms to a given word.

        Args:
            word: Query word
            topn: Number of similar words to return (default: 10)

        Returns:
            Dictionary with:
                - success: Boolean indicating success
                - word: Original query word
                - word_normalized: Normalized word used for query
                - similar: List of (word, similarity_score) tuples
                - error: Error message if failed
        """
        try:
            # Normalize word
            word_normalized = self.normalize_word(word)

            # Get similar words
            similar_words = self.wv.most_similar(word_normalized, topn=topn)

            return {
                'success': True,
                'word': word,
                'word_normalized': word_normalized,
                'similar': [{'word': w, 'score': float(score)} for w, score in similar_words],
                'count': len(similar_words),
                'error': None
            }

        except KeyError as e:
            logger.warning(f"Word not in vocabulary: {word}")
            return {
                'success': False,
                'word': word,
                'word_normalized': None,
                'similar': [],
                'count': 0,
                'error': f"Word '{word}' not found in vocabulary"
            }
        except Exception as e:
            logger.error(f"Error finding similar terms for '{word}': {e}")
            return {
                'success': False,
                'word': word,
                'word_normalized': None,
                'similar': [],
                'count': 0,
                'error': str(e)
            }

    def calculate_similarity(self, word1: str, word2: str) -> Dict:
        """
        Calculate cosine similarity between two words.

        Args:
            word1: First word
            word2: Second word

        Returns:
            Dictionary with:
                - success: Boolean indicating success
                - word1: First word (original)
                - word2: Second word (original)
                - word1_normalized: Normalized first word
                - word2_normalized: Normalized second word
                - similarity: Cosine similarity score (0-1)
                - error: Error message if failed
        """
        try:
            # Normalize words
            word1_normalized = self.normalize_word(word1)
            word2_normalized = self.normalize_word(word2)

            # Calculate similarity
            similarity = self.wv.similarity(word1_normalized, word2_normalized)

            return {
                'success': True,
                'word1': word1,
                'word2': word2,
                'word1_normalized': word1_normalized,
                'word2_normalized': word2_normalized,
                'similarity': float(similarity),
                'error': None
            }

        except KeyError as e:
            logger.warning(f"Word not in vocabulary: {word1} or {word2}")
            return {
                'success': False,
                'word1': word1,
                'word2': word2,
                'word1_normalized': None,
                'word2_normalized': None,
                'similarity': 0.0,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error calculating similarity between '{word1}' and '{word2}': {e}")
            return {
                'success': False,
                'word1': word1,
                'word2': word2,
                'word1_normalized': None,
                'word2_normalized': None,
                'similarity': 0.0,
                'error': str(e)
            }

    def get_vocabulary_stats(self) -> Dict:
        """
        Get comprehensive vocabulary statistics.

        Returns:
            Dictionary with:
                - vocabulary_size: Total number of words
                - top_words: List of (word, count) for most frequent words
                - sample_terms: Sample of interesting terms
                - multi_word_phrases: List of multi-word phrase tokens
        """
        try:
            # Vocabulary size
            vocab_size = len(self.wv)

            # Get word counts (from model's vocabulary)
            # Note: Word2Vec stores vocab counts in vocab objects
            word_counts = []
            for word in self.wv.index_to_key[:100]:  # Top 100 by frequency
                count = self.wv.get_vecattr(word, "count")
                word_counts.append((word, int(count)))

            # Sort by count descending
            word_counts.sort(key=lambda x: x[1], reverse=True)

            # Find multi-word phrases (contain underscore)
            multi_word_phrases = [word for word in self.wv.index_to_key if '_' in word]

            # Sample interesting Fed-specific terms
            interesting_terms = []
            for term in ['accommodative', 'transitory', 'inflation', 'employment',
                        'monetary_policy', 'federal_reserve', 'considerable_time',
                        'patient', 'gradual', 'hawkish', 'dovish']:
                if term in self.wv:
                    interesting_terms.append(term)

            return {
                'success': True,
                'vocabulary_size': vocab_size,
                'top_words': word_counts[:20],
                'multi_word_phrases_count': len(multi_word_phrases),
                'multi_word_phrases_sample': multi_word_phrases[:10],
                'interesting_terms': interesting_terms,
                'model_path': str(Word2VecExplorer._model_path),
                'error': None
            }

        except Exception as e:
            logger.error(f"Error getting vocabulary stats: {e}")
            return {
                'success': False,
                'vocabulary_size': 0,
                'top_words': [],
                'multi_word_phrases_count': 0,
                'multi_word_phrases_sample': [],
                'interesting_terms': [],
                'model_path': None,
                'error': str(e)
            }

    def search_vocabulary(self, query: str, limit: int = 20) -> Dict:
        """
        Search vocabulary for words matching a query (for autocomplete).

        Args:
            query: Search query (partial word match)
            limit: Maximum number of results

        Returns:
            Dictionary with:
                - success: Boolean
                - query: Original query
                - matches: List of matching words
                - count: Number of matches
        """
        try:
            query_lower = query.lower()

            # Find words that start with or contain the query
            matches_start = []
            matches_contain = []

            for word in self.wv.index_to_key:
                if word.startswith(query_lower):
                    matches_start.append(word)
                elif query_lower in word:
                    matches_contain.append(word)

                # Stop if we have enough
                if len(matches_start) >= limit:
                    break

            # Combine: prioritize starts-with matches
            all_matches = matches_start + matches_contain
            all_matches = all_matches[:limit]

            return {
                'success': True,
                'query': query,
                'matches': all_matches,
                'count': len(all_matches),
                'error': None
            }

        except Exception as e:
            logger.error(f"Error searching vocabulary: {e}")
            return {
                'success': False,
                'query': query,
                'matches': [],
                'count': 0,
                'error': str(e)
            }

    def get_word_vector(self, word: str) -> Optional[Dict]:
        """
        Get the embedding vector for a word.

        Args:
            word: Word to get vector for

        Returns:
            Dictionary with word and vector, or None if not found
        """
        try:
            word_normalized = self.normalize_word(word)
            vector = self.wv[word_normalized]

            return {
                'success': True,
                'word': word,
                'word_normalized': word_normalized,
                'vector': vector.tolist(),
                'vector_size': len(vector),
                'error': None
            }

        except KeyError:
            return {
                'success': False,
                'word': word,
                'word_normalized': None,
                'vector': None,
                'vector_size': 0,
                'error': f"Word '{word}' not found in vocabulary"
            }

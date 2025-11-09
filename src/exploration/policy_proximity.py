"""
Policy Proximity Scoring for FedSpeak.

Calculates how "policy-relevant" a term is by measuring its semantic proximity
to core monetary policy concepts.

Author: Phase 7 Implementation
Date: November 8, 2025
"""

import logging
from typing import List, Dict, Optional
from src.exploration.word2vec_service import Word2VecExplorer

logger = logging.getLogger(__name__)


class PolicyProximityScorer:
    """
    Calculate policy proximity scores for terms.

    Policy proximity measures how semantically close a term is to core
    monetary policy concepts (inflation, employment, growth, etc.).
    """

    # Default policy seed terms (core Fed policy concepts)
    DEFAULT_POLICY_SEEDS = [
        'inflation',
        'employment',
        'growth',
        'policy',
        'rate',
        'risk',
        'economy',
        'labor',
        'prices'
    ]

    def __init__(self, explorer: Optional[Word2VecExplorer] = None,
                 policy_seeds: Optional[List[str]] = None):
        """
        Initialize policy proximity scorer.

        Args:
            explorer: Word2VecExplorer instance. If None, creates new one.
            policy_seeds: List of policy seed terms. If None, uses defaults.
        """
        self.explorer = explorer or Word2VecExplorer()
        self.policy_seeds = policy_seeds or self.DEFAULT_POLICY_SEEDS

        # Filter policy seeds to only those that exist in vocabulary
        self.valid_seeds = []
        for seed in self.policy_seeds:
            if self.explorer.check_word_exists(seed):
                try:
                    normalized = self.explorer.normalize_word(seed)
                    self.valid_seeds.append(normalized)
                except KeyError:
                    continue

        logger.info(
            f"PolicyProximityScorer initialized with "
            f"{len(self.valid_seeds)}/{len(self.policy_seeds)} valid seed terms"
        )

    def calculate_proximity_score(self, word: str) -> Dict:
        """
        Calculate policy proximity score for a word.

        The score is the average cosine similarity between the word and
        all policy seed terms.

        Args:
            word: Word to score

        Returns:
            Dictionary with:
                - success: Boolean
                - word: Original word
                - word_normalized: Normalized word
                - proximity_score: Average similarity to policy seeds (0-1)
                - seed_scores: Individual similarity to each seed term
                - closest_seed: Most similar policy seed term
                - furthest_seed: Least similar policy seed term
                - error: Error message if failed
        """
        try:
            # Normalize word
            word_normalized = self.explorer.normalize_word(word)

            # Calculate similarity to each policy seed
            seed_scores = []
            for seed in self.valid_seeds:
                similarity = self.explorer.wv.similarity(word_normalized, seed)
                seed_scores.append({
                    'seed': seed,
                    'similarity': float(similarity)
                })

            # Sort by similarity (descending)
            seed_scores.sort(key=lambda x: x['similarity'], reverse=True)

            # Calculate average proximity score
            avg_score = sum(s['similarity'] for s in seed_scores) / len(seed_scores)

            # Get closest and furthest seeds
            closest_seed = seed_scores[0] if seed_scores else None
            furthest_seed = seed_scores[-1] if seed_scores else None

            return {
                'success': True,
                'word': word,
                'word_normalized': word_normalized,
                'proximity_score': round(avg_score, 4),
                'seed_scores': seed_scores,
                'closest_seed': closest_seed,
                'furthest_seed': furthest_seed,
                'num_seeds': len(self.valid_seeds),
                'error': None
            }

        except KeyError:
            logger.warning(f"Word not in vocabulary: {word}")
            return {
                'success': False,
                'word': word,
                'word_normalized': None,
                'proximity_score': 0.0,
                'seed_scores': [],
                'closest_seed': None,
                'furthest_seed': None,
                'num_seeds': len(self.valid_seeds),
                'error': f"Word '{word}' not found in vocabulary"
            }
        except Exception as e:
            logger.error(f"Error calculating policy proximity for '{word}': {e}")
            return {
                'success': False,
                'word': word,
                'word_normalized': None,
                'proximity_score': 0.0,
                'seed_scores': [],
                'closest_seed': None,
                'furthest_seed': None,
                'num_seeds': len(self.valid_seeds),
                'error': str(e)
            }

    def compare_terms(self, word1: str, word2: str) -> Dict:
        """
        Compare policy proximity of two terms.

        Args:
            word1: First word
            word2: Second word

        Returns:
            Dictionary with proximity scores for both words and comparison
        """
        try:
            # Calculate proximity for both words
            score1 = self.calculate_proximity_score(word1)
            score2 = self.calculate_proximity_score(word2)

            if not score1['success'] or not score2['success']:
                return {
                    'success': False,
                    'word1_score': score1,
                    'word2_score': score2,
                    'difference': 0.0,
                    'more_policy_relevant': None,
                    'error': 'One or both words not found in vocabulary'
                }

            # Calculate difference
            difference = score1['proximity_score'] - score2['proximity_score']

            # Determine which is more policy-relevant
            if abs(difference) < 0.01:
                more_relevant = 'equal'
            elif difference > 0:
                more_relevant = word1
            else:
                more_relevant = word2

            return {
                'success': True,
                'word1_score': score1,
                'word2_score': score2,
                'difference': round(difference, 4),
                'more_policy_relevant': more_relevant,
                'error': None
            }

        except Exception as e:
            logger.error(f"Error comparing terms '{word1}' and '{word2}': {e}")
            return {
                'success': False,
                'word1_score': None,
                'word2_score': None,
                'difference': 0.0,
                'more_policy_relevant': None,
                'error': str(e)
            }

    def rank_terms(self, words: List[str]) -> Dict:
        """
        Rank multiple terms by policy proximity.

        Args:
            words: List of words to rank

        Returns:
            Dictionary with ranked results
        """
        try:
            # Calculate proximity for all words
            results = []
            for word in words:
                score_result = self.calculate_proximity_score(word)
                if score_result['success']:
                    results.append({
                        'word': word,
                        'proximity_score': score_result['proximity_score'],
                        'closest_seed': score_result['closest_seed']['seed']
                    })

            # Sort by proximity score (descending)
            results.sort(key=lambda x: x['proximity_score'], reverse=True)

            return {
                'success': True,
                'ranked_terms': results,
                'count': len(results),
                'most_relevant': results[0] if results else None,
                'least_relevant': results[-1] if results else None,
                'error': None
            }

        except Exception as e:
            logger.error(f"Error ranking terms: {e}")
            return {
                'success': False,
                'ranked_terms': [],
                'count': 0,
                'most_relevant': None,
                'least_relevant': None,
                'error': str(e)
            }

    def get_policy_seeds_info(self) -> Dict:
        """
        Get information about the policy seed terms used for scoring.

        Returns:
            Dictionary with seed term information
        """
        return {
            'success': True,
            'policy_seeds': self.policy_seeds,
            'valid_seeds': self.valid_seeds,
            'num_total': len(self.policy_seeds),
            'num_valid': len(self.valid_seeds),
            'missing_seeds': [s for s in self.policy_seeds if s not in self.valid_seeds]
        }

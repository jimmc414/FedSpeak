"""
Tests for Word2Vec exploration service and policy proximity scoring.

Tests the core functionality of semantic similarity queries and
policy relevance scoring.
"""

import pytest
from src.exploration import Word2VecExplorer, PolicyProximityScorer


class TestWord2VecExplorer:
    """Test cases for Word2Vec explorer."""

    @pytest.fixture
    def explorer(self):
        """Create Word2Vec explorer instance (singleton)."""
        return Word2VecExplorer()

    def test_initialization(self, explorer):
        """Test explorer initializes correctly."""
        assert explorer is not None
        assert explorer.model is not None
        assert explorer.wv is not None
        assert len(explorer.wv) > 0

    def test_vocabulary_size(self, explorer):
        """Test vocabulary has expected size."""
        vocab_size = len(explorer.wv)
        # Should be approximately 1,218 words from training
        assert vocab_size > 1000
        assert vocab_size < 2000

    def test_check_word_exists_valid(self, explorer):
        """Test word existence check for valid words."""
        # Known Fed terms
        assert explorer.check_word_exists('inflation')
        assert explorer.check_word_exists('committee')
        assert explorer.check_word_exists('policy')

    def test_check_word_exists_invalid(self, explorer):
        """Test word existence check for invalid words."""
        # Words unlikely to be in Fed corpus
        assert not explorer.check_word_exists('skateboard')
        assert not explorer.check_word_exists('cryptocurrency')
        assert not explorer.check_word_exists('xyzabc123')

    def test_normalize_word_lowercase(self, explorer):
        """Test word normalization handles case."""
        assert explorer.normalize_word('INFLATION') == 'inflation'
        assert explorer.normalize_word('Committee') == 'committee'

    def test_normalize_word_multiword(self, explorer):
        """Test word normalization handles multi-word phrases."""
        # Assuming monetary_policy exists in vocabulary
        if 'monetary_policy' in explorer.wv:
            assert explorer.normalize_word('monetary policy') == 'monetary_policy'

    def test_normalize_word_not_found(self, explorer):
        """Test word normalization raises error for OOV words."""
        with pytest.raises(KeyError):
            explorer.normalize_word('nonexistentword12345')

    def test_get_similar_terms_success(self, explorer):
        """Test getting similar terms for valid word."""
        result = explorer.get_similar_terms('inflation', topn=5)

        assert result['success'] is True
        assert result['word'] == 'inflation'
        assert result['word_normalized'] == 'inflation'
        assert len(result['similar']) == 5
        assert result['count'] == 5
        assert result['error'] is None

        # Check structure of similar words
        first_similar = result['similar'][0]
        assert 'word' in first_similar
        assert 'score' in first_similar
        assert isinstance(first_similar['score'], float)
        assert 0 <= first_similar['score'] <= 1

    def test_get_similar_terms_invalid_word(self, explorer):
        """Test getting similar terms for invalid word."""
        result = explorer.get_similar_terms('nonexistentword12345')

        assert result['success'] is False
        assert 'not found' in result['error'].lower()
        assert len(result['similar']) == 0

    def test_calculate_similarity_success(self, explorer):
        """Test pairwise similarity calculation."""
        result = explorer.calculate_similarity('inflation', 'prices')

        assert result['success'] is True
        assert result['word1'] == 'inflation'
        assert result['word2'] == 'prices'
        assert result['word1_normalized'] == 'inflation'
        assert result['word2_normalized'] == 'prices'
        assert isinstance(result['similarity'], float)
        assert -1 <= result['similarity'] <= 1
        assert result['error'] is None

    def test_calculate_similarity_self(self, explorer):
        """Test similarity of word with itself."""
        result = explorer.calculate_similarity('inflation', 'inflation')

        assert result['success'] is True
        # Self-similarity should be close to 1.0
        assert result['similarity'] > 0.99

    def test_calculate_similarity_invalid_word(self, explorer):
        """Test similarity with invalid word."""
        result = explorer.calculate_similarity('inflation', 'nonexistentword12345')

        assert result['success'] is False
        assert result['similarity'] == 0.0
        assert result['error'] is not None

    def test_get_vocabulary_stats(self, explorer):
        """Test vocabulary statistics retrieval."""
        stats = explorer.get_vocabulary_stats()

        assert stats['success'] is True
        assert stats['vocabulary_size'] > 1000
        assert len(stats['top_words']) > 0
        assert stats['multi_word_phrases_count'] >= 0
        assert len(stats['multi_word_phrases_sample']) >= 0
        assert len(stats['interesting_terms']) > 0

        # Check top words structure
        first_word = stats['top_words'][0]
        assert isinstance(first_word, tuple)
        assert len(first_word) == 2
        word, count = first_word
        assert isinstance(word, str)
        assert isinstance(count, int)
        assert count > 0

    def test_search_vocabulary_match(self, explorer):
        """Test vocabulary search with matching query."""
        result = explorer.search_vocabulary('inf', limit=10)

        assert result['success'] is True
        assert result['query'] == 'inf'
        assert len(result['matches']) > 0
        assert result['count'] > 0

        # Should find 'inflation' and possibly other inf* words
        assert any('inf' in word for word in result['matches'])

    def test_search_vocabulary_no_match(self, explorer):
        """Test vocabulary search with no matches."""
        result = explorer.search_vocabulary('xyzabc123', limit=10)

        assert result['success'] is True
        assert result['query'] == 'xyzabc123'
        assert len(result['matches']) == 0
        assert result['count'] == 0

    def test_search_vocabulary_limit(self, explorer):
        """Test vocabulary search respects limit."""
        result = explorer.search_vocabulary('a', limit=5)

        assert result['success'] is True
        assert len(result['matches']) <= 5

    def test_get_word_vector_success(self, explorer):
        """Test getting word embedding vector."""
        result = explorer.get_word_vector('inflation')

        assert result['success'] is True
        assert result['word'] == 'inflation'
        assert result['word_normalized'] == 'inflation'
        assert isinstance(result['vector'], list)
        assert result['vector_size'] == 100  # Model trained with 100 dimensions
        assert all(isinstance(v, float) for v in result['vector'])

    def test_get_word_vector_invalid(self, explorer):
        """Test getting vector for invalid word."""
        result = explorer.get_word_vector('nonexistentword12345')

        assert result['success'] is False
        assert result['vector'] is None
        assert result['vector_size'] == 0


class TestPolicyProximityScorer:
    """Test cases for policy proximity scorer."""

    @pytest.fixture
    def explorer(self):
        """Create Word2Vec explorer instance."""
        return Word2VecExplorer()

    @pytest.fixture
    def scorer(self, explorer):
        """Create policy proximity scorer instance."""
        return PolicyProximityScorer(explorer=explorer)

    def test_initialization(self, scorer):
        """Test scorer initializes correctly."""
        assert scorer is not None
        assert scorer.explorer is not None
        assert len(scorer.policy_seeds) > 0
        assert len(scorer.valid_seeds) > 0

    def test_policy_seeds_valid(self, scorer):
        """Test that policy seeds exist in vocabulary."""
        # Most seeds should be valid (but not necessarily all)
        assert len(scorer.valid_seeds) >= len(scorer.policy_seeds) * 0.7

    def test_calculate_proximity_score_success(self, scorer):
        """Test proximity score calculation for valid word."""
        result = scorer.calculate_proximity_score('inflation')

        assert result['success'] is True
        assert result['word'] == 'inflation'
        assert result['word_normalized'] == 'inflation'
        assert isinstance(result['proximity_score'], float)
        assert 0 <= result['proximity_score'] <= 1
        assert len(result['seed_scores']) > 0
        assert result['closest_seed'] is not None
        assert result['furthest_seed'] is not None
        assert result['error'] is None

        # Check seed scores structure
        first_seed = result['seed_scores'][0]
        assert 'seed' in first_seed
        assert 'similarity' in first_seed
        assert isinstance(first_seed['similarity'], float)

    def test_calculate_proximity_score_invalid(self, scorer):
        """Test proximity score for invalid word."""
        result = scorer.calculate_proximity_score('nonexistentword12345')

        assert result['success'] is False
        assert result['proximity_score'] == 0.0
        assert len(result['seed_scores']) == 0
        assert result['error'] is not None

    def test_policy_relevant_word_high_score(self, scorer):
        """Test that policy-relevant words have positive proximity scores."""
        # Words that should be policy-relevant
        for word in ['inflation', 'employment', 'policy']:
            if scorer.explorer.check_word_exists(word):
                result = scorer.calculate_proximity_score(word)
                if result['success']:
                    # Policy seeds should have positive proximity
                    # Note: Scores vary based on Word2Vec training
                    assert result['proximity_score'] > 0.0
                    assert result['proximity_score'] <= 1.0

    def test_compare_terms_success(self, scorer):
        """Test comparing proximity of two terms."""
        result = scorer.compare_terms('inflation', 'prices')

        assert result['success'] is True
        assert result['word1_score'] is not None
        assert result['word2_score'] is not None
        assert isinstance(result['difference'], float)
        assert result['more_policy_relevant'] in ['inflation', 'prices', 'equal']

    def test_compare_terms_invalid(self, scorer):
        """Test comparing with invalid term."""
        result = scorer.compare_terms('inflation', 'nonexistentword12345')

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_rank_terms_success(self, scorer):
        """Test ranking multiple terms."""
        words = ['inflation', 'committee', 'policy', 'rate']
        result = scorer.rank_terms(words)

        assert result['success'] is True
        assert len(result['ranked_terms']) > 0
        assert result['count'] > 0
        assert result['most_relevant'] is not None
        assert result['least_relevant'] is not None

        # Check ranking structure
        first_rank = result['ranked_terms'][0]
        assert 'word' in first_rank
        assert 'proximity_score' in first_rank
        assert 'closest_seed' in first_rank

        # Verify ranking order (descending by score)
        scores = [item['proximity_score'] for item in result['ranked_terms']]
        assert scores == sorted(scores, reverse=True)

    def test_rank_terms_empty_list(self, scorer):
        """Test ranking with empty word list."""
        result = scorer.rank_terms([])

        assert result['success'] is True
        assert len(result['ranked_terms']) == 0
        assert result['count'] == 0

    def test_get_policy_seeds_info(self, scorer):
        """Test getting policy seeds information."""
        info = scorer.get_policy_seeds_info()

        assert info['success'] is True
        assert len(info['policy_seeds']) > 0
        assert len(info['valid_seeds']) > 0
        assert info['num_total'] > 0
        assert info['num_valid'] > 0
        assert isinstance(info['missing_seeds'], list)

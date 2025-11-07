#!/usr/bin/env python3
"""
Synonym Discovery with Word2Vec
================================

Tests if Word2Vec can automatically discover synonyms for Fed keywords.

Critical Test A: Validate known synonyms from config.yaml
Critical Test B: Discover new synonym candidates

Author: Phase 3 Semantic Testing
Date: November 6, 2025
"""

import os
import json
import yaml
from datetime import datetime
from gensim.models import Word2Vec
import numpy as np


class SynonymDiscoveryTester:
    """Test Word2Vec synonym discovery capabilities"""

    def __init__(self, model_path, config_path):
        self.model = Word2Vec.load(model_path)
        self.wv = self.model.wv

        # Load config to get known synonyms
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def check_word_exists(self, word):
        """Check if word exists in vocabulary"""
        return word.lower() in self.wv

    def find_similar(self, word, topn=10):
        """Find most similar words"""
        word = word.lower()
        if not self.check_word_exists(word):
            return None, f"'{word}' not in vocabulary"

        similar = self.wv.most_similar(word, topn=topn)
        return similar, None

    def get_similarity(self, word1, word2):
        """Get similarity between two words"""
        word1 = word1.lower()
        word2 = word2.lower()

        if not self.check_word_exists(word1):
            return None, f"'{word1}' not in vocabulary"
        if not self.check_word_exists(word2):
            return None, f"'{word2}' not in vocabulary"

        return self.wv.similarity(word1, word2), None

    def test_known_synonyms(self):
        """Test A: Validate known synonyms from config"""
        print("\n" + "="*80)
        print("TEST A: KNOWN SYNONYM VALIDATION")
        print("="*80)
        print("\nTesting if known synonyms appear in top 10 most similar words...")

        results = []

        for keyword_config in self.config['keywords']:
            keyword = keyword_config['word']
            known_synonyms = keyword_config.get('synonyms', [])

            if not known_synonyms:
                continue

            print(f"\n{keyword.upper()}")
            print("-" * 60)

            if not self.check_word_exists(keyword):
                print(f"ERROR: '{keyword}' not in vocabulary")
                results.append({
                    'keyword': keyword,
                    'error': 'not_in_vocabulary',
                    'known_synonyms': known_synonyms,
                    'found_synonyms': [],
                    'similarities': {}
                })
                continue

            # Get top 10 most similar words
            similar_words, error = self.find_similar(keyword, topn=10)
            if error:
                print(f"ERROR: {error}")
                continue

            print(f"Top 10 most similar words:")
            for word, score in similar_words:
                marker = " ← KNOWN SYNONYM" if word in known_synonyms else ""
                print(f"  {word:20s} {score:.4f}{marker}")

            # Check which known synonyms were found
            found_similar_words = [word for word, _ in similar_words]
            found_synonyms = [syn for syn in known_synonyms if syn in found_similar_words]
            missed_synonyms = [syn for syn in known_synonyms if syn not in found_similar_words]

            # Get similarities for all known synonyms (even if not in top 10)
            synonym_similarities = {}
            for syn in known_synonyms:
                sim, error = self.get_similarity(keyword, syn)
                if error:
                    synonym_similarities[syn] = {'error': error}
                else:
                    synonym_similarities[syn] = {
                        'similarity': float(sim),
                        'in_top_10': syn in found_similar_words,
                        'rank': found_similar_words.index(syn) + 1 if syn in found_similar_words else None
                    }

            print(f"\nKnown synonyms: {len(known_synonyms)}")
            print(f"Found in top 10: {len(found_synonyms)} / {len(known_synonyms)}")
            if found_synonyms:
                print(f"  Found: {', '.join(found_synonyms)}")
            if missed_synonyms:
                print(f"  Missed: {', '.join(missed_synonyms)}")

            # Check similarities for missed synonyms
            if missed_synonyms:
                print(f"\nSimilarities for missed synonyms:")
                for syn in missed_synonyms:
                    info = synonym_similarities.get(syn, {})
                    if 'error' in info:
                        print(f"  {syn:20s} ERROR: {info['error']}")
                    else:
                        print(f"  {syn:20s} {info['similarity']:.4f} (rank > 10)")

            results.append({
                'keyword': keyword,
                'known_synonyms': known_synonyms,
                'found_synonyms': found_synonyms,
                'missed_synonyms': missed_synonyms,
                'top_10_similar': [(w, float(s)) for w, s in similar_words],
                'synonym_similarities': synonym_similarities,
                'discovery_rate': len(found_synonyms) / len(known_synonyms) if known_synonyms else 0
            })

        return results

    def discover_new_candidates(self, expansion_terms):
        """Test B: Discover new synonym candidates for expansion terms"""
        print("\n" + "="*80)
        print("TEST B: NEW SYNONYM DISCOVERY")
        print("="*80)
        print("\nDiscovering synonym candidates for expansion terms...")

        results = []

        for term in expansion_terms:
            print(f"\n{term.upper()}")
            print("-" * 60)

            # Handle multi-word phrases
            term_token = term.replace(' ', '_')

            if not self.check_word_exists(term_token):
                print(f"ERROR: '{term}' (as '{term_token}') not in vocabulary")
                results.append({
                    'term': term,
                    'error': 'not_in_vocabulary',
                    'candidates': []
                })
                continue

            # Get top 15 most similar words
            similar_words, error = self.find_similar(term_token, topn=15)
            if error:
                print(f"ERROR: {error}")
                continue

            print(f"Top 15 most similar words:")
            for rank, (word, score) in enumerate(similar_words, 1):
                print(f"  {rank:2d}. {word:25s} {score:.4f}")

            # Identify high-similarity candidates (> 0.6)
            high_sim_candidates = [(w, s) for w, s in similar_words if s > 0.6]

            print(f"\nHigh-similarity candidates (score > 0.6): {len(high_sim_candidates)}")
            for word, score in high_sim_candidates:
                print(f"  {word:25s} {score:.4f}")

            results.append({
                'term': term,
                'term_token': term_token,
                'top_15_similar': [(w, float(s)) for w, s in similar_words],
                'high_similarity_candidates': [(w, float(s)) for w, s in high_sim_candidates],
                'num_candidates': len(high_sim_candidates)
            })

        return results

    def verify_corpus_presence(self, corpus_dir, words):
        """Check if discovered words actually appear in Fed statements"""
        print("\n" + "="*80)
        print("CORPUS PRESENCE VERIFICATION")
        print("="*80)
        print("\nChecking if discovered synonyms appear in original corpus...")

        import glob

        # Load all policy statements
        pattern = os.path.join(corpus_dir, "policy_statement_*.txt")
        files = sorted(glob.glob(pattern))

        # Combine all text
        corpus_text = ""
        for filepath in files:
            with open(filepath, 'r', encoding='utf-8') as f:
                corpus_text += " " + f.read().lower()

        # Check each word
        results = []
        for word in words:
            # Remove underscores for multi-word phrases
            original_phrase = word.replace('_', ' ')

            # Check both underscore and space versions
            found_underscore = word in corpus_text
            found_phrase = original_phrase in corpus_text

            found = found_underscore or found_phrase

            results.append({
                'word': word,
                'original_phrase': original_phrase,
                'found': found,
                'found_as': 'phrase' if found_phrase else ('token' if found_underscore else None)
            })

            marker = "✓" if found else "✗"
            print(f"  {marker} {word:30s} {'FOUND' if found else 'NOT FOUND'}")

        return results


def main():
    """Main execution"""
    print("Synonym Discovery Testing with Word2Vec")
    print("=" * 80)

    # Configuration
    model_path = "/mnt/c/python/FedSpeak/prototypes/results/fed_word2vec.model"
    config_path = "/mnt/c/python/FedSpeak/config/config.yaml"
    corpus_dir = "/mnt/c/python/FedSpeak/data/processed"
    output_dir = "/mnt/c/python/FedSpeak/prototypes/results"

    # Check if model exists
    if not os.path.exists(model_path):
        print(f"ERROR: Model not found at {model_path}")
        print("Please run word2vec_training.py first")
        return

    # Initialize tester
    print("\nLoading Word2Vec model...")
    tester = SynonymDiscoveryTester(model_path, config_path)
    print(f"Vocabulary size: {len(tester.wv):,} words")

    # Test A: Known synonyms
    known_synonym_results = tester.test_known_synonyms()

    # Test B: New candidates for expansion terms
    expansion_terms = [
        'symmetric',
        'substantial further progress',
        'substantial_further_progress'  # Try both versions
    ]

    new_candidate_results = tester.discover_new_candidates(expansion_terms)

    # Collect all discovered words for corpus verification
    all_discovered_words = set()

    for result in known_synonym_results:
        if 'top_10_similar' in result:
            for word, _ in result['top_10_similar']:
                all_discovered_words.add(word)

    for result in new_candidate_results:
        if 'high_similarity_candidates' in result:
            for word, _ in result['high_similarity_candidates']:
                all_discovered_words.add(word)

    # Verify corpus presence
    corpus_verification = tester.verify_corpus_presence(
        corpus_dir,
        sorted(all_discovered_words)
    )

    # Calculate overall metrics
    total_known_synonyms = sum(
        len(r['known_synonyms']) for r in known_synonym_results
        if 'known_synonyms' in r
    )
    total_found = sum(
        len(r['found_synonyms']) for r in known_synonym_results
        if 'found_synonyms' in r
    )
    overall_discovery_rate = total_found / total_known_synonyms if total_known_synonyms > 0 else 0

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'model_path': model_path,
        'vocabulary_size': len(tester.wv),
        'test_a_known_synonyms': {
            'results': known_synonym_results,
            'total_known_synonyms': total_known_synonyms,
            'total_found_in_top_10': total_found,
            'overall_discovery_rate': overall_discovery_rate
        },
        'test_b_new_candidates': {
            'expansion_terms': expansion_terms,
            'results': new_candidate_results
        },
        'corpus_verification': corpus_verification
    }

    results_path = os.path.join(output_dir, 'synonym_discovery_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nResults saved to: {results_path}")

    # Summary
    print("\n" + "="*80)
    print("SYNONYM DISCOVERY SUMMARY")
    print("="*80)
    print(f"Known synonyms tested: {total_known_synonyms}")
    print(f"Found in top 10 similar: {total_found}")
    print(f"Discovery rate: {overall_discovery_rate:.1%}")
    print(f"\nExpansion terms tested: {len(expansion_terms)}")
    print(f"Total unique words discovered: {len(all_discovered_words)}")
    print(f"Words verified in corpus: {sum(1 for r in corpus_verification if r['found'])}")

    return results


if __name__ == "__main__":
    main()

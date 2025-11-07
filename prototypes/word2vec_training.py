#!/usr/bin/env python3
"""
Word2Vec Training on Federal Reserve Corpus
============================================

Trains Word2Vec model on FOMC policy statements to learn semantic relationships
specific to Federal Reserve language.

Tests Response 1 claim: "Accommodative" and "supportive" show 0.78-0.85 similarity

Author: Phase 3 Semantic Testing
Date: November 6, 2025
"""

import os
import re
import glob
from datetime import datetime
from gensim.models import Word2Vec
import numpy as np
import json


class FedCorpusLoader:
    """Load and preprocess Federal Reserve policy statements"""

    def __init__(self, corpus_dir):
        self.corpus_dir = corpus_dir

    def load_statements(self):
        """Load all policy statements from directory"""
        pattern = os.path.join(self.corpus_dir, "policy_statement_*.txt")
        files = sorted(glob.glob(pattern))

        statements = []
        for filepath in files:
            # Extract date from filename
            filename = os.path.basename(filepath)
            date_str = filename.replace("policy_statement_", "").replace(".txt", "")

            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()

            statements.append({
                'date': date_str,
                'text': text,
                'filepath': filepath
            })

        return statements

    def preprocess_text(self, text):
        """Preprocess text for Word2Vec training"""
        # Convert to lowercase
        text = text.lower()

        # Handle multi-word phrases as single tokens (Fed-specific)
        multi_word_phrases = [
            'considerable time',
            'full range of tools',
            'substantial further progress',
            'monetary policy',
            'federal reserve',
            'open market',
            'inflation expectations',
            'labor market',
            'price stability',
            'maximum employment',
            'dual mandate',
            'balance sheet',
            'forward guidance'
        ]

        for phrase in multi_word_phrases:
            text = text.replace(phrase, phrase.replace(' ', '_'))

        # Remove non-alphabetic characters except underscores and hyphens
        text = re.sub(r'[^a-z_\-\s]', ' ', text)

        # Split into tokens
        tokens = text.split()

        # Remove very short tokens (likely noise)
        tokens = [t for t in tokens if len(t) > 2]

        return tokens

    def prepare_training_corpus(self):
        """Prepare corpus as list of tokenized documents"""
        statements = self.load_statements()

        corpus = []
        for stmt in statements:
            tokens = self.preprocess_text(stmt['text'])
            corpus.append(tokens)

        print(f"Loaded {len(corpus)} policy statements")

        # Calculate corpus statistics
        total_tokens = sum(len(doc) for doc in corpus)
        unique_tokens = len(set(token for doc in corpus for token in doc))

        print(f"Total tokens: {total_tokens:,}")
        print(f"Unique tokens: {unique_tokens:,}")
        print(f"Average tokens per document: {total_tokens / len(corpus):.1f}")

        return corpus, statements


class Word2VecTrainer:
    """Train and evaluate Word2Vec model on Fed corpus"""

    def __init__(self, corpus, statements):
        self.corpus = corpus
        self.statements = statements
        self.model = None

    def train(self, vector_size=100, window=5, min_count=2, workers=4, epochs=50):
        """
        Train Word2Vec model

        Parameters optimized for small corpus (145 documents):
        - vector_size=100: Smaller than typical (avoids overfitting on small corpus)
        - window=5: Standard context window
        - min_count=2: Include words appearing at least twice
        - epochs=50: More iterations to learn from limited data
        """
        print("\nTraining Word2Vec model...")
        print(f"Parameters: vector_size={vector_size}, window={window}, " +
              f"min_count={min_count}, epochs={epochs}")

        start_time = datetime.now()

        self.model = Word2Vec(
            sentences=self.corpus,
            vector_size=vector_size,
            window=window,
            min_count=min_count,
            workers=workers,
            epochs=epochs,
            sg=0,  # Use CBOW (better for small corpus than Skip-gram)
            negative=5,  # Negative sampling
            seed=42  # Reproducibility
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"Training completed in {duration:.2f} seconds")
        print(f"Vocabulary size: {len(self.model.wv)} words")

        return self.model

    def save_model(self, filepath):
        """Save trained model"""
        self.model.save(filepath)
        print(f"Model saved to: {filepath}")

    def get_vocabulary_stats(self):
        """Get statistics about learned vocabulary"""
        vocab = self.model.wv

        # Get word frequencies
        word_counts = [(word, vocab.get_vecattr(word, "count"))
                      for word in vocab.index_to_key]
        word_counts = sorted(word_counts, key=lambda x: x[1], reverse=True)

        stats = {
            'vocabulary_size': len(vocab),
            'most_frequent_words': word_counts[:20],
            'least_frequent_words': word_counts[-20:],
            'total_word_count': sum(count for _, count in word_counts)
        }

        return stats

    def check_word_exists(self, word):
        """Check if word exists in vocabulary"""
        return word.lower() in self.model.wv

    def get_similarity(self, word1, word2):
        """Get cosine similarity between two words"""
        word1 = word1.lower()
        word2 = word2.lower()

        if not self.check_word_exists(word1):
            return None, f"'{word1}' not in vocabulary"
        if not self.check_word_exists(word2):
            return None, f"'{word2}' not in vocabulary"

        similarity = self.model.wv.similarity(word1, word2)
        return similarity, None

    def find_similar_words(self, word, topn=10):
        """Find most similar words to given word"""
        word = word.lower()

        if not self.check_word_exists(word):
            return None, f"'{word}' not in vocabulary"

        similar = self.model.wv.most_similar(word, topn=topn)
        return similar, None


def test_response_claims(trainer):
    """Test specific claims from model responses"""
    print("\n" + "="*80)
    print("TESTING MODEL RESPONSE CLAIMS")
    print("="*80)

    results = {
        'timestamp': datetime.now().isoformat(),
        'claims_tested': []
    }

    # Claim 1: "Accommodative" and "supportive" show 0.78-0.85 similarity
    print("\nClaim 1: 'accommodative' <-> 'supportive' similarity = 0.78-0.85")
    print("-" * 60)
    sim, error = trainer.get_similarity('accommodative', 'supportive')
    if error:
        print(f"ERROR: {error}")
        results['claims_tested'].append({
            'claim': "accommodative-supportive similarity 0.78-0.85",
            'status': 'error',
            'error': error
        })
    else:
        print(f"Actual similarity: {sim:.4f}")
        in_range = 0.78 <= sim <= 0.85
        print(f"Claim validation: {'✓ PASS' if in_range else '✗ FAIL'}")
        results['claims_tested'].append({
            'claim': "accommodative-supportive similarity 0.78-0.85",
            'status': 'pass' if in_range else 'fail',
            'actual_similarity': float(sim),
            'expected_range': [0.78, 0.85]
        })

    # Claim 2: "Accommodative" and "easy" show 0.68-0.72 similarity
    print("\nClaim 2: 'accommodative' <-> 'easy' similarity = 0.68-0.72")
    print("-" * 60)
    sim, error = trainer.get_similarity('accommodative', 'easy')
    if error:
        print(f"ERROR: {error}")
        results['claims_tested'].append({
            'claim': "accommodative-easy similarity 0.68-0.72",
            'status': 'error',
            'error': error
        })
    else:
        print(f"Actual similarity: {sim:.4f}")
        in_range = 0.68 <= sim <= 0.72
        print(f"Claim validation: {'✓ PASS' if in_range else '✗ FAIL'}")
        results['claims_tested'].append({
            'claim': "accommodative-easy similarity 0.68-0.72",
            'status': 'pass' if in_range else 'fail',
            'actual_similarity': float(sim),
            'expected_range': [0.68, 0.72]
        })

    # Claim 3: "Patient" and "gradual" show 0.76 similarity
    print("\nClaim 3: 'patient' <-> 'gradual' similarity = ~0.76")
    print("-" * 60)
    sim, error = trainer.get_similarity('patient', 'gradual')
    if error:
        print(f"ERROR: {error}")
        results['claims_tested'].append({
            'claim': "patient-gradual similarity ~0.76",
            'status': 'error',
            'error': error
        })
    else:
        print(f"Actual similarity: {sim:.4f}")
        in_range = abs(sim - 0.76) < 0.05  # Within 5% tolerance
        print(f"Claim validation: {'✓ PASS' if in_range else '✗ FAIL'}")
        results['claims_tested'].append({
            'claim': "patient-gradual similarity ~0.76",
            'status': 'pass' if in_range else 'fail',
            'actual_similarity': float(sim),
            'expected_value': 0.76
        })

    return results


def main():
    """Main execution"""
    print("Word2Vec Training on Federal Reserve Corpus")
    print("=" * 80)

    # Configuration
    corpus_dir = "/mnt/c/python/FedSpeak/data/processed"
    output_dir = "/mnt/c/python/FedSpeak/prototypes/results"
    os.makedirs(output_dir, exist_ok=True)

    # Load corpus
    print("\n1. Loading corpus...")
    loader = FedCorpusLoader(corpus_dir)
    corpus, statements = loader.prepare_training_corpus()

    # Train model
    print("\n2. Training Word2Vec model...")
    trainer = Word2VecTrainer(corpus, statements)
    model = trainer.train(
        vector_size=100,
        window=5,
        min_count=2,
        epochs=50
    )

    # Save model
    model_path = os.path.join(output_dir, 'fed_word2vec.model')
    trainer.save_model(model_path)

    # Get vocabulary statistics
    print("\n3. Vocabulary statistics...")
    vocab_stats = trainer.get_vocabulary_stats()
    print(f"Vocabulary size: {vocab_stats['vocabulary_size']:,} words")
    print(f"Total word count: {vocab_stats['total_word_count']:,}")

    print("\nTop 20 most frequent words:")
    for word, count in vocab_stats['most_frequent_words']:
        print(f"  {word:20s} {count:6,d}")

    # Test response claims
    claim_results = test_response_claims(trainer)

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'corpus_statistics': {
            'num_documents': len(statements),
            'total_tokens': sum(len(doc) for doc in corpus),
            'unique_tokens': len(set(token for doc in corpus for token in doc)),
            'vocabulary_size': vocab_stats['vocabulary_size']
        },
        'training_parameters': {
            'vector_size': 100,
            'window': 5,
            'min_count': 2,
            'epochs': 50,
            'algorithm': 'CBOW'
        },
        'model_path': model_path,
        'vocabulary_stats': vocab_stats,
        'claim_validation': claim_results
    }

    results_path = os.path.join(output_dir, 'word2vec_training_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n4. Results saved to: {results_path}")

    # Summary
    print("\n" + "="*80)
    print("TRAINING COMPLETE")
    print("="*80)
    print(f"Corpus: {len(statements)} documents, {vocab_stats['vocabulary_size']:,} words in vocabulary")
    print(f"Model: {model_path}")
    print(f"Results: {results_path}")

    return trainer, results


if __name__ == "__main__":
    trainer, results = main()

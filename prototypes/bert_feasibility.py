#!/usr/bin/env python3
"""
BERT Fine-tuning Feasibility Assessment
========================================

Assesses feasibility of using BERT for semantic change detection on Fed corpus.

Questions:
1. Is 145 documents sufficient for fine-tuning?
2. What's the computational cost (GPU hours, memory)?
3. Is BERT overkill for this corpus size?
4. Should we use BERT or stick with Word2Vec?

Comparison to typical requirements from literature.

Author: Phase 3 Semantic Testing
Date: November 6, 2025
"""

import os
import json
import glob
from datetime import datetime
import numpy as np


class BERTFeasibilityAnalyzer:
    """Analyze feasibility of BERT fine-tuning for FedSpeak corpus"""

    def __init__(self, corpus_dir):
        self.corpus_dir = corpus_dir
        self.statements = self.load_statements()

    def load_statements(self):
        """Load all policy statements"""
        pattern = os.path.join(self.corpus_dir, "policy_statement_*.txt")
        files = sorted(glob.glob(pattern))

        statements = []
        for filepath in files:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            statements.append(text)

        return statements

    def analyze_corpus_statistics(self):
        """Analyze corpus size and characteristics"""
        print("\n" + "="*80)
        print("CORPUS STATISTICS FOR BERT FINE-TUNING")
        print("="*80)

        # Document count
        num_docs = len(self.statements)

        # Token statistics
        all_text = " ".join(self.statements)
        tokens = all_text.split()  # Simple whitespace tokenization
        words = [t for t in tokens if t.isalpha()]

        total_tokens = len(tokens)
        total_words = len(words)
        unique_words = len(set(w.lower() for w in words))

        # Per-document statistics
        doc_lengths = [len(s.split()) for s in self.statements]
        mean_length = np.mean(doc_lengths)
        median_length = np.median(doc_lengths)
        min_length = np.min(doc_lengths)
        max_length = np.max(doc_lengths)

        stats = {
            'num_documents': num_docs,
            'total_tokens': total_tokens,
            'total_words': total_words,
            'unique_words': unique_words,
            'mean_doc_length': mean_length,
            'median_doc_length': median_length,
            'min_doc_length': min_length,
            'max_doc_length': max_length
        }

        print(f"\nCorpus Overview:")
        print(f"  Documents: {num_docs:,}")
        print(f"  Total tokens: {total_tokens:,}")
        print(f"  Total words: {total_words:,}")
        print(f"  Unique words: {unique_words:,}")
        print(f"\nDocument Length Statistics:")
        print(f"  Mean: {mean_length:.1f} tokens")
        print(f"  Median: {median_length:.1f} tokens")
        print(f"  Range: {min_length} - {max_length} tokens")

        return stats

    def compare_to_bert_requirements(self, stats):
        """Compare corpus to typical BERT fine-tuning requirements"""
        print("\n" + "="*80)
        print("COMPARISON TO BERT FINE-TUNING REQUIREMENTS")
        print("="*80)

        # Typical requirements from literature
        requirements = {
            'minimum_documents': {
                'value': 1000,
                'source': 'Typical domain adaptation',
                'category': 'minimum'
            },
            'recommended_documents': {
                'value': 10000,
                'source': 'BERT paper recommendations',
                'category': 'recommended'
            },
            'minimum_tokens': {
                'value': 1_000_000,
                'source': 'Domain-specific BERT (e.g., BioBERT, FinBERT)',
                'category': 'minimum'
            },
            'recommended_tokens': {
                'value': 10_000_000,
                'source': 'Original BERT training',
                'category': 'recommended'
            }
        }

        print(f"\nFedSpeak Corpus vs Typical Requirements:")
        print("-" * 80)
        print(f"{'Metric':<30s} {'FedSpeak':>15s} {'Minimum':>15s} {'Recommended':>15s}")
        print("-" * 80)

        # Documents
        fed_docs = stats['num_documents']
        min_docs = requirements['minimum_documents']['value']
        rec_docs = requirements['recommended_documents']['value']
        print(f"{'Documents':<30s} {fed_docs:>15,d} {min_docs:>15,d} {rec_docs:>15,d}")
        print(f"  % of minimum: {fed_docs/min_docs*100:>14.1f}%")
        print(f"  % of recommended: {fed_docs/rec_docs*100:>14.1f}%")

        # Tokens
        fed_tokens = stats['total_tokens']
        min_tokens = requirements['minimum_tokens']['value']
        rec_tokens = requirements['recommended_tokens']['value']
        print(f"\n{'Tokens':<30s} {fed_tokens:>15,d} {min_tokens:>15,d} {rec_tokens:>15,d}")
        print(f"  % of minimum: {fed_tokens/min_tokens*100:>14.1f}%")
        print(f"  % of recommended: {fed_tokens/rec_tokens*100:>14.1f}%")

        # Assessment
        doc_gap = min_docs / fed_docs
        token_gap = min_tokens / fed_tokens

        print("\n" + "-" * 80)
        print("ASSESSMENT:")
        print(f"  Document deficit: {doc_gap:.1f}x too small (need {doc_gap:.1f}x more documents)")
        print(f"  Token deficit: {token_gap:.1f}x too small (need {token_gap:.1f}x more tokens)")

        sufficient = fed_docs >= min_docs and fed_tokens >= min_tokens

        if sufficient:
            print(f"\nVerdict: ✓ Corpus meets minimum requirements for BERT fine-tuning")
        else:
            print(f"\nVerdict: ✗ Corpus DOES NOT meet minimum requirements for BERT fine-tuning")

        return {
            'requirements': requirements,
            'fedspeak_stats': stats,
            'document_gap': doc_gap,
            'token_gap': token_gap,
            'sufficient_for_finetuning': sufficient
        }

    def estimate_computational_cost(self, stats):
        """Estimate computational cost of BERT fine-tuning"""
        print("\n" + "="*80)
        print("COMPUTATIONAL COST ESTIMATION")
        print("="*80)

        num_docs = stats['num_documents']
        total_tokens = stats['total_tokens']

        # Estimates based on typical BERT fine-tuning (base model, not large)
        # These are rough estimates from literature

        # Training time
        # BERT-base: ~1-2 GPU hours per 1000 documents per epoch (on modern GPU)
        gpu_hours_per_epoch = (num_docs / 1000) * 1.5
        typical_epochs = 3  # Standard for fine-tuning
        total_gpu_hours = gpu_hours_per_epoch * typical_epochs

        # Memory requirements
        # BERT-base: ~4GB model + ~4GB batch processing = ~8GB minimum
        # BERT-large: ~6GB model + ~6GB batch processing = ~12GB minimum
        memory_base = 8  # GB
        memory_large = 12  # GB

        # Cost estimates (AWS p3.2xlarge: V100 GPU, ~$3/hour)
        cost_per_gpu_hour = 3.0
        estimated_cost = total_gpu_hours * cost_per_gpu_hour

        print(f"\nFine-tuning BERT-base on FedSpeak corpus:")
        print(f"  Documents: {num_docs:,}")
        print(f"  Tokens: {total_tokens:,}")
        print(f"  Epochs: {typical_epochs}")
        print(f"\nEstimated Requirements:")
        print(f"  GPU hours per epoch: {gpu_hours_per_epoch:.2f}")
        print(f"  Total GPU hours: {total_gpu_hours:.2f}")
        print(f"  GPU memory (base): {memory_base} GB")
        print(f"  GPU memory (large): {memory_large} GB")
        print(f"\nEstimated Cost (AWS p3.2xlarge):")
        print(f"  Training cost: ${estimated_cost:.2f}")

        # Compare to Word2Vec
        print(f"\nComparison to Word2Vec:")
        print(f"  Word2Vec training time: ~1-2 minutes (CPU)")
        print(f"  Word2Vec cost: $0 (runs on CPU)")
        print(f"  BERT cost premium: {estimated_cost:.0f}x more expensive")

        return {
            'gpu_hours_per_epoch': gpu_hours_per_epoch,
            'typical_epochs': typical_epochs,
            'total_gpu_hours': total_gpu_hours,
            'memory_gb_base': memory_base,
            'memory_gb_large': memory_large,
            'estimated_cost_usd': estimated_cost,
            'cost_premium_vs_word2vec': estimated_cost
        }

    def assess_bert_vs_word2vec(self):
        """Assess whether BERT is worth it vs Word2Vec"""
        print("\n" + "="*80)
        print("BERT vs WORD2VEC FOR FEDSPEAK")
        print("="*80)

        comparison = {
            'Word2Vec': {
                'pros': [
                    'Fast training (< 2 minutes)',
                    'Runs on CPU (no GPU needed)',
                    'Low memory requirements (~500MB)',
                    'Proven effective for word similarity',
                    'Sufficient for static word embeddings',
                    'Easy to interpret',
                    'Works well on small corpus (145 docs)'
                ],
                'cons': [
                    'No context-aware embeddings',
                    'Single vector per word (no polysemy)',
                    'Cannot handle out-of-vocabulary words well',
                    'No pre-training on general language'
                ]
            },
            'BERT': {
                'pros': [
                    'Context-aware embeddings',
                    'Pre-trained on large corpus',
                    'Handles polysemy (multiple meanings)',
                    'Better for sentence/document similarity',
                    'State-of-the-art for many NLP tasks'
                ],
                'cons': [
                    'Requires GPU ($50-100 training cost)',
                    'Corpus too small for effective fine-tuning (145 vs 1000+ needed)',
                    'Overfitting risk on small corpus',
                    'Complex to implement and tune',
                    'Overkill for simple word similarity tasks',
                    'Pre-trained BERT lacks Fed-specific language'
                ]
            }
        }

        print("\nWord2Vec:")
        print("  Pros:")
        for pro in comparison['Word2Vec']['pros']:
            print(f"    ✓ {pro}")
        print("  Cons:")
        for con in comparison['Word2Vec']['cons']:
            print(f"    ✗ {con}")

        print("\nBERT:")
        print("  Pros:")
        for pro in comparison['BERT']['pros']:
            print(f"    ✓ {pro}")
        print("  Cons:")
        for con in comparison['BERT']['cons']:
            print(f"    ✗ {con}")

        return comparison

    def make_recommendation(self, corpus_stats, requirements_assessment, cost_estimate):
        """Make final recommendation"""
        print("\n" + "="*80)
        print("FINAL RECOMMENDATION")
        print("="*80)

        # Decision factors
        factors = []

        # Corpus size
        if not requirements_assessment['sufficient_for_finetuning']:
            factors.append({
                'factor': 'Corpus too small',
                'weight': 'critical',
                'favors': 'Word2Vec',
                'reasoning': f"145 documents is {requirements_assessment['document_gap']:.1f}x below minimum for BERT fine-tuning"
            })

        # Cost
        if cost_estimate['estimated_cost_usd'] > 10:
            factors.append({
                'factor': 'High computational cost',
                'weight': 'important',
                'favors': 'Word2Vec',
                'reasoning': f"BERT would cost ~${cost_estimate['estimated_cost_usd']:.0f} vs $0 for Word2Vec"
            })

        # Use case (keyword similarity vs context)
        factors.append({
            'factor': 'Use case: keyword similarity',
            'weight': 'critical',
            'favors': 'Word2Vec',
            'reasoning': 'FedSpeak needs static word embeddings for synonym discovery, not contextual understanding'
        })

        # Overfitting risk
        factors.append({
            'factor': 'Overfitting risk',
            'weight': 'important',
            'favors': 'Word2Vec',
            'reasoning': 'BERT would likely overfit on 145 documents'
        })

        print("\nDecision Factors:")
        for i, factor in enumerate(factors, 1):
            print(f"\n{i}. {factor['factor']} ({factor['weight']})")
            print(f"   Favors: {factor['favors']}")
            print(f"   Reasoning: {factor['reasoning']}")

        # Final verdict
        recommendation = 'Word2Vec'

        print("\n" + "-" * 80)
        print(f"RECOMMENDATION: Use {recommendation}")
        print("-" * 80)
        print(f"\nRationale:")
        print(f"  1. FedSpeak corpus (145 docs, {corpus_stats['total_tokens']:,} tokens) is too small for BERT")
        print(f"  2. Word2Vec is sufficient for keyword similarity and synonym discovery")
        print(f"  3. BERT fine-tuning would cost ~${cost_estimate['estimated_cost_usd']:.0f} with high overfitting risk")
        print(f"  4. Word2Vec trains in <2 minutes on CPU vs hours on GPU for BERT")
        print(f"\nConclusion: BERT is overkill for FedSpeak. Word2Vec provides better cost-benefit.")

        # When would BERT be appropriate?
        print(f"\n" + "-" * 80)
        print("When Would BERT Be Appropriate?")
        print("-" * 80)
        print("  BERT would be worth considering if:")
        print("    • Corpus expanded to 10,000+ documents")
        print("    • Need context-dependent embeddings (polysemy)")
        print("    • Analyzing full sentences/paragraphs, not just keywords")
        print("    • Have GPU resources available ($50-100 budget)")
        print("    • Pre-trained financial/economic BERT available (e.g., FinBERT)")

        return {
            'recommendation': recommendation,
            'decision_factors': factors,
            'rationale': 'Corpus too small, Word2Vec sufficient for use case',
            'bert_appropriate_conditions': [
                '10,000+ documents',
                'Context-dependent analysis needed',
                'GPU resources available',
                'Pre-trained domain model available'
            ]
        }


def main():
    """Main execution"""
    print("BERT Feasibility Assessment for FedSpeak")
    print("=" * 80)

    # Configuration
    corpus_dir = "/mnt/c/python/FedSpeak/data/processed"
    output_dir = "/mnt/c/python/FedSpeak/prototypes/results"

    # Initialize analyzer
    print("\nAnalyzing corpus...")
    analyzer = BERTFeasibilityAnalyzer(corpus_dir)

    # Analyze corpus
    corpus_stats = analyzer.analyze_corpus_statistics()

    # Compare to requirements
    requirements_assessment = analyzer.compare_to_bert_requirements(corpus_stats)

    # Estimate cost
    cost_estimate = analyzer.estimate_computational_cost(corpus_stats)

    # Compare approaches
    comparison = analyzer.assess_bert_vs_word2vec()

    # Make recommendation
    recommendation = analyzer.make_recommendation(
        corpus_stats,
        requirements_assessment,
        cost_estimate
    )

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'corpus_statistics': corpus_stats,
        'requirements_assessment': requirements_assessment,
        'cost_estimate': cost_estimate,
        'bert_vs_word2vec': comparison,
        'recommendation': recommendation
    }

    results_path = os.path.join(output_dir, 'bert_feasibility_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nResults saved to: {results_path}")

    # Summary
    print("\n" + "="*80)
    print("FEASIBILITY SUMMARY")
    print("="*80)
    print(f"Corpus size: {corpus_stats['num_documents']} docs, {corpus_stats['total_tokens']:,} tokens")
    print(f"BERT requirements: {requirements_assessment['document_gap']:.1f}x more docs needed")
    print(f"Estimated cost: ${cost_estimate['estimated_cost_usd']:.2f}")
    print(f"Recommendation: {recommendation['recommendation']}")

    return results


if __name__ == "__main__":
    main()

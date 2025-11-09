"""Sentiment analysis for media coverage using FinBERT.

This module provides finance-specific sentiment analysis using FinBERT,
a BERT model pre-trained on financial text and fine-tuned for sentiment
classification.

It also implements hybrid sentiment scoring combining GDELT tone scores
with FinBERT predictions for improved accuracy.

Model: yiyanghkust/finbert-tone
Paper: https://arxiv.org/abs/1908.10063
"""

import logging
from typing import Dict, List, Optional, Union

import torch
from transformers import BertTokenizer, BertForSequenceClassification, pipeline

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """FinBERT-based sentiment analyzer for financial news.

    Uses the yiyanghkust/finbert-tone model for finance-specific sentiment
    classification. Supports single-text and batch processing.

    Sentiment Labels:
    - positive: Optimistic/favorable outlook
    - neutral: Balanced/factual reporting
    - negative: Pessimistic/concerning outlook

    Scores: 0-1 confidence for predicted label
    """

    # FinBERT model (finance-tuned BERT)
    MODEL_NAME = "yiyanghkust/finbert-tone"

    # Sentiment label mapping
    LABEL_SCORES = {
        'positive': 1.0,
        'neutral': 0.0,
        'negative': -1.0
    }

    def __init__(self,
                 model_name: Optional[str] = None,
                 device: str = "cpu",
                 batch_size: int = 8):
        """Initialize FinBERT sentiment analyzer.

        Args:
            model_name: HuggingFace model name (default: yiyanghkust/finbert-tone)
            device: Device for inference ('cpu' or 'cuda')
            batch_size: Batch size for processing (default: 8)

        Raises:
            ImportError: If transformers or torch not installed
            RuntimeError: If model loading fails
        """
        self.model_name = model_name or self.MODEL_NAME
        self.device = device
        self.batch_size = batch_size

        logger.info(f"Loading FinBERT model: {self.model_name} (device={device})")

        try:
            # Load model and tokenizer
            self.model = BertForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=3  # positive, neutral, negative
            )

            self.tokenizer = BertTokenizer.from_pretrained(self.model_name)

            # Create pipeline for easy inference
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if device == "cuda" else -1,  # -1 = CPU
                batch_size=self.batch_size
            )

            logger.info("FinBERT model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e}")
            raise RuntimeError(f"FinBERT initialization failed: {e}")

    def analyze(self, text: str) -> Dict:
        """Analyze sentiment of a single text.

        Args:
            text: Text to analyze (article title, headline, snippet)

        Returns:
            Dictionary with:
            - label: Sentiment label (positive/neutral/negative)
            - score: Confidence score (0-1)
            - sentiment_score: Normalized score (-1 to +1)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for sentiment analysis")
            return {
                'label': 'neutral',
                'score': 0.0,
                'sentiment_score': 0.0
            }

        try:
            # Run inference
            result = self.pipeline(text[:512])[0]  # Limit to 512 tokens

            # Convert to standardized format
            label = result['label'].lower()
            confidence = result['score']
            sentiment_score = self.LABEL_SCORES.get(label, 0.0) * confidence

            return {
                'label': label,
                'score': confidence,
                'sentiment_score': sentiment_score
            }

        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                'label': 'neutral',
                'score': 0.0,
                'sentiment_score': 0.0,
                'error': str(e)
            }

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze sentiment of multiple texts efficiently.

        Args:
            texts: List of texts to analyze

        Returns:
            List of sentiment dictionaries (same format as analyze())
        """
        if not texts:
            return []

        # Filter empty texts
        valid_texts = [t[:512] if t and t.strip() else "" for t in texts]

        try:
            # Batch inference
            results = self.pipeline(valid_texts)

            # Convert to standardized format
            analyzed = []
            for result, original_text in zip(results, texts):
                if not original_text or not original_text.strip():
                    analyzed.append({
                        'label': 'neutral',
                        'score': 0.0,
                        'sentiment_score': 0.0
                    })
                else:
                    label = result['label'].lower()
                    confidence = result['score']
                    sentiment_score = self.LABEL_SCORES.get(label, 0.0) * confidence

                    analyzed.append({
                        'label': label,
                        'score': confidence,
                        'sentiment_score': sentiment_score
                    })

            return analyzed

        except Exception as e:
            logger.error(f"Batch sentiment analysis error: {e}")

            # Return neutral results for all texts
            return [
                {'label': 'neutral', 'score': 0.0, 'sentiment_score': 0.0, 'error': str(e)}
                for _ in texts
            ]

    def calculate_avg_sentiment(self, sentiment_results: List[Dict]) -> float:
        """Calculate average sentiment score from multiple results.

        Args:
            sentiment_results: List of sentiment dictionaries

        Returns:
            Average sentiment score (-1 to +1 scale)
        """
        if not sentiment_results:
            return 0.0

        scores = [r.get('sentiment_score', 0.0) for r in sentiment_results]

        if not scores:
            return 0.0

        return sum(scores) / len(scores)


class HybridSentimentScorer:
    """Hybrid sentiment scoring combining GDELT tone and FinBERT.

    Combines two sentiment signals:
    1. GDELT tone scores (-100 to +100 scale)
    2. FinBERT sentiment (-1 to +1 scale)

    Weights can be adjusted based on empirical performance.
    """

    def __init__(self,
                 finbert_analyzer: Optional[SentimentAnalyzer] = None,
                 gdelt_weight: float = 0.4,
                 finbert_weight: float = 0.6):
        """Initialize hybrid sentiment scorer.

        Args:
            finbert_analyzer: FinBERT analyzer instance (creates new if None)
            gdelt_weight: Weight for GDELT tone (default: 0.4)
            finbert_weight: Weight for FinBERT sentiment (default: 0.6)

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        if abs(gdelt_weight + finbert_weight - 1.0) > 0.01:
            raise ValueError(
                f"Weights must sum to 1.0 (got {gdelt_weight + finbert_weight})"
            )

        self.finbert = finbert_analyzer or SentimentAnalyzer()
        self.gdelt_weight = gdelt_weight
        self.finbert_weight = finbert_weight

        logger.info(
            f"Hybrid sentiment scorer initialized "
            f"(GDELT={gdelt_weight}, FinBERT={finbert_weight})"
        )

    def score_articles(self, articles: List[Dict]) -> Dict:
        """Score sentiment for a list of articles using hybrid approach.

        Args:
            articles: List of article dictionaries from GDELT
                     Each must have 'title' and 'tone' fields

        Returns:
            Dictionary with:
            - gdelt_tone_avg: Average GDELT tone (-100 to +100)
            - finbert_sentiment_avg: Average FinBERT sentiment (-1 to +1)
            - hybrid_score: Weighted combination (-1 to +1)
            - article_count: Number of articles analyzed
            - finbert_results: List of FinBERT results per article
        """
        if not articles:
            return {
                'gdelt_tone_avg': 0.0,
                'finbert_sentiment_avg': 0.0,
                'hybrid_score': 0.0,
                'article_count': 0,
                'finbert_results': []
            }

        # Extract GDELT tone scores
        gdelt_tones = []
        for article in articles:
            tone = article.get('tone')
            if tone is not None:
                try:
                    gdelt_tones.append(float(tone))
                except (ValueError, TypeError):
                    pass

        gdelt_tone_avg = sum(gdelt_tones) / len(gdelt_tones) if gdelt_tones else 0.0

        # Extract article titles for FinBERT
        titles = [article.get('title', '') for article in articles]

        # Run FinBERT sentiment analysis (batch)
        finbert_results = self.finbert.analyze_batch(titles)
        finbert_sentiment_avg = self.finbert.calculate_avg_sentiment(finbert_results)

        # Calculate hybrid score
        # Normalize GDELT tone to -1 to +1 scale (divide by 100)
        gdelt_normalized = gdelt_tone_avg / 100.0

        hybrid_score = (
            self.gdelt_weight * gdelt_normalized +
            self.finbert_weight * finbert_sentiment_avg
        )

        return {
            'gdelt_tone_avg': round(gdelt_tone_avg, 2),
            'finbert_sentiment_avg': round(finbert_sentiment_avg, 4),
            'hybrid_score': round(hybrid_score, 4),
            'article_count': len(articles),
            'finbert_results': finbert_results
        }

    def score_top_articles(self, articles: List[Dict], top_n: int = 20) -> Dict:
        """Score sentiment for top N articles only (efficiency optimization).

        Args:
            articles: List of article dictionaries from GDELT
            top_n: Number of top articles to analyze (default: 20)

        Returns:
            Same format as score_articles()
        """
        if len(articles) <= top_n:
            return self.score_articles(articles)

        # Use GDELT tone to select top N most prominent articles
        # (Higher absolute tone = more prominent coverage)
        def article_prominence(article: Dict) -> float:
            tone = article.get('tone')
            if tone is not None:
                try:
                    return abs(float(tone))
                except (ValueError, TypeError):
                    pass
            return 0.0

        sorted_articles = sorted(
            articles,
            key=article_prominence,
            reverse=True
        )

        top_articles = sorted_articles[:top_n]

        logger.debug(
            f"Scoring top {top_n} articles (out of {len(articles)} total)"
        )

        return self.score_articles(top_articles)

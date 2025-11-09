"""MILA: Monetary Insight via LLM Analysis

This module provides LLM-based stance analysis for Federal Reserve policy statements,
classifying monetary policy stance as hawkish, dovish, or neutral using Claude 3.5 Sonnet.

MILA analyzes FOMC statements to determine:
- Overall policy stance (hawkish/dovish/neutral)
- Confidence in classification
- Numeric score (-1.0 dovish to +1.0 hawkish)
- Explanation of the classification
- Key phrases supporting the analysis

The system uses aggressive caching to minimize API costs and provides comprehensive
cost tracking for budget management.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Union
from pathlib import Path

import anthropic

from src.config.settings import Settings

logger = logging.getLogger(__name__)


class MILAAnalyzer:
    """LLM-based stance analyzer for Federal Reserve policy statements.

    Uses Claude 3.5 Sonnet to classify monetary policy stance with
    structured output and comprehensive cost tracking.

    Stance Classifications:
    - hawkish: Favors tighter monetary policy (rate increases, reducing accommodation)
    - dovish: Favors looser monetary policy (rate cuts, maintaining accommodation)
    - neutral: Balanced or data-dependent stance

    Scores: -1.0 (most dovish) to +1.0 (most hawkish)
    Confidence: 0.0 (low) to 1.0 (high)
    """

    # Default model and configuration
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    DEFAULT_MAX_TOKENS = 2048
    DEFAULT_TEMPERATURE = 0.1  # Low temperature for consistency

    # Singleton instance
    _instance = None
    _client = None
    _cache = None
    _cost_tracker = None

    def __new__(cls, api_key: Optional[str] = None, model: Optional[str] = None,
                cache_dir: Optional[str] = None):
        """Singleton pattern to ensure only one analyzer instance."""
        if cls._instance is None:
            cls._instance = super(MILAAnalyzer, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None,
                 cache_dir: Optional[str] = None):
        """Initialize MILA analyzer.

        Args:
            api_key: Anthropic API key (default: from env ANTHROPIC_API_KEY)
            model: Claude model to use (default: claude-3-5-sonnet-20241022)
            cache_dir: Directory for caching results (default: data/mila_cache)

        Raises:
            ValueError: If API key is not provided and not in environment
        """
        # Only initialize once
        if MILAAnalyzer._client is not None:
            return

        # Load settings
        settings = Settings()

        # Get API key
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            # Try from config
            self.api_key = settings.get('explainability.mila.api_key')

        if not self.api_key:
            logger.warning(
                "ANTHROPIC_API_KEY not found in environment or config. "
                "MILA will be disabled. Set ANTHROPIC_API_KEY to enable."
            )
            MILAAnalyzer._client = None
            return

        # Model configuration
        self.model = model or settings.get(
            'explainability.mila.model',
            default=self.DEFAULT_MODEL
        )
        self.max_tokens = settings.get(
            'explainability.mila.max_tokens',
            default=self.DEFAULT_MAX_TOKENS
        )
        self.temperature = settings.get(
            'explainability.mila.temperature',
            default=self.DEFAULT_TEMPERATURE
        )

        # Initialize Anthropic client
        try:
            MILAAnalyzer._client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"MILA initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            MILAAnalyzer._client = None
            return

        # Initialize cache (lazy import to avoid circular dependency)
        try:
            from src.explainability.mila_cache import MILAStanceCache
            cache_directory = cache_dir or settings.get(
                'explainability.mila.cache_dir',
                default='data/mila_cache'
            )
            MILAAnalyzer._cache = MILAStanceCache(cache_dir=cache_directory)
            logger.info(f"MILA cache initialized at {cache_directory}")
        except Exception as e:
            logger.warning(f"MILA cache initialization failed: {e}")
            MILAAnalyzer._cache = None

        # Initialize cost tracker
        try:
            from src.explainability.cost_tracker import CostTracker
            MILAAnalyzer._cost_tracker = CostTracker()
            logger.info("MILA cost tracker initialized")
        except Exception as e:
            logger.warning(f"Cost tracker initialization failed: {e}")
            MILAAnalyzer._cost_tracker = None

    @property
    def client(self):
        """Get Anthropic client."""
        return MILAAnalyzer._client

    @property
    def cache(self):
        """Get cache instance."""
        return MILAAnalyzer._cache

    @property
    def cost_tracker(self):
        """Get cost tracker instance."""
        return MILAAnalyzer._cost_tracker

    def is_enabled(self) -> bool:
        """Check if MILA is enabled (API key configured)."""
        return self.client is not None

    def analyze_stance(self, statement_text: str, date: str,
                      doc_type: str = 'policy_statement') -> Dict:
        """Analyze hawkish/dovish stance of FOMC statement.

        Args:
            statement_text: Full text of FOMC statement
            date: Statement date (YYYYMMDD format)
            doc_type: Document type (policy_statement, minutes, etc.)

        Returns:
            {
                'success': bool,
                'stance': 'hawkish' | 'dovish' | 'neutral',
                'score': float (-1.0 to +1.0),
                'confidence': float (0.0 to 1.0),
                'explanation': str,
                'key_phrases': List[str],
                'cached': bool,
                'error': Optional[str]
            }

        Raises:
            ValueError: If MILA is not enabled (no API key)
        """
        if not self.is_enabled():
            return {
                'success': False,
                'stance': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'explanation': 'MILA is not enabled (missing API key)',
                'key_phrases': [],
                'cached': False,
                'error': 'MILA_DISABLED'
            }

        # Check cache first
        if self.cache:
            cached_result = self.cache.get_stance(date, doc_type)
            if cached_result:
                logger.debug(f"Cache hit for {date} ({doc_type})")
                return {**cached_result, 'cached': True, 'success': True, 'error': None}

        # Build prompt
        prompt = self._build_stance_prompt(statement_text, date)

        try:
            # Call Claude API
            logger.info(f"Analyzing stance for {date} ({doc_type})")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Track cost
            if self.cost_tracker and hasattr(response, 'usage'):
                self.cost_tracker.track_request(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    model=self.model
                )

            # Parse response
            result = self._parse_response(response)

            # Cache result
            if self.cache and result['success']:
                self.cache.save_stance(date, doc_type, result)
                logger.debug(f"Cached stance for {date} ({doc_type})")

            return {**result, 'cached': False}

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error for {date}: {e}")
            return {
                'success': False,
                'stance': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'explanation': f'API error: {str(e)}',
                'key_phrases': [],
                'cached': False,
                'error': 'API_ERROR'
            }
        except Exception as e:
            logger.error(f"Unexpected error analyzing stance for {date}: {e}")
            return {
                'success': False,
                'stance': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'explanation': f'Analysis failed: {str(e)}',
                'key_phrases': [],
                'cached': False,
                'error': 'ANALYSIS_FAILED'
            }

    def _build_stance_prompt(self, statement_text: str, date: str) -> str:
        """Build prompt for stance analysis.

        Args:
            statement_text: Full FOMC statement text
            date: Statement date (for context)

        Returns:
            Formatted prompt string
        """
        return f"""Analyze the Federal Reserve's monetary policy stance in this FOMC statement from {date}.

STATEMENT:
{statement_text}

TASK:
Classify the statement's overall stance as:
- HAWKISH: Favors tighter monetary policy (rate increases, reducing accommodation, concerns about inflation)
- DOVISH: Favors looser monetary policy (rate cuts, maintaining accommodation, concerns about employment/growth)
- NEUTRAL: Balanced or data-dependent stance

Provide:
1. Overall stance (hawkish/dovish/neutral)
2. Confidence score (0.0-1.0) - how certain are you?
3. Numeric score (-1.0 = most dovish, 0.0 = neutral, +1.0 = most hawkish)
4. 2-3 sentence explanation of why you classified it this way
5. 3-5 key phrases from the statement supporting your analysis (exact quotes)

Return ONLY valid JSON in this exact format:
{{
    "stance": "hawkish",
    "score": 0.75,
    "confidence": 0.90,
    "explanation": "The statement signals a clear tightening stance with emphasis on inflation control and discussion of reducing accommodation. The committee's focus on price stability and willingness to raise rates demonstrates a hawkish posture.",
    "key_phrases": ["reduce inflation to 2 percent", "ongoing increases in the target range", "inflation remains elevated", "additional policy firming", "price stability"]
}}

Remember:
- Score range: -1.0 (most dovish) to +1.0 (most hawkish)
- Confidence range: 0.0 (uncertain) to 1.0 (very certain)
- Use exact quotes for key_phrases
- Return ONLY the JSON, no additional text"""

    def _parse_response(self, response) -> Dict:
        """Parse Claude API response into structured result.

        Args:
            response: Anthropic API response object

        Returns:
            Parsed stance analysis result

        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Extract text from response
            if not response.content or len(response.content) == 0:
                raise ValueError("Empty response from Claude API")

            response_text = response.content[0].text.strip()

            # Parse JSON
            # Sometimes Claude adds markdown code blocks, remove them
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove ```

            response_text = response_text.strip()

            data = json.loads(response_text)

            # Validate required fields
            required_fields = ['stance', 'score', 'confidence', 'explanation', 'key_phrases']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate stance value
            if data['stance'] not in ['hawkish', 'dovish', 'neutral']:
                raise ValueError(f"Invalid stance: {data['stance']}")

            # Validate score range
            if not -1.0 <= data['score'] <= 1.0:
                logger.warning(f"Score {data['score']} out of range, clipping to [-1, 1]")
                data['score'] = max(-1.0, min(1.0, data['score']))

            # Validate confidence range
            if not 0.0 <= data['confidence'] <= 1.0:
                logger.warning(f"Confidence {data['confidence']} out of range, clipping to [0, 1]")
                data['confidence'] = max(0.0, min(1.0, data['confidence']))

            # Ensure key_phrases is a list
            if not isinstance(data['key_phrases'], list):
                data['key_phrases'] = [str(data['key_phrases'])]

            return {
                'success': True,
                'stance': data['stance'],
                'score': float(data['score']),
                'confidence': float(data['confidence']),
                'explanation': str(data['explanation']),
                'key_phrases': [str(p) for p in data['key_phrases']],
                'error': None
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            raise ValueError(f"Invalid JSON in response: {e}")
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            raise

    def get_cost_summary(self) -> Dict:
        """Get cost tracking summary.

        Returns:
            {
                'total_requests': int,
                'total_cost': float,
                'cost_this_month': float,
                'cache_hit_rate': float,
                ...
            }
        """
        if not self.cost_tracker:
            return {
                'total_requests': 0,
                'total_cost': 0.0,
                'cost_this_month': 0.0,
                'cache_hit_rate': 0.0,
                'enabled': False
            }

        summary = self.cost_tracker.get_summary()

        # Add cache stats if available
        if self.cache:
            cache_stats = self.cache.get_stats()
            summary['cache_hit_rate'] = cache_stats.get('hit_rate', 0.0)
            summary['cached_analyses'] = cache_stats.get('total_entries', 0)

        return summary

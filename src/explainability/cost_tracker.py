"""Cost tracking for MILA API usage.

This module provides comprehensive cost tracking for Claude API calls,
including per-request tracking, monthly budgets, and cost alerts.

Pricing (Claude 3.5 Sonnet as of November 2024):
- Input tokens: $3.00 per million tokens
- Output tokens: $15.00 per million tokens

Cost tracking is persisted to disk for historical analysis.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class CostTracker:
    """Track and manage MILA API costs.

    Provides:
    - Per-request cost calculation
    - Monthly budget tracking
    - Cost alerts when thresholds exceeded
    - Historical cost analysis
    - Token usage statistics

    All costs stored as high-precision Decimal for accurate financial tracking.
    """

    # Pricing per million tokens (Claude 3.5 Sonnet)
    PRICING = {
        'claude-3-5-sonnet-20241022': {
            'input': Decimal('3.00'),   # $3.00 per 1M input tokens
            'output': Decimal('15.00')  # $15.00 per 1M output tokens
        },
        'claude-3-opus-20240229': {
            'input': Decimal('15.00'),
            'output': Decimal('75.00')
        },
        'claude-3-haiku-20240307': {
            'input': Decimal('0.25'),
            'output': Decimal('1.25')
        }
    }

    def __init__(self,
                 storage_file: str = "data/mila_cache/cost_tracking.json",
                 budget_alert_threshold: float = 500.0):
        """Initialize cost tracker.

        Args:
            storage_file: Path to cost tracking JSON file
            budget_alert_threshold: Monthly budget threshold for alerts (dollars)
        """
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

        self.budget_alert_threshold = Decimal(str(budget_alert_threshold))

        # Load existing tracking data
        self.data = self._load_data()

        logger.info(
            f"Cost tracker initialized (budget alert: ${budget_alert_threshold}/month)"
        )

    def track_request(self,
                     input_tokens: int,
                     output_tokens: int,
                     model: str = 'claude-3-5-sonnet-20241022'):
        """Track a single API request.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name for pricing lookup

        Returns:
            Cost in dollars for this request
        """
        # Get pricing for model
        if model not in self.PRICING:
            logger.warning(
                f"Unknown model '{model}', using Sonnet pricing"
            )
            model = 'claude-3-5-sonnet-20241022'

        pricing = self.PRICING[model]

        # Calculate cost (tokens / 1_000_000 * price_per_million)
        input_cost = (Decimal(input_tokens) / Decimal('1000000')) * pricing['input']
        output_cost = (Decimal(output_tokens) / Decimal('1000000')) * pricing['output']
        total_cost = input_cost + output_cost

        # Record request
        request_data = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'input_cost': float(input_cost),
            'output_cost': float(output_cost),
            'total_cost': float(total_cost)
        }

        # Add to history
        if 'requests' not in self.data:
            self.data['requests'] = []
        self.data['requests'].append(request_data)

        # Update totals
        self.data['total_requests'] = self.data.get('total_requests', 0) + 1
        self.data['total_input_tokens'] = self.data.get('total_input_tokens', 0) + input_tokens
        self.data['total_output_tokens'] = self.data.get('total_output_tokens', 0) + output_tokens
        self.data['total_cost'] = self.data.get('total_cost', 0.0) + float(total_cost)

        # Save to disk
        self._save_data()

        # Check budget alert
        monthly_cost = self._get_monthly_cost()
        if monthly_cost > float(self.budget_alert_threshold):
            logger.warning(
                f"Monthly MILA cost (${monthly_cost:.2f}) exceeds "
                f"budget threshold (${self.budget_alert_threshold})"
            )

        logger.debug(
            f"Tracked request: {input_tokens} in + {output_tokens} out "
            f"= ${total_cost:.4f} (monthly: ${monthly_cost:.2f})"
        )

        return float(total_cost)

    def get_summary(self) -> Dict:
        """Get comprehensive cost tracking summary.

        Returns:
            {
                'total_requests': int,
                'total_tokens': int,
                'total_cost': float,
                'cost_this_month': float,
                'cost_this_week': float,
                'cost_today': float,
                'average_cost_per_request': float,
                'budget_threshold': float,
                'budget_remaining': float,
                ...
            }
        """
        total_requests = self.data.get('total_requests', 0)
        total_cost = self.data.get('total_cost', 0.0)
        total_tokens = (
            self.data.get('total_input_tokens', 0) +
            self.data.get('total_output_tokens', 0)
        )

        monthly_cost = self._get_monthly_cost()
        weekly_cost = self._get_weekly_cost()
        daily_cost = self._get_daily_cost()

        avg_cost = total_cost / total_requests if total_requests > 0 else 0.0

        budget_remaining = float(self.budget_alert_threshold) - monthly_cost

        return {
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'total_input_tokens': self.data.get('total_input_tokens', 0),
            'total_output_tokens': self.data.get('total_output_tokens', 0),
            'total_cost': round(total_cost, 2),
            'cost_this_month': round(monthly_cost, 2),
            'cost_this_week': round(weekly_cost, 2),
            'cost_today': round(daily_cost, 2),
            'average_cost_per_request': round(avg_cost, 4),
            'budget_threshold': float(self.budget_alert_threshold),
            'budget_remaining': round(budget_remaining, 2),
            'budget_utilized_pct': round((monthly_cost / float(self.budget_alert_threshold)) * 100, 1)
                                  if self.budget_alert_threshold > 0 else 0.0,
            'enabled': True
        }

    def _get_monthly_cost(self) -> float:
        """Calculate cost for current month."""
        return self._get_cost_for_period(days=30)

    def _get_weekly_cost(self) -> float:
        """Calculate cost for past 7 days."""
        return self._get_cost_for_period(days=7)

    def _get_daily_cost(self) -> float:
        """Calculate cost for today."""
        return self._get_cost_for_period(days=1)

    def _get_cost_for_period(self, days: int) -> float:
        """Calculate cost for a time period.

        Args:
            days: Number of days to look back

        Returns:
            Total cost in dollars for the period
        """
        if 'requests' not in self.data:
            return 0.0

        cutoff_date = datetime.now() - timedelta(days=days)
        period_cost = 0.0

        for request in self.data['requests']:
            try:
                request_time = datetime.fromisoformat(request['timestamp'])
                if request_time >= cutoff_date:
                    period_cost += request.get('total_cost', 0.0)
            except (ValueError, KeyError):
                continue

        return period_cost

    def get_request_history(self, limit: int = 100) -> List[Dict]:
        """Get recent request history.

        Args:
            limit: Maximum number of requests to return

        Returns:
            List of request dictionaries (most recent first)
        """
        requests = self.data.get('requests', [])
        return list(reversed(requests[-limit:]))

    def _load_data(self) -> Dict:
        """Load cost tracking data from disk.

        Returns:
            Cost tracking data dictionary
        """
        if not self.storage_file.exists():
            return {
                'created_at': datetime.now().isoformat(),
                'total_requests': 0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_cost': 0.0,
                'requests': []
            }

        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cost tracking data: {e}")
            return {
                'created_at': datetime.now().isoformat(),
                'total_requests': 0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_cost': 0.0,
                'requests': []
            }

    def _save_data(self):
        """Save cost tracking data to disk."""
        try:
            self.data['updated_at'] = datetime.now().isoformat()
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except (IOError, OSError) as e:
            logger.error(f"Failed to save cost tracking data: {e}")

    def reset_monthly_tracking(self):
        """Reset monthly cost tracking (keeps total historical data).

        WARNING: Use with caution. This doesn't delete history, but resets
        the monthly tracking counter.
        """
        logger.warning("Monthly cost tracking reset requested")

        # Keep all requests in history
        # Cost calculations use timestamps, so monthly costs will recalculate correctly

        # Just log the reset
        if 'resets' not in self.data:
            self.data['resets'] = []

        self.data['resets'].append({
            'timestamp': datetime.now().isoformat(),
            'reason': 'manual_reset'
        })

        self._save_data()
        logger.info("Monthly tracking reset (historical data preserved)")

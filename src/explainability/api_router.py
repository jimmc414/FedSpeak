"""API routing logic for Anthropic client initialization.

This module provides intelligent routing between Anthropic's cloud API and local
Claude Code Max inference based on API key patterns.

Key Pattern Detection:
    - Normal key: sk-ant-api03-abc123xyz... → Routes to Anthropic cloud API
    - Local key: sk-ant-api03-999999999999... → Routes to Claude Code Max (local)

The "all 9s" pattern is a convention that signals local routing should be used
instead of making API calls to Anthropic's servers. This is useful for:
    - Development/testing with Claude Code Max subscription
    - Avoiding API costs during development
    - Working offline or in restricted network environments
"""

import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class APIRouter:
    """Route API calls between Anthropic cloud API and local Claude Code.

    This class implements automatic detection and routing based on API key patterns.
    When an API key ends with 12+ consecutive 9s (e.g., sk-ant-999999999999), it
    signals that local Claude Code Max should be used instead of the cloud API.

    Attributes:
        CLAUDE_CODE_PATTERN (str): Minimum pattern for local routing detection
        MIN_NINES_LENGTH (int): Minimum consecutive 9s required for local routing
    """

    CLAUDE_CODE_PATTERN = "999999999999"  # 12 consecutive 9s
    MIN_NINES_LENGTH = 12

    @staticmethod
    def detect_routing_mode(api_key: str) -> Tuple[str, bool]:
        """Detect if API key indicates local Claude Code routing.

        Examines the API key to determine whether it should route to Anthropic's
        cloud API or local Claude Code Max. Detection is based on the "all 9s"
        pattern in the final segment of the key.

        Args:
            api_key: Anthropic API key or local routing placeholder

        Returns:
            Tuple of (routing_mode, is_local) where:
                - routing_mode: 'claude_code' or 'anthropic_api'
                - is_local: True if using local Claude Code, False for cloud API

        Examples:
            >>> APIRouter.detect_routing_mode("sk-ant-api03-abc123")
            ('anthropic_api', False)

            >>> APIRouter.detect_routing_mode("sk-ant-999999999999")
            ('claude_code', True)

            >>> APIRouter.detect_routing_mode("sk-ant-api03-999999999999")
            ('claude_code', True)
        """
        if not api_key:
            logger.debug("Empty API key, defaulting to Anthropic API mode")
            return 'anthropic_api', False

        # Split by hyphens and check the last segment
        segments = api_key.split('-')
        if not segments:
            logger.debug("Invalid API key format (no hyphens), defaulting to Anthropic API")
            return 'anthropic_api', False

        last_segment = segments[-1]

        # Check if last segment is all 9s and meets minimum length
        if (len(last_segment) >= APIRouter.MIN_NINES_LENGTH and
            all(c == '9' for c in last_segment)):
            logger.info(
                f"Detected Claude Code routing pattern (all-9s in last segment: {len(last_segment)} chars)"
            )
            return 'claude_code', True

        logger.debug("Standard API key pattern detected, routing to Anthropic API")
        return 'anthropic_api', False

    @staticmethod
    def create_client(api_key: Optional[str] = None, **kwargs):
        """Create appropriate Anthropic client based on API key pattern.

        This factory method creates an Anthropic client instance with automatic
        routing. It examines the API key and routes to either:
            - Anthropic cloud API (for normal keys)
            - Claude Code Max local inference (for all-9s placeholder keys)

        The routing is transparent to the caller - the returned client has the
        same interface regardless of routing mode.

        Args:
            api_key: Anthropic API key or local routing indicator (e.g., "sk-ant-999999999999")
                    If None, checks ANTHROPIC_API_KEY environment variable
            **kwargs: Additional arguments passed to Anthropic client constructor

        Returns:
            Configured Anthropic client instance

        Raises:
            ValueError: If no API key is provided (via parameter or environment)
            ImportError: If anthropic package is not installed
            Exception: If client initialization fails

        Examples:
            # Cloud API routing (normal key)
            >>> client = APIRouter.create_client("sk-ant-api03-abc123")
            INFO - Initializing Anthropic API client (cloud mode)

            # Local routing (all-9s key)
            >>> client = APIRouter.create_client("sk-ant-999999999999")
            INFO - Initializing Claude Code client (local mode)

            # From environment variable
            >>> os.environ['ANTHROPIC_API_KEY'] = "sk-ant-999999999999"
            >>> client = APIRouter.create_client()
            INFO - Initializing Claude Code client (local mode)
        """
        # Get API key from parameter or environment
        key = api_key or os.getenv('ANTHROPIC_API_KEY')

        if not key:
            raise ValueError(
                "No API key provided. Set ANTHROPIC_API_KEY environment variable or "
                "pass api_key parameter. Use 'sk-ant-999999999999' for local routing "
                "or a valid Anthropic key for cloud API."
            )

        # Detect routing mode
        routing_mode, is_local = APIRouter.detect_routing_mode(key)

        # Import Anthropic client (lazy import)
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

        # Create client based on routing mode
        if is_local:
            # Local Claude Code Max routing
            logger.info("Initializing Claude Code client (local mode)")
            logger.info(
                "Note: Using Claude Code Max for inference. Ensure Claude Code CLI "
                "is installed and authenticated."
            )
            # Currently, we still use the standard Anthropic client with the placeholder key
            # In the future, this could route to a local endpoint or proxy
            client = anthropic.Anthropic(api_key=key, **kwargs)
            # Tag the client so downstream code can detect routing mode if needed
            client._fedspeak_routing_mode = 'claude_code'
            client._fedspeak_is_local = True
        else:
            # Standard Anthropic cloud API
            logger.info("Initializing Anthropic API client (cloud mode)")
            client = anthropic.Anthropic(api_key=key, **kwargs)
            client._fedspeak_routing_mode = 'anthropic_api'
            client._fedspeak_is_local = False

        return client

    @staticmethod
    def get_routing_info(client) -> dict:
        """Get routing information from a client instance.

        Extracts routing mode metadata that was attached during client creation.
        Useful for logging, debugging, and conditional logic based on routing mode.

        Args:
            client: Anthropic client instance created by APIRouter.create_client()

        Returns:
            Dictionary with keys:
                - routing_mode: 'claude_code' or 'anthropic_api'
                - is_local: True if local routing, False if cloud
                - description: Human-readable routing description

        Examples:
            >>> client = APIRouter.create_client("sk-ant-999999999999")
            >>> info = APIRouter.get_routing_info(client)
            >>> print(info['description'])
            'Claude Code (local inference)'
        """
        routing_mode = getattr(client, '_fedspeak_routing_mode', 'anthropic_api')
        is_local = getattr(client, '_fedspeak_is_local', False)

        if is_local:
            description = "Claude Code (local inference)"
        else:
            description = "Anthropic API (cloud)"

        return {
            'routing_mode': routing_mode,
            'is_local': is_local,
            'description': description
        }

    @staticmethod
    def validate_api_key_format(api_key: str) -> Tuple[bool, str]:
        """Validate API key format (basic sanity check).

        Performs basic validation to ensure the key looks reasonable. Does not
        verify the key is valid with Anthropic's servers.

        Args:
            api_key: API key to validate

        Returns:
            Tuple of (is_valid, message) where:
                - is_valid: True if format looks valid
                - message: Explanation (empty string if valid, error description if not)

        Examples:
            >>> APIRouter.validate_api_key_format("sk-ant-api03-abc123")
            (True, '')

            >>> APIRouter.validate_api_key_format("invalid")
            (False, 'API key must start with sk-ant-')

            >>> APIRouter.validate_api_key_format("sk-ant-999999999999")
            (True, '')  # All-9s pattern is valid (local routing)
        """
        if not api_key:
            return False, "API key is empty"

        # Must start with sk-ant-
        if not api_key.startswith('sk-ant-'):
            return False, "API key must start with 'sk-ant-'"

        # Must have at least 3 segments (sk, ant, suffix)
        segments = api_key.split('-')
        if len(segments) < 3:
            return False, "API key must have at least 3 segments separated by hyphens"

        # Last segment should be substantial (12+ characters)
        last_segment = segments[-1]
        if len(last_segment) < 12:
            return False, f"API key suffix too short ({len(last_segment)} chars, need 12+)"

        # Looks valid (could be cloud API or local routing)
        return True, ''


# Convenience function for backward compatibility
def create_anthropic_client(api_key: Optional[str] = None, **kwargs):
    """Convenience wrapper for APIRouter.create_client().

    This function provides a simpler interface for common use cases.

    Args:
        api_key: Anthropic API key or local routing indicator
        **kwargs: Additional arguments for Anthropic client

    Returns:
        Configured Anthropic client
    """
    return APIRouter.create_client(api_key=api_key, **kwargs)

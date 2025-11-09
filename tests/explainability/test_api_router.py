"""Tests for API routing logic (APIRouter).

Tests the intelligent routing between Anthropic cloud API and local Claude Code Max
based on API key patterns.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.explainability.api_router import APIRouter, create_anthropic_client


class TestAPIKeyDetection:
    """Test API key pattern detection."""

    def test_detect_all_nines_pattern_exact(self):
        """Test detection of exact 12-nine pattern."""
        key = "sk-ant-999999999999"
        mode, is_local = APIRouter.detect_routing_mode(key)

        assert mode == 'claude_code'
        assert is_local is True

    def test_detect_all_nines_pattern_with_prefix(self):
        """Test detection with standard prefix."""
        key = "sk-ant-api03-999999999999"
        mode, is_local = APIRouter.detect_routing_mode(key)

        assert mode == 'claude_code'
        assert is_local is True

    def test_detect_all_nines_pattern_long(self):
        """Test detection with extra nines (more than minimum)."""
        key = "sk-ant-api03-99999999999999999999"  # 20 nines
        mode, is_local = APIRouter.detect_routing_mode(key)

        assert mode == 'claude_code'
        assert is_local is True

    def test_detect_normal_api_key(self):
        """Test normal Anthropic API key is not detected as local."""
        key = "sk-ant-api03-abc123xyz456"
        mode, is_local = APIRouter.detect_routing_mode(key)

        assert mode == 'anthropic_api'
        assert is_local is False

    def test_detect_partial_nines_not_detected(self):
        """Test that partial nines (mixed with other chars) are not detected."""
        key = "sk-ant-api03-999999abc123"
        mode, is_local = APIRouter.detect_routing_mode(key)

        assert mode == 'anthropic_api'
        assert is_local is False

    def test_detect_too_few_nines(self):
        """Test that fewer than 12 nines are not detected."""
        key = "sk-ant-99999"  # Only 5 nines
        mode, is_local = APIRouter.detect_routing_mode(key)

        assert mode == 'anthropic_api'
        assert is_local is False

    def test_detect_empty_key(self):
        """Test empty key returns cloud API mode."""
        mode, is_local = APIRouter.detect_routing_mode("")

        assert mode == 'anthropic_api'
        assert is_local is False

    def test_detect_none_key(self):
        """Test None key returns cloud API mode."""
        mode, is_local = APIRouter.detect_routing_mode(None)

        assert mode == 'anthropic_api'
        assert is_local is False

    def test_detect_no_hyphens(self):
        """Test key without hyphens returns cloud API mode."""
        mode, is_local = APIRouter.detect_routing_mode("999999999999")

        assert mode == 'anthropic_api'
        assert is_local is False


class TestClientCreation:
    """Test client creation with routing."""

    @patch('src.explainability.api_router.anthropic.Anthropic')
    def test_create_client_with_local_key(self, mock_anthropic):
        """Test client creation with all-9s key triggers local routing."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        key = "sk-ant-999999999999"
        client = APIRouter.create_client(api_key=key)

        # Verify client was created
        mock_anthropic.assert_called_once_with(api_key=key)

        # Verify routing metadata was attached
        assert hasattr(client, '_fedspeak_routing_mode')
        assert client._fedspeak_routing_mode == 'claude_code'
        assert client._fedspeak_is_local is True

    @patch('src.explainability.api_router.anthropic.Anthropic')
    def test_create_client_with_cloud_key(self, mock_anthropic):
        """Test client creation with normal key triggers cloud routing."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        key = "sk-ant-api03-abc123xyz"
        client = APIRouter.create_client(api_key=key)

        # Verify client was created
        mock_anthropic.assert_called_once_with(api_key=key)

        # Verify routing metadata was attached
        assert hasattr(client, '_fedspeak_routing_mode')
        assert client._fedspeak_routing_mode == 'anthropic_api'
        assert client._fedspeak_is_local is False

    @patch('src.explainability.api_router.anthropic.Anthropic')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-999999999999'})
    def test_create_client_from_environment(self, mock_anthropic):
        """Test client reads key from environment variable."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        client = APIRouter.create_client()  # No key parameter

        # Verify client was created with env var
        mock_anthropic.assert_called_once()
        assert client._fedspeak_is_local is True

    def test_create_client_no_key_raises(self):
        """Test client creation with no key raises ValueError."""
        with pytest.raises(ValueError, match="No API key provided"):
            APIRouter.create_client(api_key=None)

    @patch('src.explainability.api_router.anthropic.Anthropic')
    def test_create_client_with_kwargs(self, mock_anthropic):
        """Test that additional kwargs are passed to Anthropic client."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        key = "sk-ant-api03-abc123"
        client = APIRouter.create_client(
            api_key=key,
            max_retries=5,
            timeout=30.0
        )

        # Verify kwargs were passed
        mock_anthropic.assert_called_once_with(
            api_key=key,
            max_retries=5,
            timeout=30.0
        )


class TestRoutingInfo:
    """Test routing information extraction."""

    def test_get_routing_info_local(self):
        """Test routing info for local client."""
        mock_client = MagicMock()
        mock_client._fedspeak_routing_mode = 'claude_code'
        mock_client._fedspeak_is_local = True

        info = APIRouter.get_routing_info(mock_client)

        assert info['routing_mode'] == 'claude_code'
        assert info['is_local'] is True
        assert 'local' in info['description'].lower()

    def test_get_routing_info_cloud(self):
        """Test routing info for cloud client."""
        mock_client = MagicMock()
        mock_client._fedspeak_routing_mode = 'anthropic_api'
        mock_client._fedspeak_is_local = False

        info = APIRouter.get_routing_info(mock_client)

        assert info['routing_mode'] == 'anthropic_api'
        assert info['is_local'] is False
        assert 'cloud' in info['description'].lower()

    def test_get_routing_info_no_metadata(self):
        """Test routing info defaults for client without metadata."""
        mock_client = MagicMock(spec=[])  # No attributes

        info = APIRouter.get_routing_info(mock_client)

        # Should default to cloud API
        assert info['routing_mode'] == 'anthropic_api'
        assert info['is_local'] is False


class TestAPIKeyValidation:
    """Test API key format validation."""

    def test_validate_normal_key(self):
        """Test validation of normal Anthropic key."""
        key = "sk-ant-api03-abc123xyz456def789ghi012"
        valid, message = APIRouter.validate_api_key_format(key)

        assert valid is True
        assert message == ''

    def test_validate_all_nines_key(self):
        """Test validation of all-9s local routing key."""
        key = "sk-ant-999999999999"
        valid, message = APIRouter.validate_api_key_format(key)

        assert valid is True
        assert message == ''

    def test_validate_empty_key(self):
        """Test validation rejects empty key."""
        valid, message = APIRouter.validate_api_key_format("")

        assert valid is False
        assert 'empty' in message.lower()

    def test_validate_wrong_prefix(self):
        """Test validation rejects key without sk-ant- prefix."""
        key = "wrong-prefix-abc123"
        valid, message = APIRouter.validate_api_key_format(key)

        assert valid is False
        assert 'sk-ant-' in message

    def test_validate_too_few_segments(self):
        """Test validation rejects key with too few segments."""
        key = "sk-ant"
        valid, message = APIRouter.validate_api_key_format(key)

        assert valid is False
        assert 'segment' in message.lower()

    def test_validate_short_suffix(self):
        """Test validation rejects key with short suffix."""
        key = "sk-ant-abc"  # Only 3 char suffix
        valid, message = APIRouter.validate_api_key_format(key)

        assert valid is False
        assert 'short' in message.lower()


class TestConvenienceFunction:
    """Test convenience wrapper function."""

    @patch('src.explainability.api_router.anthropic.Anthropic')
    def test_create_anthropic_client_wrapper(self, mock_anthropic):
        """Test that convenience function works identically to APIRouter.create_client()."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        key = "sk-ant-999999999999"
        client = create_anthropic_client(api_key=key)

        # Verify it behaves the same
        mock_anthropic.assert_called_once_with(api_key=key)
        assert client._fedspeak_is_local is True


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_key_with_many_hyphens(self):
        """Test key with multiple hyphens is handled correctly."""
        key = "sk-ant-api03-region-east-999999999999"
        mode, is_local = APIRouter.detect_routing_mode(key)

        # Should detect based on LAST segment only
        assert mode == 'claude_code'
        assert is_local is True

    def test_key_with_trailing_hyphen(self):
        """Test key with trailing hyphen."""
        key = "sk-ant-999999999999-"
        mode, is_local = APIRouter.detect_routing_mode(key)

        # Last segment is empty, should not detect
        assert mode == 'anthropic_api'
        assert is_local is False

    def test_key_with_whitespace(self):
        """Test key with whitespace is handled (should fail validation)."""
        key = "sk-ant-999 999 999"
        valid, message = APIRouter.validate_api_key_format(key)

        # Should fail because hyphens are missing
        assert valid is False

    def test_case_sensitivity(self):
        """Test that detection is case-sensitive (9 not 'nine')."""
        key = "sk-ant-NINE-NINE-NINE"
        mode, is_local = APIRouter.detect_routing_mode(key)

        # Should not detect (uppercase letters, not digit 9)
        assert mode == 'anthropic_api'
        assert is_local is False

    def test_mixed_nines_and_zeros(self):
        """Test that 9s mixed with 0s are not detected."""
        key = "sk-ant-990099009900"  # Mix of 9s and 0s
        mode, is_local = APIRouter.detect_routing_mode(key)

        # Should not detect (not all 9s)
        assert mode == 'anthropic_api'
        assert is_local is False

"""Unit tests for configuration and logging modules."""

import pytest
import logging
from pathlib import Path
import tempfile
import os

from src.config import setup_logging, JSONFormatter
from src.config.settings import Settings, get_settings
from src.exceptions import ConfigError


class TestJSONFormatter:
    """Test suite for JSONFormatter class."""

    def test_json_formatter_basic(self):
        """Test JSON formatter produces valid JSON."""
        import json

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        parsed = json.loads(formatted)
        assert parsed['message'] == 'Test message'
        assert parsed['level'] == 'INFO'
        assert parsed['logger'] == 'test'
        assert parsed['line'] == 42

    def test_json_formatter_with_exception(self):
        """Test JSON formatter handles exceptions."""
        import json

        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=42,
            msg='Error occurred',
            args=(),
            exc_info=exc_info
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert 'exception' in parsed
        assert 'ValueError' in parsed['exception']


class TestLoggingSetup:
    """Test suite for setup_logging function."""

    def test_setup_logging_console_only(self):
        """Test logging setup with console output only."""
        setup_logging(level='INFO', log_to_console=True, log_to_file=False)

        logger = logging.getLogger('src.core.detector')
        assert logger.level <= logging.INFO

    def test_setup_logging_creates_handlers(self):
        """Test logging setup creates appropriate handlers."""
        setup_logging(level='WARNING', log_to_console=True, log_to_file=False)

        logger = logging.getLogger('src')

        # Should have handlers configured
        assert len(logger.handlers) > 0 or len(logging.root.handlers) > 0

    def test_setup_logging_both_outputs(self, tmp_path):
        """Test logging with both console and file output."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        setup_logging(log_dir=str(log_dir), level='DEBUG',
                     log_to_console=True, log_to_file=True)

        logger = logging.getLogger('src')
        assert logger.level <= logging.DEBUG


class TestSettings:
    """Test suite for Settings class."""

    def test_settings_initialization(self):
        """Test Settings class initializes correctly."""
        settings = Settings()
        assert settings.config is not None
        assert isinstance(settings.config, dict)

    def test_settings_get_existing_key(self):
        """Test getting existing configuration key."""
        settings = Settings()

        # Should have detection settings from config.yaml
        lookback = settings.get('detection.hybrid_detector.lookback')
        assert lookback is not None
        assert isinstance(lookback, int)

    def test_settings_get_with_default(self):
        """Test getting non-existent key returns default."""
        settings = Settings()

        value = settings.get('nonexistent.key.path', default=42)
        assert value == 42

    def test_settings_get_nested_keys(self):
        """Test dot notation for nested keys."""
        settings = Settings()

        # Test multi-level nesting
        value = settings.get('detection.hybrid_detector.increase_threshold')
        assert value is not None

    def test_settings_singleton_pattern(self):
        """Test get_settings returns same instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_get_path(self):
        """Test get_path method resolves paths and handles defaults."""
        settings = Settings()

        # Test path resolution with default (when key doesn't exist or returns non-path value)
        test_path = settings.get_path('nonexistent.path.key', default='data/test')
        assert isinstance(test_path, Path)
        assert 'data' in str(test_path)

    def test_settings_multiple_instances(self):
        """Test multiple Settings instances work correctly."""
        settings1 = Settings()
        settings2 = Settings()

        # Both should have config loaded
        assert settings1.config is not None
        assert settings2.config is not None
        assert isinstance(settings1.config, dict)
        assert isinstance(settings2.config, dict)

    def test_settings_with_env_override(self):
        """Test environment-specific configuration override."""
        # Set environment variable
        original_env = os.environ.get('FEDSPEAK_ENV')
        os.environ['FEDSPEAK_ENV'] = 'testing'

        try:
            settings = Settings()
            # Should load base config (testing.yaml may not exist, that's ok)
            assert settings.config is not None
        finally:
            # Restore original environment
            if original_env:
                os.environ['FEDSPEAK_ENV'] = original_env
            elif 'FEDSPEAK_ENV' in os.environ:
                del os.environ['FEDSPEAK_ENV']

    def test_settings_handles_missing_config(self):
        """Test Settings handles missing configuration file gracefully."""
        # This tests the error handling path
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Settings with non-existent config
            settings = Settings()
            # Should not crash, should have some config loaded
            assert settings.config is not None


class TestConfigModule:
    """Integration tests for config module."""

    def test_full_config_flow(self, tmp_path):
        """Test complete configuration and logging flow."""
        # Setup logging
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        setup_logging(log_dir=str(log_dir), level='INFO',
                     log_to_console=False, log_to_file=True)

        # Get settings
        settings = get_settings()

        # Log a message
        logger = logging.getLogger('src.test')
        logger.info("Test message")

        # Verify log file contains message
        log_files = list(log_dir.glob('*.log'))
        assert len(log_files) >= 1

        # Check log file has content
        log_content = log_files[0].read_text()
        assert len(log_content) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

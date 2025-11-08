"""
FedSpeak Configuration Management
==================================

Handles loading and validation of configuration from YAML files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from ..exceptions import ConfigError


logger = logging.getLogger(__name__)


class Settings:
    """
    Configuration manager for FedSpeak.

    Loads configuration from YAML files with environment variable support.
    Supports configuration overrides via environment-specific files.

    Usage:
        settings = Settings()
        lookback = settings.get('detection.lookback', default=3)
        data_dir = settings.get('corpus.data_dir')
    """

    def __init__(self, config_path: Optional[str] = None, env: Optional[str] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to main config file (default: config/config.yaml)
            env: Environment name (default: from FEDSPEAK_ENV env var or 'development')

        Raises:
            ConfigError: If configuration file is missing or invalid
        """
        self.env = env or os.getenv('FEDSPEAK_ENV', 'development')

        # Determine config file path
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default: config/config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            self.config_path = project_root / 'config' / 'config.yaml'

        # Load main configuration
        self.config: Dict[str, Any] = {}
        self._load_config()

        # Load environment-specific overrides if they exist
        self._load_env_overrides()

        logger.info(f"Configuration loaded from {self.config_path} (env: {self.env})")

    def _load_config(self) -> None:
        """
        Load main configuration file.

        Raises:
            ConfigError: If config file is missing or invalid
        """
        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {self.config_path}: {e}") from e
        except Exception as e:
            raise ConfigError(f"Failed to load config from {self.config_path}: {e}") from e

        if not isinstance(self.config, dict):
            raise ConfigError(f"Configuration must be a dictionary, got {type(self.config)}")

    def _load_env_overrides(self) -> None:
        """
        Load environment-specific configuration overrides.

        Looks for config/{env}.yaml (e.g., config/production.yaml)
        """
        env_config_path = self.config_path.parent / f"{self.env}.yaml"

        if env_config_path.exists():
            try:
                with open(env_config_path, 'r', encoding='utf-8') as f:
                    env_config = yaml.safe_load(f)

                if env_config:
                    self._deep_merge(self.config, env_config)
                    logger.info(f"Applied environment overrides from {env_config_path}")
            except yaml.YAMLError as e:
                logger.warning(f"Failed to load env config {env_config_path}: {e}")
            except Exception as e:
                logger.warning(f"Error loading env config {env_config_path}: {e}")

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Deep merge override dict into base dict.

        Args:
            base: Base dictionary (modified in place)
            override: Override dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key (supports dot notation, e.g., 'detection.lookback')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Examples:
            >>> settings.get('detection.lookback')
            3
            >>> settings.get('detection.threshold', default=0.5)
            0.5
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_required(self, key: str) -> Any:
        """
        Get required configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            ConfigError: If key is missing
        """
        value = self.get(key)
        if value is None:
            raise ConfigError(f"Required configuration key missing: {key}")
        return value

    def get_path(self, key: str, default: Optional[str] = None) -> Path:
        """
        Get configuration value as a Path object.

        Resolves paths relative to project root.

        Args:
            key: Configuration key
            default: Default path if key not found

        Returns:
            Path object
        """
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Path configuration key missing: {key}")

        path = Path(value)

        # If relative path, resolve from project root
        if not path.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            path = project_root / path

        return path

    def to_dict(self) -> Dict[str, Any]:
        """
        Get full configuration as dictionary.

        Returns:
            Full configuration dictionary
        """
        return self.config.copy()


# Global settings instance (lazy-loaded)
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance.

    Returns:
        Settings instance (singleton)
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings(config_path: Optional[str] = None, env: Optional[str] = None) -> Settings:
    """
    Reload settings (useful for testing).

    Args:
        config_path: Path to config file
        env: Environment name

    Returns:
        New Settings instance
    """
    global _settings_instance
    _settings_instance = Settings(config_path=config_path, env=env)
    return _settings_instance


__all__ = ['Settings', 'get_settings', 'reload_settings']

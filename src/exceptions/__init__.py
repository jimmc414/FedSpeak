"""
FedSpeak Custom Exceptions
===========================

Custom exception classes for FedSpeak detection system.
"""


class FedSpeakError(Exception):
    """Base exception for all FedSpeak errors."""
    pass


class DetectionError(FedSpeakError):
    """
    Raised when detection algorithm encounters an error.

    Examples:
        - Invalid detection parameters
        - Algorithm execution failures
        - Statistical test failures
    """
    pass


class DataError(FedSpeakError):
    """
    Raised when data loading or parsing fails.

    Examples:
        - Missing data files
        - Corrupted data
        - Invalid data format
        - Empty corpus
    """
    pass


class ConfigError(FedSpeakError):
    """
    Raised when configuration is invalid or missing.

    Examples:
        - Missing configuration file
        - Invalid YAML syntax
        - Missing required configuration keys
        - Invalid configuration values
    """
    pass


__all__ = ['FedSpeakError', 'DetectionError', 'DataError', 'ConfigError']

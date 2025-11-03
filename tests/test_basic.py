"""Basic tests for FedSpeak modules."""

import pytest
import yaml
from pathlib import Path


def test_config_loads():
    """Test that configuration file loads correctly."""
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    assert 'keywords' in config
    assert 'detection' in config
    assert len(config['keywords']) >= 5


def test_modules_importable():
    """Test that all modules can be imported."""
    from fedspeak import fetcher, extractor, analyzer, detector, alerter, cli
    
    assert fetcher is not None
    assert extractor is not None
    assert analyzer is not None
    assert detector is not None
    assert alerter is not None
    assert cli is not None


def test_keyword_configuration():
    """Test keyword configuration is valid."""
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    keywords = config['keywords']
    
    # Check required fields
    for kw in keywords:
        assert 'word' in kw
        assert 'type' in kw
        assert 'enabled' in kw
        assert kw['type'] in ['addition', 'deletion', 'substitution']


def test_detection_parameters():
    """Test detection parameters are valid."""
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    detection = config['detection']
    
    assert detection['sustained_removal_threshold'] == 3
    assert detection['baseline_window_months'] == 6
    assert detection['min_baseline_samples'] == 3
    assert detection['focus_document_type'] == 'policy_statement'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

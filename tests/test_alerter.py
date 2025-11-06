"""Unit tests for AlertGenerator module."""

import pytest
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from fedspeak.alerter import AlertGenerator
from fedspeak.detector import Shift


class TestAlertGenerator:
    """Test suite for AlertGenerator class."""

    def test_initialization(self, sample_config, temp_data_dir):
        """Test alert generator initializes correctly."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        assert generator.output_dir.exists()
        assert generator.viz_dir.exists()
        assert 'transitory' in generator.context_catalog
        assert 'patient' in generator.context_catalog

    def test_build_context_catalog(self, sample_config):
        """Test context catalog construction."""
        config = sample_config
        config['alerts'] = {'output_dir': 'alerts', 'visualization_dir': 'viz'}

        generator = AlertGenerator(config)
        catalog = generator.context_catalog

        assert 'transitory' in catalog
        assert catalog['transitory']['type'] == 'deletion'
        assert catalog['transitory']['context'] == 'inflation narrative'
        assert catalog['transitory']['shift_id'] == 'SHIFT-2021-01'

    def test_generate_alert_emergence(self, sample_config, sample_keyword_metrics, temp_data_dir):
        """Test alert generation for emergence."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        shift = Shift(
            shift_type='emergence',
            word='transitory',
            date=datetime(2021, 9, 22),
            doc_id='monetary20210922a',
            doc_type='policy_statement',
            previous_count=0.0,
            current_count=2,
            confidence='high'
        )

        alert = generator.generate_alert(shift, sample_keyword_metrics)

        assert alert['shift_type'] == 'emergence'
        assert alert['word'] == 'transitory'
        assert alert['confidence'] == 'high'
        assert 'ALERT-' in alert['alert_id']
        assert alert['change']['current_count'] == 2
        assert alert['change']['previous_count'] == 0.0

    def test_generate_alert_removal(self, sample_config, sample_keyword_metrics, temp_data_dir):
        """Test alert generation for removal."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        shift = Shift(
            shift_type='removal',
            word='transitory',
            date=datetime(2021, 12, 15),
            doc_id='monetary20211215a',
            doc_type='policy_statement',
            previous_count=2.5,
            current_count=0,
            confidence='high'
        )

        alert = generator.generate_alert(shift, sample_keyword_metrics)

        assert alert['shift_type'] == 'removal'
        assert alert['word'] == 'transitory'
        assert alert['change']['current_count'] == 0
        assert alert['change']['previous_count'] == 2.5

    def test_gather_evidence_emergence(self, sample_config, sample_keyword_metrics, temp_data_dir):
        """Test evidence gathering for emergence."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        shift = Shift(
            shift_type='emergence',
            word='transitory',
            date=datetime(2021, 9, 22),
            doc_id='doc1',
            doc_type='policy_statement',
            previous_count=0.0,
            current_count=2,
            confidence='high'
        )

        evidence = generator._gather_evidence(shift, sample_keyword_metrics)

        assert 'prior_occurrences' in evidence
        assert 'first_occurrence' in evidence
        assert evidence['first_occurrence'] is True

    def test_gather_evidence_removal(self, sample_config, sample_keyword_metrics, temp_data_dir):
        """Test evidence gathering for removal."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        shift = Shift(
            shift_type='removal',
            word='transitory',
            date=datetime(2021, 12, 15),
            doc_id='doc1',
            doc_type='policy_statement',
            previous_count=2.5,
            current_count=0,
            confidence='high'
        )

        evidence = generator._gather_evidence(shift, sample_keyword_metrics)

        assert 'previous_occurrences' in evidence
        assert isinstance(evidence['previous_occurrences'], list)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_timeline_visualization(self, mock_close, mock_savefig,
                                          sample_config, sample_keyword_metrics, temp_data_dir):
        """Test timeline visualization creation."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        shift = Shift(
            shift_type='removal',
            word='transitory',
            date=datetime(2021, 12, 15),
            doc_id='doc1',
            doc_type='policy_statement',
            previous_count=2.5,
            current_count=0,
            confidence='high'
        )

        viz_path = generator._create_timeline_visualization(shift, sample_keyword_metrics)

        assert viz_path is not None
        assert 'transitory_timeline.png' in str(viz_path)
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()

    def test_format_alert_text(self, sample_config, temp_data_dir):
        """Test alert text formatting."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        alert = {
            'alert_id': 'TEST-123',
            'word': 'transitory',
            'shift_type': 'removal',
            'document': {
                'doc_type': 'policy_statement',
                'date': '2021-12-15'
            },
            'confidence': 'high',
            'change': {
                'previous_count': 2.5,
                'current_count': 0,
                'change_description': '2.5 → 0'
            },
            'context': {
                'category': 'inflation narrative',
                'significance': 'Test significance',
                'priority': 'high',
                'shift_id': 'SHIFT-2021-01'
            },
            'evidence': {},
            'visualization': None
        }

        text = generator.format_alert_text(alert)

        assert 'FEDSPEAK LANGUAGE SHIFT DETECTED' in text
        assert 'transitory' in text
        assert 'REMOVAL' in text
        assert '2.5 → 0' in text
        assert 'Test significance' in text

    def test_save_alerts(self, sample_config, temp_data_dir):
        """Test saving alerts to files."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        alert = {
            'alert_id': 'TEST-123',
            'word': 'transitory',
            'shift_type': 'removal',
            'timestamp': datetime.now().isoformat()
        }

        # Save JSON
        json_path = generator.output_dir / 'test_alert.json'
        with open(json_path, 'w') as f:
            json.dump(alert, f, indent=2)

        # Verify saved
        assert json_path.exists()

        # Verify can be loaded
        with open(json_path, 'r') as f:
            loaded = json.load(f)

        assert loaded['word'] == 'transitory'

    def test_visualization_empty_data(self, sample_config, temp_data_dir):
        """Test visualization handles empty data gracefully."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        shift = Shift(
            shift_type='emergence',
            word='nonexistent',
            date=datetime(2021, 11, 3),
            doc_id='doc1',
            doc_type='policy_statement',
            previous_count=0.0,
            current_count=1,
            confidence='high'
        )

        # Empty DataFrame
        empty_df = pd.DataFrame(columns=['date', 'word', 'count'])

        viz_path = generator._create_timeline_visualization(shift, empty_df)

        # Should return None for empty data
        assert viz_path is None

    def test_alert_id_generation(self, sample_config, temp_data_dir):
        """Test alert ID follows correct format."""
        config = sample_config
        config['alerts'] = {
            'output_dir': str(temp_data_dir / 'alerts'),
            'visualization_dir': str(temp_data_dir / 'viz')
        }

        generator = AlertGenerator(config)

        shift = Shift(
            shift_type='removal',
            word='considerable time',  # Multi-word phrase
            date=datetime(2021, 12, 15),
            doc_id='doc1',
            doc_type='policy_statement',
            previous_count=2.0,
            current_count=0,
            confidence='high'
        )

        time_series = pd.DataFrame({
            'date': [datetime(2021, 12, 15)],
            'word': ['considerable time'],
            'count': [0]
        })

        alert = generator.generate_alert(shift, time_series)

        # Check alert ID format
        assert alert['alert_id'].startswith('ALERT-20211215-removal-')
        assert 'considerable_time' in alert['alert_id']  # Spaces replaced with underscores


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

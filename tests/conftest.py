"""Pytest fixtures and test data for FedSpeak tests."""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for testing."""
    return {
        'keywords': [
            {
                'word': 'transitory',
                'type': 'deletion',
                'context': 'inflation narrative',
                'shift_id': 'SHIFT-2021-01',
                'enabled': True,
                'priority': 'high',
                'significance': 'Test significance'
            },
            {
                'word': 'patient',
                'type': 'addition',
                'context': 'rate guidance',
                'shift_id': 'SHIFT-2019-01',
                'enabled': True,
                'priority': 'high',
                'significance': 'Test significance'
            }
        ],
        'detection': {
            'sustained_removal_threshold': 3,
            'baseline_window_months': 6,
            'min_baseline_samples': 3,
            'focus_document_type': 'policy_statement'
        },
        'download': {
            'statement_url_template': 'https://www.federalreserve.gov/newsevents/pressreleases/monetary{date}.htm',
            'retry_attempts': 3,
            'retry_delay_seconds': 2
        },
        'paths': {
            'raw_data': 'data/raw',
            'processed_data': 'data/processed',
            'metadata': 'data/metadata',
            'results': 'results'
        }
    }


@pytest.fixture
def sample_html_2021() -> str:
    """Sample FOMC statement HTML from December 2021 (post-2013 format)."""
    return """
    <html>
    <head><title>Federal Reserve Press Release</title></head>
    <body>
        <div id="article">
            <h3>Federal Reserve issues FOMC statement</h3>
            <p><strong>For release at 2:00 p.m. EST</strong></p>
            <p>The Federal Reserve is committed to using its full range of tools
            to support the U.S. economy in this challenging time, thereby promoting
            its maximum employment and price stability goals.</p>
            <p>The Committee seeks to achieve maximum employment and inflation at
            the rate of 2 percent over the longer run. With inflation having exceeded
            2 percent for some time, the Committee expects it will be appropriate to
            maintain this target range until labor market conditions have reached
            levels consistent with the Committee's assessments of maximum employment.</p>
        </div>
        <div id="footer">Contact: Board of Governors</div>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_2010() -> str:
    """Sample FOMC statement HTML from 2010 (pre-2013 format)."""
    return """
    <html>
    <head><title>Federal Reserve Press Release</title></head>
    <body>
        <div id="leftText">
            <h3>FOMC Statement</h3>
            <p>Information received since the Federal Open Market Committee met
            in August indicates that the pace of recovery in output and employment
            has slowed in recent months. The Committee will maintain the target
            range for the federal funds rate at 0 to 1/4 percent and continues
            to anticipate that economic conditions are likely to warrant exceptionally
            low levels of the federal funds rate for an extended period.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_extracted_text() -> str:
    """Sample extracted text from a statement."""
    return """The Federal Reserve is committed to using its full range of tools
to support the U.S. economy. The Committee decided to keep the target range for
the federal funds rate at 0 to 1/4 percent. The Committee expects it will be
appropriate to maintain this target range for a considerable time. Inflation
has been running below the Committee's longer-run objective."""


@pytest.fixture
def sample_keyword_metrics() -> pd.DataFrame:
    """Sample keyword metrics DataFrame for testing."""
    data = {
        'date': pd.to_datetime([
            '2021-09-22', '2021-11-03', '2021-12-15',
            '2022-01-26', '2022-03-16', '2022-05-04'
        ]),
        'doc_id': [
            'monetary20210922a',
            'monetary20211103a',
            'monetary20211215a',
            'monetary20220126a',
            'monetary20220316a',
            'monetary20220504a'
        ],
        'filename': [
            'monetary20210922a.html.txt',
            'monetary20211103a.html.txt',
            'monetary20211215a.html.txt',
            'monetary20220126a.html.txt',
            'monetary20220316a.html.txt',
            'monetary20220504a.html.txt'
        ],
        'word': ['transitory'] * 6,
        'count': [2, 3, 0, 0, 0, 0],
        'doc_type': ['policy_statement'] * 6,
        'word_count': [350, 340, 355, 360, 365, 370]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_baseline_data() -> pd.DataFrame:
    """Sample data with calculated baselines."""
    df = pd.DataFrame({
        'date': pd.to_datetime([
            '2021-07-28', '2021-09-22', '2021-11-03',
            '2021-12-15', '2022-01-26', '2022-03-16'
        ]),
        'doc_id': [
            'monetary20210728a',
            'monetary20210922a',
            'monetary20211103a',
            'monetary20211215a',
            'monetary20220126a',
            'monetary20220316a'
        ],
        'filename': [
            'monetary20210728a.html.txt',
            'monetary20210922a.html.txt',
            'monetary20211103a.html.txt',
            'monetary20211215a.html.txt',
            'monetary20220126a.html.txt',
            'monetary20220316a.html.txt'
        ],
        'word': ['transitory'] * 6,
        'count': [2, 2, 3, 0, 0, 0],
        'baseline': [0.0, 2.0, 2.0, 2.3, 1.7, 1.0],
        'doc_type': ['policy_statement'] * 6
    })
    return df


@pytest.fixture
def temp_data_dir(tmp_path) -> Path:
    """Create temporary data directory structure."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    metadata_dir = tmp_path / "data" / "metadata"
    results_dir = tmp_path / "results" / "alerts"
    viz_dir = tmp_path / "results" / "visualizations"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    viz_dir.mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.fixture
def mock_response_success():
    """Mock successful HTTP response."""
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.text = "<html><body>Test content</body></html>"
            self.content = b"Test content"

        def raise_for_status(self):
            pass

    return MockResponse()


@pytest.fixture
def mock_response_404():
    """Mock 404 HTTP response."""
    class MockResponse:
        def __init__(self):
            self.status_code = 404
            self.text = "Not Found"

        def raise_for_status(self):
            from requests.exceptions import HTTPError
            raise HTTPError("404 Not Found")

    return MockResponse()

"""Flask web dashboard for FedSpeak alerts.

Provides web interface for viewing, filtering, and exporting FOMC language shift alerts.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import csv
from io import StringIO

from flask import Flask, render_template, request, jsonify, Response
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, template_folder='../../templates')
app.config['JSON_SORT_KEYS'] = False


def load_alerts(alert_dir: Path, max_age_days: Optional[int] = None) -> List[Dict]:
    """Load all alert JSON files from directory.

    Args:
        alert_dir: Directory containing alert JSON files
        max_age_days: Optional maximum age in days (filters older alerts)

    Returns:
        List of alert dictionaries, sorted by date (newest first)
    """
    alert_files = sorted(alert_dir.glob('ALERT-*.json'), reverse=True)

    alerts = []
    cutoff_date = None

    if max_age_days:
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

    for alert_file in alert_files:
        try:
            with open(alert_file, 'r', encoding='utf-8') as f:
                alert = json.load(f)

            # Filter by age if specified
            if cutoff_date:
                alert_timestamp = datetime.fromisoformat(alert['timestamp'])
                if alert_timestamp < cutoff_date:
                    continue

            alerts.append(alert)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load alert {alert_file}: {e}")
            continue

    logger.info(f"Loaded {len(alerts)} alerts from {alert_dir}")
    return alerts


def filter_alerts(alerts: List[Dict],
                  confidence: Optional[str] = None,
                  shift_type: Optional[str] = None,
                  term: Optional[str] = None,
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None,
                  tier: Optional[int] = None) -> List[Dict]:
    """Filter alerts by various criteria.

    Args:
        alerts: List of alert dictionaries
        confidence: Filter by confidence level (high/medium/low)
        shift_type: Filter by shift type (emergence/removal/increase/decrease)
        term: Filter by term (partial match, case-insensitive)
        start_date: Filter alerts on or after this date (YYYY-MM-DD)
        end_date: Filter alerts on or before this date (YYYY-MM-DD)
        tier: Filter by tier (1, 2, or 3) - Phase 5 market validation

    Returns:
        Filtered list of alerts
    """
    filtered = alerts

    if confidence:
        filtered = [a for a in filtered if a.get('confidence', '').lower() == confidence.lower()]

    if shift_type:
        filtered = [a for a in filtered if a.get('shift_type', '').lower() == shift_type.lower()]

    if term:
        term_lower = term.lower()
        filtered = [a for a in filtered if term_lower in a.get('term', '').lower()]

    if start_date:
        filtered = [a for a in filtered
                   if a.get('document', {}).get('date', '') >= start_date.replace('-', '')]

    if end_date:
        filtered = [a for a in filtered
                   if a.get('document', {}).get('date', '') <= end_date.replace('-', '')]

    # Phase 5: Filter by tier
    if tier is not None:
        filtered = [a for a in filtered if a.get('tier', 2) == tier]

    return filtered


@app.route('/')
def index():
    """Main dashboard page with alert list and filtering."""
    settings = get_settings()
    alert_dir = Path(settings.get('alerts.output_dir', default='results/alerts'))
    max_age_days = settings.get('distribution.dashboard.max_age_days', default=90)

    # Load all alerts
    all_alerts = load_alerts(alert_dir, max_age_days=max_age_days)

    # Get filter parameters from query string
    confidence_filter = request.args.get('confidence')
    shift_type_filter = request.args.get('shift_type')
    term_filter = request.args.get('term')
    start_date_filter = request.args.get('start_date')
    end_date_filter = request.args.get('end_date')
    tier_filter = request.args.get('tier')  # Phase 5: Tier filtering

    # Convert tier to int if provided
    tier_filter_int = int(tier_filter) if tier_filter and tier_filter.isdigit() else None

    # Apply filters
    filtered_alerts = filter_alerts(
        all_alerts,
        confidence=confidence_filter,
        shift_type=shift_type_filter,
        term=term_filter,
        start_date=start_date_filter,
        end_date=end_date_filter,
        tier=tier_filter_int  # Phase 5
    )

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = settings.get('distribution.dashboard.alerts_per_page', default=50)

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    paginated_alerts = filtered_alerts[start_idx:end_idx]
    total_pages = (len(filtered_alerts) + per_page - 1) // per_page

    return render_template(
        'dashboard.html',
        alerts=paginated_alerts,
        total_alerts=len(filtered_alerts),
        page=page,
        total_pages=total_pages,
        filters={
            'confidence': confidence_filter,
            'shift_type': shift_type_filter,
            'term': term_filter,
            'start_date': start_date_filter,
            'end_date': end_date_filter,
            'tier': tier_filter  # Phase 5
        }
    )


@app.route('/alert/<alert_id>')
def alert_detail(alert_id: str):
    """Detailed view of a specific alert."""
    settings = get_settings()
    alert_dir = Path(settings.get('alerts.output_dir', default='results/alerts'))

    alert_file = alert_dir / f"{alert_id}.json"

    if not alert_file.exists():
        return render_template('error.html', error=f"Alert {alert_id} not found"), 404

    try:
        with open(alert_file, 'r', encoding='utf-8') as f:
            alert = json.load(f)

        return render_template('alert_detail.html', alert=alert)

    except (json.JSONDecodeError, IOError) as e:
        return render_template('error.html', error=f"Failed to load alert: {e}"), 500


@app.route('/api/alerts')
def api_alerts():
    """JSON API endpoint for alerts."""
    settings = get_settings()
    alert_dir = Path(settings.get('alerts.output_dir', default='results/alerts'))
    max_age_days = settings.get('distribution.dashboard.max_age_days', default=90)

    # Load alerts
    all_alerts = load_alerts(alert_dir, max_age_days=max_age_days)

    # Apply filters from query parameters
    confidence_filter = request.args.get('confidence')
    shift_type_filter = request.args.get('shift_type')
    term_filter = request.args.get('term')
    start_date_filter = request.args.get('start_date')
    end_date_filter = request.args.get('end_date')

    filtered_alerts = filter_alerts(
        all_alerts,
        confidence=confidence_filter,
        shift_type=shift_type_filter,
        term=term_filter,
        start_date=start_date_filter,
        end_date=end_date_filter
    )

    # Limit results
    limit = int(request.args.get('limit', 100))
    filtered_alerts = filtered_alerts[:limit]

    return jsonify({
        'total': len(filtered_alerts),
        'alerts': filtered_alerts
    })


@app.route('/api/alerts.csv')
def api_alerts_csv():
    """CSV export endpoint for alerts."""
    settings = get_settings()
    alert_dir = Path(settings.get('alerts.output_dir', default='results/alerts'))
    max_age_days = settings.get('distribution.dashboard.max_age_days', default=90)

    # Load and filter alerts (same as JSON API)
    all_alerts = load_alerts(alert_dir, max_age_days=max_age_days)

    confidence_filter = request.args.get('confidence')
    shift_type_filter = request.args.get('shift_type')
    term_filter = request.args.get('term')
    start_date_filter = request.args.get('start_date')
    end_date_filter = request.args.get('end_date')

    filtered_alerts = filter_alerts(
        all_alerts,
        confidence=confidence_filter,
        shift_type=shift_type_filter,
        term=term_filter,
        start_date=start_date_filter,
        end_date=end_date_filter
    )

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'Alert ID',
        'Timestamp',
        'Term',
        'Shift Type',
        'Confidence',
        'Document Date',
        'Previous Avg',
        'Current Count',
        'Change Description'
    ])

    # Data rows
    for alert in filtered_alerts:
        writer.writerow([
            alert.get('alert_id', ''),
            alert.get('timestamp', ''),
            alert.get('term', ''),
            alert.get('shift_type', ''),
            alert.get('confidence', ''),
            alert.get('document', {}).get('date', ''),
            alert.get('change', {}).get('previous_avg', ''),
            alert.get('change', {}).get('current_count', ''),
            alert.get('change', {}).get('change_description', '')
        ])

    # Return as downloadable CSV
    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=fedspeak_alerts.csv'}
    )


@app.route('/api/stats')
def api_stats():
    """API endpoint for alert statistics."""
    settings = get_settings()
    alert_dir = Path(settings.get('alerts.output_dir', default='results/alerts'))
    max_age_days = settings.get('distribution.dashboard.max_age_days', default=90)

    all_alerts = load_alerts(alert_dir, max_age_days=max_age_days)

    # Calculate statistics
    stats = {
        'total_alerts': len(all_alerts),
        'by_confidence': {
            'high': len([a for a in all_alerts if a.get('confidence') == 'high']),
            'medium': len([a for a in all_alerts if a.get('confidence') == 'medium']),
            'low': len([a for a in all_alerts if a.get('confidence') == 'low'])
        },
        'by_shift_type': {
            'emergence': len([a for a in all_alerts if a.get('shift_type') == 'emergence']),
            'removal': len([a for a in all_alerts if a.get('shift_type') == 'removal']),
            'increase': len([a for a in all_alerts if a.get('shift_type') == 'increase']),
            'decrease': len([a for a in all_alerts if a.get('shift_type') == 'decrease'])
        },
        'terms': {}
    }

    # Count alerts by term
    for alert in all_alerts:
        term = alert.get('term', 'unknown')
        stats['terms'][term] = stats['terms'].get(term, 0) + 1

    # Sort terms by count
    stats['terms'] = dict(sorted(stats['terms'].items(), key=lambda x: x[1], reverse=True))

    return jsonify(stats)


def main():
    """Run Flask dashboard in development mode."""
    settings = get_settings()

    host = settings.get('distribution.dashboard.host', default='localhost')
    port = settings.get('distribution.dashboard.port', default=5000)
    debug = settings.get('distribution.dashboard.debug', default=True)

    logger.info(f"Starting FedSpeak dashboard at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # Setup logging
    from src.config import setup_logging
    setup_logging(level='INFO', log_to_console=True, log_to_file=False)

    main()

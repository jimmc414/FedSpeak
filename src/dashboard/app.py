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
from src.exploration import Word2VecExplorer, PolicyProximityScorer

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, template_folder='../../templates')
app.config['JSON_SORT_KEYS'] = False

# Phase 7: Initialize Word2Vec explorer (singleton, loaded once)
try:
    word2vec_explorer = Word2VecExplorer()
    policy_proximity = PolicyProximityScorer(explorer=word2vec_explorer)
    word2vec_enabled = True
    logger.info("Word2Vec exploration enabled")
except Exception as e:
    logger.warning(f"Word2Vec exploration disabled: {e}")
    word2vec_explorer = None
    policy_proximity = None
    word2vec_enabled = False

# Phase 8: Initialize MILA analyzer (singleton, loaded once)
try:
    from src.explainability import MILAAnalyzer
    mila_analyzer = MILAAnalyzer()
    mila_enabled = mila_analyzer.is_enabled()
    if mila_enabled:
        logger.info("MILA stance analysis enabled")
    else:
        logger.warning("MILA disabled (missing ANTHROPIC_API_KEY)")
except Exception as e:
    logger.warning(f"MILA initialization failed: {e}")
    mila_analyzer = None
    mila_enabled = False


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


# ============================================================================
# Phase 7: Word2Vec Exploration Routes
# ============================================================================

@app.route('/explore')
def explore():
    """Word2Vec exploration dashboard."""
    if not word2vec_enabled:
        return render_template('error.html',
                             error="Word2Vec exploration is not available. Model not loaded."), 503

    # Get vocabulary stats for initial page load
    vocab_stats = word2vec_explorer.get_vocabulary_stats()

    return render_template(
        'word2vec_explorer.html',
        vocab_stats=vocab_stats,
        word2vec_enabled=word2vec_enabled
    )


@app.route('/api/explore/similar')
def api_explore_similar():
    """API endpoint: Find similar words."""
    if not word2vec_enabled:
        return jsonify({'success': False, 'error': 'Word2Vec not available'}), 503

    word = request.args.get('word')
    if not word:
        return jsonify({'success': False, 'error': 'Missing required parameter: word'}), 400

    topn = int(request.args.get('topn', 10))

    # Limit topn to reasonable range
    topn = max(1, min(topn, 50))

    result = word2vec_explorer.get_similar_terms(word, topn=topn)
    return jsonify(result)


@app.route('/api/explore/similarity')
def api_explore_similarity():
    """API endpoint: Calculate pairwise similarity."""
    if not word2vec_enabled:
        return jsonify({'success': False, 'error': 'Word2Vec not available'}), 503

    word1 = request.args.get('word1')
    word2 = request.args.get('word2')

    if not word1 or not word2:
        return jsonify({
            'success': False,
            'error': 'Missing required parameters: word1, word2'
        }), 400

    result = word2vec_explorer.calculate_similarity(word1, word2)
    return jsonify(result)


@app.route('/api/explore/vocabulary')
def api_explore_vocabulary():
    """API endpoint: Get vocabulary statistics."""
    if not word2vec_enabled:
        return jsonify({'success': False, 'error': 'Word2Vec not available'}), 503

    result = word2vec_explorer.get_vocabulary_stats()
    return jsonify(result)


@app.route('/api/explore/proximity')
def api_explore_proximity():
    """API endpoint: Calculate policy proximity score."""
    if not word2vec_enabled:
        return jsonify({'success': False, 'error': 'Word2Vec not available'}), 503

    word = request.args.get('word')
    if not word:
        return jsonify({'success': False, 'error': 'Missing required parameter: word'}), 400

    result = policy_proximity.calculate_proximity_score(word)
    return jsonify(result)


@app.route('/api/explore/search')
def api_explore_search():
    """API endpoint: Search vocabulary (autocomplete)."""
    if not word2vec_enabled:
        return jsonify({'success': False, 'error': 'Word2Vec not available'}), 503

    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'error': 'Query must be at least 2 characters'
        }), 400

    limit = int(request.args.get('limit', 20))
    limit = max(1, min(limit, 50))

    result = word2vec_explorer.search_vocabulary(query, limit=limit)
    return jsonify(result)


# ============================================================================
# Phase 8: MILA Explainability & Visualization Routes
# ============================================================================

@app.route('/explainability')
def explainability():
    """MILA stance analysis dashboard."""
    if not mila_enabled:
        return render_template(
            'error.html',
            error="MILA is not available. Set ANTHROPIC_API_KEY to enable."
        ), 503

    # Load available statements for dropdown
    statements = _get_statement_list()

    return render_template(
        'explainability.html',
        statements=statements,
        mila_enabled=mila_enabled
    )


@app.route('/explainability/compare')
def explainability_compare():
    """Statement comparison view."""
    if not mila_enabled:
        return render_template(
            'error.html',
            error="MILA is not available. Set ANTHROPIC_API_KEY to enable."
        ), 503

    # Get query parameters
    date1 = request.args.get('date1')
    date2 = request.args.get('date2')

    # Load available statements
    statements = _get_statement_list()

    # If both dates provided, load comparison data
    if date1 and date2:
        try:
            import difflib
            from pathlib import Path

            # Load statements
            data_dir = Path('data/processed')
            stmt1_path = data_dir / f'policy_statement_{date1}.txt'
            stmt2_path = data_dir / f'policy_statement_{date2}.txt'

            if not stmt1_path.exists() or not stmt2_path.exists():
                return render_template(
                    'error.html',
                    error=f"Statement files not found for {date1} or {date2}"
                ), 404

            with open(stmt1_path, 'r', encoding='utf-8') as f:
                text1 = f.read()
            with open(stmt2_path, 'r', encoding='utf-8') as f:
                text2 = f.read()

            # Get MILA analyses
            stance1 = mila_analyzer.analyze_stance(text1, date1)
            stance2 = mila_analyzer.analyze_stance(text2, date2)

            # Generate diff HTML
            diff = difflib.HtmlDiff()
            diff_html = diff.make_table(
                text1.splitlines(),
                text2.splitlines(),
                fromdesc=f"Statement {date1}",
                todesc=f"Statement {date2}",
                context=True,
                numlines=3
            )

            return render_template(
                'comparison.html',
                statements=statements,
                date1=date1,
                date2=date2,
                date1_display=_format_date(date1),
                date2_display=_format_date(date2),
                stance1=stance1,
                stance2=stance2,
                text1=text1.replace('\n', '<br>'),
                text2=text2.replace('\n', '<br>'),
                diff_html=diff_html
            )

        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            return render_template(
                'error.html',
                error=f"Failed to load comparison: {str(e)}"
            ), 500

    # No dates provided, show selector only
    return render_template(
        'comparison.html',
        statements=statements,
        date1=None,
        date2=None
    )


@app.route('/api/explainability/stance/<date>')
def api_stance(date):
    """API endpoint: Get MILA stance analysis for a statement."""
    if not mila_enabled:
        return jsonify({'success': False, 'error': 'MILA not available'}), 503

    try:
        from pathlib import Path

        # Load statement text
        data_dir = Path('data/processed')
        stmt_path = data_dir / f'policy_statement_{date}.txt'

        if not stmt_path.exists():
            return jsonify({
                'success': False,
                'error': f'Statement not found for date {date}'
            }), 404

        with open(stmt_path, 'r', encoding='utf-8') as f:
            statement_text = f.read()

        # Get stance analysis
        result = mila_analyzer.analyze_stance(statement_text, date)

        # Add statement text to response
        result['statement_text'] = statement_text
        result['date'] = date

        return jsonify(result)

    except Exception as e:
        logger.error(f"Stance API error for {date}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/explainability/cost')
def api_cost():
    """API endpoint: Get MILA cost summary."""
    if not mila_enabled:
        return jsonify({'success': False, 'error': 'MILA not available'}), 503

    try:
        summary = mila_analyzer.get_cost_summary()
        return jsonify({'success': True, **summary})
    except Exception as e:
        logger.error(f"Cost summary error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/visualizations/stance-trend')
def api_stance_trend():
    """API endpoint: Get historical stance trend data."""
    if not mila_enabled:
        return jsonify({'success': False, 'error': 'MILA not available'}), 503

    try:
        from pathlib import Path

        # Get all cached stance analyses
        cache_dir = Path('data/mila_cache/stance')
        if not cache_dir.exists():
            return jsonify({
                'success': True,
                'timeline': [],
                'message': 'No cached analyses yet'
            })

        import json
        timeline = []

        for cache_file in sorted(cache_dir.glob('*.json')):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Extract date from metadata
                date = data.get('metadata', {}).get('date', cache_file.stem)

                timeline.append({
                    'date': date,
                    'stance': data.get('stance'),
                    'score': data.get('score'),
                    'confidence': data.get('confidence')
                })
            except Exception as e:
                logger.warning(f"Failed to load {cache_file}: {e}")
                continue

        # Sort by date
        timeline.sort(key=lambda x: x['date'])

        return jsonify({
            'success': True,
            'timeline': timeline,
            'count': len(timeline)
        })

    except Exception as e:
        logger.error(f"Stance trend error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _get_statement_list():
    """Helper: Get list of available statements."""
    from pathlib import Path

    data_dir = Path('data/processed')
    statements = []

    for file_path in sorted(data_dir.glob('policy_statement_*.txt'), reverse=True):
        date = file_path.stem.replace('policy_statement_', '')
        statements.append({
            'date': date,
            'display_date': _format_date(date),
            'doc_type': 'Policy Statement'
        })

    return statements


def _format_date(date_str):
    """Helper: Format YYYYMMDD date to readable format."""
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, '%Y%m%d')
        return dt.strftime('%B %d, %Y')
    except:
        return date_str


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

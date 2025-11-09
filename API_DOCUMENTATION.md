# FedSpeak API Documentation

**Version**: 1.0
**Last Updated**: November 9, 2025
**Base URL**: `http://localhost:5000` (local development)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Main Dashboard API](#main-dashboard-api)
4. [Word2Vec Explorer API](#word2vec-explorer-api)
5. [MILA Explainability API](#mila-explainability-api)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## Overview

The FedSpeak API provides programmatic access to language shift detections, Word2Vec semantic analysis, and MILA stance classifications. All endpoints return JSON responses.

### API Features

- **Alert Retrieval**: Query alerts with filtering and pagination
- **Data Export**: CSV and JSON export endpoints
- **Word2Vec Analysis**: Semantic similarity and policy proximity
- **MILA Stance**: LLM-powered hawkish/dovish classification
- **Statistics**: System-wide stats and metrics

### Base URL

```
Local Development: http://localhost:5000
Production: https://your-domain.com  (configure as needed)
```

### Content Type

All requests and responses use `application/json` unless specified.

```http
Content-Type: application/json
Accept: application/json
```

### Claude Code Integration

**Dual Integration Points:**

FedSpeak integrates with Claude Code (Anthropic's official AI assistant) in two distinct ways:

**1. Claude Code as System Operator**
- Claude Code can autonomously operate FedSpeak via API calls
- All endpoints documented below are accessible to Claude Code for autonomous execution
- See AGENT_GUIDE.md for autonomous execution protocols and decision trees
- Example: Claude Code can query `/api/alerts`, analyze results, and generate reports

**2. Claude Code as MILA Inference Provider**
- When configured with "all 9s" API key (`sk-ant-999999999999`)
- Claude Code Max provides inference for `/api/explainability/stance/*` endpoints
- Transparent routing - API behavior is identical regardless of routing mode
- See [MILA Explainability API](#mila-explainability-api) for details

**These integrations are independent**: Claude Code can call APIs while MILA uses cloud inference, or vice versa. The system supports all combinations: Claude Code operating + cloud inference, manual operation + Claude Code inference, both, or neither.

---

## Authentication

**Current Status**: No authentication required (local development)

**Production Recommendations**:
- Implement API key authentication
- Use HTTPS/TLS encryption
- Add rate limiting per API key
- Consider OAuth 2.0 for enterprise deployments

**Future Auth Header**:
```http
Authorization: Bearer <api-key>
```

---

## Main Dashboard API

### GET `/api/alerts`

Retrieve alerts with optional filtering.

**Parameters**:

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `tier` | integer | No | Filter by tier (1, 2, or 3) | All |
| `confidence` | string | No | Filter by confidence (high, medium, low) | All |
| `shift_type` | string | No | Filter by shift type (emergence, escalation, removal, de-escalation) | All |
| `term` | string | No | Filter by monitored term | All |
| `start_date` | string | No | Start date (YYYY-MM-DD) | All time |
| `end_date` | string | No | End date (YYYY-MM-DD) | All time |
| `page` | integer | No | Page number for pagination | 1 |
| `per_page` | integer | No | Alerts per page | 20 |

**Example Request**:
```http
GET /api/alerts?tier=1&confidence=high&start_date=2021-01-01&end_date=2021-12-31
```

**Example Response**:
```json
{
  "alerts": [
    {
      "alert_id": "ALERT-20211215-removal-transitory",
      "timestamp": "2021-12-15T14:30:00Z",
      "shift_type": "removal",
      "term": "transitory",
      "document": {
        "date": "20211215",
        "doc_type": "policy_statement"
      },
      "change": {
        "previous_avg": 2.0,
        "current_count": 0,
        "change_description": "2.0 → 0"
      },
      "confidence": "high",
      "confidence_adjusted": "tier_1",
      "tier": 1,
      "tier_name": "tier_1",
      "market_validation": {
        "validated": true,
        "market_score": 0.72,
        "indicators_triggered": 3,
        "details": {
          "dgs2_change": 0.15,
          "dgs10_change": 0.08,
          "vix_change": 12.5,
          "spy_change": -2.1
        }
      },
      "media_validation": {
        "validated": true,
        "media_score": 0.68,
        "coverage_volume": 85,
        "source_diversity": 28,
        "hybrid_sentiment": -0.42
      },
      "mila_analysis": {
        "success": true,
        "stance": "hawkish",
        "score": 0.78,
        "confidence": 0.92,
        "explanation": "The statement signals tightening policy...",
        "key_phrases": ["faster taper", "inflation risks", "prepared to adjust"],
        "cached": true
      },
      "detection_metadata": {
        "prev_avg": 2.0,
        "curr_count": 0,
        "hypothesis": "removal",
        "confidence": "high"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "pages": 1
  }
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `500 Internal Server Error`: Server error

---

### GET `/api/alerts.csv`

Export alerts as CSV file.

**Parameters**: Same as `/api/alerts`

**Example Request**:
```http
GET /api/alerts.csv?tier=1
```

**Example Response**:
```csv
alert_id,timestamp,term,shift_type,document_date,confidence,tier,previous_avg,current_count,market_validated,media_validated,mila_stance,mila_score
ALERT-20211215-removal-transitory,2021-12-15T14:30:00Z,transitory,removal,20211215,high,1,2.0,0,true,true,hawkish,0.78
```

**Content-Type**: `text/csv`

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Invalid parameters

---

### GET `/api/alerts/<alert_id>`

Retrieve specific alert by ID.

**Example Request**:
```http
GET /api/alerts/ALERT-20211215-removal-transitory
```

**Example Response**:
```json
{
  "alert_id": "ALERT-20211215-removal-transitory",
  "timestamp": "2021-12-15T14:30:00Z",
  ...
}
```

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: Alert not found

---

### GET `/api/stats`

Retrieve system statistics.

**Example Request**:
```http
GET /api/stats
```

**Example Response**:
```json
{
  "total_alerts": 45,
  "tier_1_alerts": 8,
  "tier_2_alerts": 15,
  "tier_3_alerts": 22,
  "high_confidence": 18,
  "medium_confidence": 12,
  "low_confidence": 15,
  "shift_types": {
    "emergence": 10,
    "escalation": 8,
    "removal": 12,
    "de-escalation": 15
  },
  "date_range": {
    "earliest": "2021-01-01",
    "latest": "2023-12-31"
  }
}
```

**Status Codes**:
- `200 OK`: Success

---

## Word2Vec Explorer API

### GET `/api/explore/similar`

Find semantically similar words using Word2Vec.

**Parameters**:

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `word` | string | Yes | Word to analyze | - |
| `topn` | integer | No | Number of similar words | 10 |

**Example Request**:
```http
GET /api/explore/similar?word=inflation&topn=5
```

**Example Response**:
```json
{
  "success": true,
  "word": "inflation",
  "similar_words": [
    {"word": "prices", "score": 0.89},
    {"word": "price", "score": 0.85},
    {"word": "elevated", "score": 0.78},
    {"word": "wage", "score": 0.72},
    {"word": "cost", "score": 0.68}
  ],
  "count": 5
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Missing or invalid word
- `404 Not Found`: Word not in vocabulary

---

### GET `/api/explore/proximity`

Calculate policy proximity score for a word.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `word` | string | Yes | Word to analyze |

**Example Request**:
```http
GET /api/explore/proximity?word=inflation
```

**Example Response**:
```json
{
  "success": true,
  "word": "inflation",
  "proximity_score": 0.82,
  "interpretation": "High policy relevance",
  "policy_seeds": [
    {"seed": "inflation", "similarity": 1.00},
    {"seed": "employment", "similarity": 0.65},
    {"seed": "rates", "similarity": 0.58},
    ...
  ]
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Missing word
- `404 Not Found`: Word not in vocabulary

---

### GET `/api/explore/similarity`

Calculate similarity between two words.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `word1` | string | Yes | First word |
| `word2` | string | Yes | Second word |

**Example Request**:
```http
GET /api/explore/similarity?word1=inflation&word2=prices
```

**Example Response**:
```json
{
  "success": true,
  "word1": "inflation",
  "word2": "prices",
  "similarity": 0.89
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Missing word
- `404 Not Found`: Word not in vocabulary

---

### GET `/api/explore/vocabulary`

Get Word2Vec vocabulary statistics.

**Example Request**:
```http
GET /api/explore/vocabulary
```

**Example Response**:
```json
{
  "success": true,
  "vocabulary_size": 1218,
  "model_dimensions": 100,
  "model_file": "prototypes/results/fed_word2vec.model",
  "trained_on_statements": 200
}
```

**Status Codes**:
- `200 OK`: Success

---

### GET `/api/explore/search`

Search vocabulary (autocomplete).

**Parameters**:

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `q` | string | Yes | Search query | - |
| `limit` | integer | No | Max results | 10 |

**Example Request**:
```http
GET /api/explore/search?q=inf&limit=5
```

**Example Response**:
```json
{
  "success": true,
  "query": "inf",
  "results": [
    "inflation",
    "inflate",
    "influence",
    "information",
    "infrastructure"
  ],
  "count": 5
}
```

**Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Missing query

---

## MILA Explainability API

### About Claude Code Inference Routing

The MILA Explainability API can route inference in two ways:

**Cloud API Mode (Anthropic)**:
- Standard Anthropic API key (`sk-ant-api03-...`)
- Inference runs on Anthropic's cloud infrastructure
- Cost: ~$0.003 per statement
- Production-ready with guaranteed uptime

**Local Routing Mode (Claude Code Max)**:
- Special "all 9s" API key (`sk-ant-999999999999`)
- Inference runs via Claude Code Max locally
- Cost: Free (uses Claude Code Max subscription)
- Perfect for development/testing

**Key Point for API Users**: Regardless of routing mode, all endpoints have identical behavior and response formats. The routing is completely transparent to API consumers.

**Configuration**: Set `ANTHROPIC_API_KEY` environment variable:
- Cloud: `export ANTHROPIC_API_KEY="sk-ant-api03-YOUR_KEY"`
- Local: `export ANTHROPIC_API_KEY="sk-ant-999999999999"`

**Verification**: Check application logs for:
- Cloud: `"via Anthropic API (cloud)"`
- Local: `"via Claude Code (local inference)"`

See USER_GUIDE.md MILA Configuration section for detailed setup.

### GET `/api/explainability/stance/<date>`

Get MILA stance analysis for a specific FOMC statement.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | string | Yes | Statement date (YYYYMMDD) |

**Example Request**:
```http
GET /api/explainability/stance/20211215
```

**Example Response**:
```json
{
  "success": true,
  "date": "20211215",
  "stance": "hawkish",
  "score": 0.78,
  "confidence": 0.92,
  "explanation": "The statement signals a clear hawkish shift. The removal of 'transitory' indicates the Fed no longer views inflation as temporary. The 'faster taper' language and discussion of 'adjusting the stance of policy' suggest rate increases are forthcoming.",
  "key_phrases": [
    "faster taper",
    "transitory no longer appropriate",
    "inflation risks elevated",
    "committee prepared to adjust"
  ],
  "statement_text": "The Federal Reserve...",
  "cached": true,
  "error": null
}
```

**If MILA disabled**:
```json
{
  "success": false,
  "stance": "neutral",
  "score": 0.0,
  "confidence": 0.0,
  "explanation": "MILA is not enabled (missing API key)",
  "key_phrases": [],
  "cached": false,
  "error": "MILA_DISABLED"
}
```

**Status Codes**:
- `200 OK`: Success (even if MILA disabled, see error field)
- `404 Not Found`: Statement not found
- `503 Service Unavailable`: MILA initialization failed

---

### GET `/api/explainability/cost`

Get MILA API cost summary.

**Example Request**:
```http
GET /api/explainability/cost
```

**Example Response**:
```json
{
  "success": true,
  "total_cost": 0.62,
  "total_requests": 215,
  "cost_this_month": 0.03,
  "cost_this_week": 0.01,
  "cost_today": 0.00,
  "average_cost_per_request": 0.0029,
  "cached_analyses": 215,
  "cache_hit_rate": 0.98,
  "budget_threshold": 500.0,
  "budget_remaining": 499.38
}
```

**Status Codes**:
- `200 OK`: Success

---

### GET `/api/visualizations/stance-trend`

Get historical stance timeline data.

**Example Request**:
```http
GET /api/visualizations/stance-trend
```

**Example Response**:
```json
{
  "success": true,
  "data": [
    {"date": "20210101", "stance": "dovish", "score": -0.85},
    {"date": "20210301", "stance": "dovish", "score": -0.72},
    {"date": "20210428", "stance": "neutral", "score": -0.15},
    {"date": "20210616", "stance": "neutral", "score": 0.12},
    {"date": "20211103", "stance": "hawkish", "score": 0.45},
    {"date": "20211215", "stance": "hawkish", "score": 0.78}
  ],
  "count": 6
}
```

**Status Codes**:
- `200 OK`: Success

---

## Error Handling

### Standard Error Response

All API errors follow this format:

```json
{
  "error": "Error type or message",
  "message": "Detailed error description",
  "status": 400
}
```

### Common Error Codes

**400 Bad Request**:
```json
{
  "error": "Invalid parameter",
  "message": "Parameter 'tier' must be 1, 2, or 3",
  "status": 400
}
```

**404 Not Found**:
```json
{
  "error": "Not found",
  "message": "Alert with ID 'ALERT-invalid' not found",
  "status": 404
}
```

**500 Internal Server Error**:
```json
{
  "error": "Internal server error",
  "message": "Failed to load alerts from file system",
  "status": 500
}
```

**503 Service Unavailable** (MILA only):
```json
{
  "error": "Service unavailable",
  "message": "MILA is not available. Set ANTHROPIC_API_KEY to enable.",
  "status": 503
}
```

---

## Rate Limiting

**Current Status**: No rate limiting (local development)

**Production Recommendations**:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1638720000
```

**Suggested Limits**:
- `/api/alerts`: 100 requests/minute
- `/api/explore/*`: 60 requests/minute
- `/api/explainability/stance/*`: 30 requests/minute (MILA API costs)

---

## Examples

### Python Examples

**Example 1: Get Tier 1 alerts**
```python
import requests

url = "http://localhost:5000/api/alerts"
params = {
    "tier": 1,
    "confidence": "high"
}

response = requests.get(url, params=params)
data = response.json()

for alert in data["alerts"]:
    print(f"Alert: {alert['term']} - {alert['shift_type']}")
    print(f"Tier: {alert['tier']}, Confidence: {alert['confidence']}")
    if alert.get("mila_analysis"):
        print(f"MILA Stance: {alert['mila_analysis']['stance']}")
    print("---")
```

**Example 2: Export alerts to CSV**
```python
import requests

url = "http://localhost:5000/api/alerts.csv"
params = {"tier": 1, "start_date": "2021-01-01", "end_date": "2021-12-31"}

response = requests.get(url, params=params)

with open("tier1_alerts_2021.csv", "wb") as f:
    f.write(response.content)

print("Exported to tier1_alerts_2021.csv")
```

**Example 3: Word2Vec similar words**
```python
import requests

url = "http://localhost:5000/api/explore/similar"
params = {"word": "inflation", "topn": 5}

response = requests.get(url, params=params)
data = response.json()

if data["success"]:
    print(f"Words similar to '{data['word']}':")
    for item in data["similar_words"]:
        print(f"  {item['word']}: {item['score']:.2f}")
```

**Example 4: MILA stance analysis**
```python
import requests

url = "http://localhost:5000/api/explainability/stance/20211215"

response = requests.get(url)
data = response.json()

if data["success"]:
    print(f"Date: {data['date']}")
    print(f"Stance: {data['stance']} (score: {data['score']:.2f})")
    print(f"Confidence: {data['confidence']:.2f}")
    print(f"Key phrases: {', '.join(data['key_phrases'])}")
else:
    print(f"Error: {data['error']}")
```

**Example 5: Policy proximity analysis**
```python
import requests

url = "http://localhost:5000/api/explore/proximity"

terms = ["inflation", "employment", "growth", "committee"]

for term in terms:
    response = requests.get(url, params={"word": term})
    data = response.json()

    if data["success"]:
        score = data["proximity_score"]
        interp = data["interpretation"]
        print(f"{term}: {score:.2f} ({interp})")
```

### curl Examples

**Example 1: Get all alerts**
```bash
curl http://localhost:5000/api/alerts
```

**Example 2: Filter by tier and date**
```bash
curl "http://localhost:5000/api/alerts?tier=1&start_date=2021-01-01&end_date=2021-12-31"
```

**Example 3: Export to CSV**
```bash
curl "http://localhost:5000/api/alerts.csv?tier=1" > alerts.csv
```

**Example 4: Word2Vec similarity**
```bash
curl "http://localhost:5000/api/explore/similar?word=inflation&topn=5"
```

**Example 5: MILA stance**
```bash
curl http://localhost:5000/api/explainability/stance/20211215 | jq .
```

### JavaScript (fetch) Examples

**Example 1: Get alerts and display**
```javascript
fetch('http://localhost:5000/api/alerts?tier=1')
  .then(response => response.json())
  .then(data => {
    data.alerts.forEach(alert => {
      console.log(`${alert.term}: ${alert.shift_type} (Tier ${alert.tier})`);
    });
  })
  .catch(error => console.error('Error:', error));
```

**Example 2: Word2Vec autocomplete**
```javascript
async function autocomplete(query) {
  const response = await fetch(`/api/explore/search?q=${query}&limit=10`);
  const data = await response.json();

  if (data.success) {
    return data.results;
  }
  return [];
}

// Usage
autocomplete('inf').then(results => console.log(results));
// Output: ["inflation", "inflate", "influence", ...]
```

**Example 3: Fetch stance with error handling**
```javascript
async function getStance(date) {
  try {
    const response = await fetch(`/api/explainability/stance/${date}`);
    const data = await response.json();

    if (data.success) {
      return {
        stance: data.stance,
        score: data.score,
        explanation: data.explanation
      };
    } else {
      console.error('MILA error:', data.error);
      return null;
    }
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
}

// Usage
getStance('20211215').then(result => {
  if (result) {
    console.log(`Stance: ${result.stance} (${result.score})`);
  }
});
```

---

## Webhook Support (Future)

**Planned Feature**: Webhook notifications for real-time alerts

**Example Configuration**:
```yaml
webhooks:
  enabled: true
  url: "https://your-domain.com/webhook"
  events:
    - "alert.tier1"
    - "alert.tier2"
  headers:
    Authorization: "Bearer your-webhook-secret"
```

**Webhook Payload**:
```json
{
  "event": "alert.tier1",
  "timestamp": "2021-12-15T14:30:00Z",
  "alert": {
    "alert_id": "ALERT-20211215-removal-transitory",
    "term": "transitory",
    "shift_type": "removal",
    "tier": 1,
    ...
  }
}
```

---

## API Versioning (Future)

**Planned**: Version-specific endpoints

```
/v1/api/alerts  (current)
/v2/api/alerts  (future)
```

**Header-based versioning**:
```http
Accept: application/vnd.fedspeak.v1+json
```

---

## Support

**For API questions or issues**:
1. Check this documentation
2. Review [User Guide](USER_GUIDE.md) for usage examples
3. Check GitHub issues: https://github.com/jimmc414/FedSpeak/issues
4. Create API issue with detailed description and example request

---

**End of API Documentation**

*Version 1.0 | Last Updated: November 9, 2025*
*For usage guide, see: USER_GUIDE.md | For deployment, see: PRODUCTION_RUNBOOK.md*

# qbt-rules HTTP API Reference

Complete reference for the qbt-rules v0.4.0+ HTTP API.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Job Management](#job-management)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview

The qbt-rules HTTP API provides RESTful endpoints for:

- **Job Execution**: Queue rules engine jobs
- **Job Management**: List, query, and cancel jobs
- **Monitoring**: Health checks and statistics
- **Information**: Version and system information

**Base URL**: `http://localhost:5000` (configurable)

**Content Type**: `application/json`

## Authentication

Most endpoints require API key authentication via:

1. **HTTP Header** (recommended):
   ```
   X-API-Key: your-secret-api-key
   ```

2. **Query Parameter** (convenience):
   ```
   ?key=your-secret-api-key
   ```

### Unauthenticated Endpoints

- `GET /api/health` - Health check (for container orchestration)
- `GET /api/version` - Version information

## Endpoints

### POST /api/execute

Queue a rules engine execution job.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `context` | string | No | Context filter (weekly-cleanup, torrent-imported, download-finished, adhoc-run) |
| `hash` | string | No | Torrent hash (40-character hex) to process single torrent |
| `key` | string | Yes* | API key (*or use X-API-Key header) |

**Response**: `202 Accepted`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "context": "weekly-cleanup",
  "hash": null,
  "status": "pending",
  "created_at": "2024-01-15T10:30:00.123456",
  "started_at": null,
  "completed_at": null,
  "result": null,
  "error": null
}
```

**Errors**:
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Missing or invalid API key
- `500 Internal Server Error` - Queue error

**Example**:
```bash
# Execute weekly-cleanup rules
curl -X POST "http://localhost:5000/api/execute?context=weekly-cleanup&key=my-secret-key"

# Process single torrent on completion
curl -X POST "http://localhost:5000/api/execute?context=download-finished&hash=abc123...&key=my-secret-key"

# Using header authentication
curl -X POST "http://localhost:5000/api/execute?context=adhoc-run" \
  -H "X-API-Key: my-secret-key"
```

---

### GET /api/jobs

List jobs with filtering and pagination.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status (pending, processing, completed, failed, cancelled) |
| `context` | string | No | Filter by context (weekly-cleanup, torrent-imported, etc.) |
| `limit` | integer | No | Max results (default: 50, max: 100) |
| `offset` | integer | No | Pagination offset (default: 0) |
| `key` | string | Yes* | API key (*or use X-API-Key header) |

**Response**: `200 OK`

```json
{
  "total": 150,
  "limit": 50,
  "offset": 0,
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "context": "weekly-cleanup",
      "hash": null,
      "status": "completed",
      "created_at": "2024-01-15T10:30:00",
      "started_at": "2024-01-15T10:30:01",
      "completed_at": "2024-01-15T10:30:05",
      "result": {
        "total_torrents": 42,
        "torrents_processed": 10,
        "rules_matched": 5,
        "actions_executed": 8,
        "actions_skipped": 2,
        "errors": 0,
        "dry_run": false
      },
      "error": null
    }
  ]
}
```

**Errors**:
- `400 Bad Request` - Invalid status filter
- `401 Unauthorized` - Missing or invalid API key

**Examples**:
```bash
# List all jobs (newest first)
curl "http://localhost:5000/api/jobs?key=my-secret-key"

# List only pending jobs
curl "http://localhost:5000/api/jobs?status=pending&key=my-secret-key"

# List weekly-cleanup context jobs
curl "http://localhost:5000/api/jobs?context=weekly-cleanup&key=my-secret-key"

# Pagination
curl "http://localhost:5000/api/jobs?limit=20&offset=40&key=my-secret-key"

# Combined filters
curl "http://localhost:5000/api/jobs?status=completed&context=weekly-cleanup&limit=10&key=my-secret-key"
```

---

### GET /api/jobs/:job_id

Get detailed status of a specific job.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | Job UUID |

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | string | Yes* | API key (*or use X-API-Key header) |

**Response**: `200 OK`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "context": "download-finished",
  "hash": "abc123def456789...",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00",
  "started_at": "2024-01-15T10:30:01",
  "completed_at": "2024-01-15T10:30:03",
  "result": {
    "total_torrents": 1,
    "torrents_processed": 1,
    "rules_matched": 2,
    "actions_executed": 3,
    "actions_skipped": 0,
    "errors": 0,
    "dry_run": false
  },
  "error": null
}
```

**Errors**:
- `404 Not Found` - Job not found
- `401 Unauthorized` - Missing or invalid API key

**Example**:
```bash
curl "http://localhost:5000/api/jobs/550e8400-e29b-41d4-a716-446655440000?key=my-secret-key"
```

---

### DELETE /api/jobs/:job_id

Cancel a pending job.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | Job UUID |

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | string | Yes* | API key (*or use X-API-Key header) |

**Response**: `200 OK`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

**Errors**:
- `400 Bad Request` - Job not in pending status (cannot cancel)
- `404 Not Found` - Job not found
- `401 Unauthorized` - Missing or invalid API key

**Example**:
```bash
curl -X DELETE "http://localhost:5000/api/jobs/550e8400-e29b-41d4-a716-446655440000?key=my-secret-key"
```

---

### GET /api/health

Health check endpoint for monitoring and container orchestration.

**Authentication**: Not required

**Response**: `200 OK` (healthy) or `503 Service Unavailable` (unhealthy)

**Healthy Response**:
```json
{
  "status": "healthy",
  "version": "0.4.0",
  "queue": {
    "backend": "SQLiteQueue",
    "pending_jobs": 3,
    "processing_jobs": 1
  },
  "worker": {
    "status": "running",
    "last_job_completed": "2024-01-15T10:30:05"
  },
  "timestamp": "2024-01-15T10:35:00"
}
```

**Unhealthy Response** (`503`):
```json
{
  "status": "unhealthy",
  "errors": [
    "Queue backend not accessible",
    "Worker thread not running"
  ],
  "timestamp": "2024-01-15T10:35:00"
}
```

**Example**:
```bash
# Simple health check
curl http://localhost:5000/api/health

# With exit code (for monitoring)
curl -f http://localhost:5000/api/health || echo "Service unhealthy"
```

---

### GET /api/stats

Get detailed server statistics.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | string | Yes* | API key (*or use X-API-Key header) |

**Response**: `200 OK`

```json
{
  "jobs": {
    "total": 1523,
    "pending": 2,
    "processing": 1,
    "completed": 1487,
    "failed": 31,
    "cancelled": 2
  },
  "performance": {
    "average_execution_time": "3.45s"
  },
  "queue": {
    "backend": "SQLiteQueue",
    "depth": 2
  },
  "worker": {
    "status": "running",
    "last_job_completed": "2024-01-15T10:30:05"
  },
  "timestamp": "2024-01-15T10:35:00"
}
```

**Errors**:
- `401 Unauthorized` - Missing or invalid API key

**Example**:
```bash
curl "http://localhost:5000/api/stats?key=my-secret-key" | jq
```

---

### GET /api/version

Get version information.

**Authentication**: Not required

**Response**: `200 OK`

```json
{
  "version": "0.4.0",
  "api_version": "1.0",
  "python_version": "3.11.7"
}
```

**Example**:
```bash
curl http://localhost:5000/api/version
```

---

## Job Management

### Job Lifecycle

```
┌─────────┐
│ pending │  ← Job queued via POST /api/execute
└────┬────┘
     │
     │ Worker dequeues
     ▼
┌────────────┐
│ processing │  ← Job being executed by worker
└─────┬──────┘
      │
      ├─────────────┐
      │             │
      ▼             ▼
┌───────────┐  ┌────────┐
│ completed │  │ failed │
└───────────┘  └────────┘

              ┌───────────┐
              │ cancelled │  ← DELETE /api/jobs/:id (only if pending)
              └───────────┘
```

### Polling for Job Completion

To wait for job completion (synchronous behavior):

```bash
#!/bin/bash
JOB_ID=$(curl -s -X POST "http://localhost:5000/api/execute?context=weekly-cleanup&key=my-key" | jq -r '.job_id')

echo "Job queued: $JOB_ID"

# Poll until completed
while true; do
  STATUS=$(curl -s "http://localhost:5000/api/jobs/$JOB_ID?key=my-key" | jq -r '.status')

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    echo "Job $STATUS"
    curl -s "http://localhost:5000/api/jobs/$JOB_ID?key=my-key" | jq
    break
  fi

  echo "Status: $STATUS (waiting...)"
  sleep 1
done
```

Or use the built-in CLI flag:

```bash
qbt-rules --context weekly-cleanup --wait
```

### Job Result Format

Completed jobs contain execution statistics in the `result` field:

```json
{
  "result": {
    "total_torrents": 42,       // Total torrents fetched from qBittorrent
    "torrents_processed": 10,   // Torrents that matched at least one rule
    "rules_matched": 15,        // Total rule matches across all torrents
    "actions_executed": 20,     // Actions actually executed
    "actions_skipped": 5,       // Actions skipped (idempotency/dry-run)
    "errors": 0,                // Action execution errors
    "dry_run": false            // Whether dry-run mode was enabled
  }
}
```

Failed jobs contain error tracebacks in the `error` field.

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `202` | Accepted | Job queued successfully |
| `400` | Bad Request | Invalid parameters |
| `401` | Unauthorized | Missing or invalid API key |
| `404` | Not Found | Job or endpoint not found |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Health check failed |

### Error Response Format

All errors return JSON:

```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

## Examples

### Scheduled Execution (Cron)

Add to crontab to run every 5 minutes:

```cron
*/5 * * * * curl -X POST "http://qbt-rules:5000/api/execute?context=weekly-cleanup&key=$API_KEY" >> /var/log/qbt-rules-cron.log 2>&1
```

### Webhook Integration (qBittorrent)

qBittorrent can fire webhooks on torrent events (requires qBittorrent v4.2+).

**Configure in qBittorrent**:
1. Settings → Web UI → Advanced
2. Enable "Run external program on torrent completion"
3. Command:
   ```bash
   curl -X POST "http://qbt-rules:5000/api/execute?context=download-finished&hash=%I&key=YOUR_API_KEY"
   ```

**Available qBittorrent variables**:
- `%I` - Torrent hash
- `%N` - Torrent name
- `%L` - Category
- `%F` - Content path

### Python Client Example

```python
import requests
import time

BASE_URL = "http://localhost:5000"
API_KEY = "your-secret-key"

def execute_rules(context=None, hash=None, wait=False):
    """Execute rules and optionally wait for completion"""

    # Queue job
    params = {"key": API_KEY}
    if context:
        params["context"] = context
    if hash:
        params["hash"] = hash

    response = requests.post(f"{BASE_URL}/api/execute", params=params)
    response.raise_for_status()

    job = response.json()
    job_id = job["job_id"]

    print(f"Job queued: {job_id}")

    if not wait:
        return job

    # Poll for completion
    while True:
        response = requests.get(
            f"{BASE_URL}/api/jobs/{job_id}",
            params={"key": API_KEY}
        )
        response.raise_for_status()

        job = response.json()
        status = job["status"]

        if status in ("completed", "failed"):
            print(f"Job {status}")
            return job

        print(f"Status: {status} (waiting...)")
        time.sleep(1)

# Usage
job = execute_rules(context="weekly-cleanup", wait=True)
print(f"Processed {job['result']['total_torrents']} torrents")
```

### Monitoring with Prometheus

Export metrics from `/api/stats`:

```python
from prometheus_client import Gauge, start_http_server
import requests
import time

# Define metrics
jobs_total = Gauge('qbt_rules_jobs_total', 'Total number of jobs')
jobs_pending = Gauge('qbt_rules_jobs_pending', 'Number of pending jobs')
jobs_processing = Gauge('qbt_rules_jobs_processing', 'Number of processing jobs')
jobs_completed = Gauge('qbt_rules_jobs_completed', 'Number of completed jobs')
jobs_failed = Gauge('qbt_rules_jobs_failed', 'Number of failed jobs')

def collect_metrics():
    response = requests.get(
        "http://localhost:5000/api/stats",
        params={"key": "your-api-key"}
    )
    stats = response.json()

    jobs_total.set(stats['jobs']['total'])
    jobs_pending.set(stats['jobs']['pending'])
    jobs_processing.set(stats['jobs']['processing'])
    jobs_completed.set(stats['jobs']['completed'])
    jobs_failed.set(stats['jobs']['failed'])

if __name__ == '__main__':
    start_http_server(8000)  # Prometheus metrics on :8000

    while True:
        collect_metrics()
        time.sleep(15)
```

### Docker Health Check

Add to Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1
```

Or docker-compose.yml:

```yaml
services:
  qbt-rules:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

## See Also

- [Architecture Documentation](./Architecture.md)
- [Docker Deployment Guide](./Docker.md)
- [Configuration Reference](../config/config.default.yml)

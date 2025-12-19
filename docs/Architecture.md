# qbt-rules Architecture (v0.4.0+)

This document describes the client-server architecture introduced in v0.4.0.

## Table of Contents

- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [Components](#components)
- [Data Flow](#data-flow)
- [Queue Backends](#queue-backends)
- [Configuration Resolution](#configuration-resolution)
- [Security Model](#security-model)

## Overview

qbt-rules v0.4.0 introduces a **client-server architecture** with the following design goals:

1. **Sequential Execution**: Ensure rules run sequentially to prevent race conditions
2. **Persistent Queue**: Jobs survive server restarts
3. **HTTP API**: RESTful interface for job submission and management
4. **Docker-First**: Containerized deployment with Docker Compose examples
5. **Pluggable Backends**: Support SQLite (default) and Redis queue backends

### Key Changes from v0.3.x

| Aspect | v0.3.x (Standalone) | v0.4.0+ (Client-Server) |
|--------|-------------------|-------------------------|
| Execution | Direct CLI invocation | HTTP API + Worker thread |
| Concurrency | None (sequential by default) | Queue-based sequential processing |
| State | Stateless | Persistent job queue |
| Distribution | PyPI package | Docker images (ghcr.io) |
| Configuration | CLI args + YAML | CLI + ENV + YAML (with _FILE secrets) |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │  Cron    │   │ Webhook  │   │  Manual  │   │  Script  │   │
│  │  Job     │   │  Handler │   │   CLI    │   │  Trigger │   │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   │
│       │              │              │              │          │
│       └──────────────┴──────────────┴──────────────┘          │
│                           │                                    │
│                  HTTP POST /api/execute                        │
│                   ?context=X&hash=Y&api-key=Z                      │
│                           │                                    │
└───────────────────────────┼────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Server Layer                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Flask HTTP API Server                        │ │
│  │  (Gunicorn with 1+ workers)                              │ │
│  │                                                           │ │
│  │  Endpoints:                                               │ │
│  │  • POST /api/execute         - Queue job                 │ │
│  │  • GET  /api/jobs           - List jobs                  │ │
│  │  • GET  /api/jobs/:id       - Get job status             │ │
│  │  • DELETE /api/jobs/:id     - Cancel pending job         │ │
│  │  • GET  /api/health         - Health check               │ │
│  │  • GET  /api/stats          - Statistics                 │ │
│  │  • GET  /api/version        - Version info               │ │
│  └──────────────────┬────────────────────────────────────────┘ │
│                     │                                          │
│                     │ enqueue(context, hash)                   │
│                     ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Queue Manager (Abstract)                     │ │
│  │                                                           │ │
│  │  Interface:                                               │ │
│  │  • enqueue()       - Add job to queue                    │ │
│  │  • dequeue()       - Get next pending job                │ │
│  │  • update_status() - Update job state                    │ │
│  │  • list_jobs()     - Query jobs                          │ │
│  │  • cancel_job()    - Cancel pending job                  │ │
│  │  • cleanup()       - Remove old completed jobs           │ │
│  └──────────────────┬────────────────────────────────────────┘ │
│                     │                                          │
│        ┌────────────┴────────────┐                             │
│        │                         │                             │
│        ▼                         ▼                             │
│  ┌────────────┐          ┌────────────┐                        │
│  │  SQLite    │          │   Redis    │                        │
│  │  Backend   │          │  Backend   │                        │
│  │ (default)  │          │ (optional) │                        │
│  └────────────┘          └────────────┘                        │
│        │                         │                             │
│        └────────────┬────────────┘                             │
│                     │ dequeue()                                │
│                     ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Worker Thread                                │ │
│  │  (Background thread, single instance)                     │ │
│  │                                                           │ │
│  │  Loop:                                                    │ │
│  │  1. Dequeue next job (blocking with timeout)             │ │
│  │  2. Execute via RulesEngine                              │ │
│  │  3. Update job status (completed/failed)                 │ │
│  │  4. Repeat                                                │ │
│  └──────────────────┬────────────────────────────────────────┘ │
│                     │                                          │
│                     │ engine.run(context, hash)                │
│                     ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Rules Engine                                 │ │
│  │                                                           │ │
│  │  1. Fetch torrents from qBittorrent API                  │ │
│  │  2. Load rules from rules.yml                            │ │
│  │  3. Evaluate conditions (with context filter)            │ │
│  │  4. Execute actions (with idempotency checks)            │ │
│  │  5. Return execution statistics                          │ │
│  └──────────────────┬────────────────────────────────────────┘ │
│                     │                                          │
│                     │ qbittorrent-api calls                    │
│                     ▼                                          │
└─────────────────────┼────────────────────────────────────────────
                      │
                      ▼
              ┌─────────────┐
              │ qBittorrent │
              │   Server    │
              └─────────────┘
```

## Components

### 1. Flask HTTP API Server

**Purpose**: Provide RESTful API for job submission and management

**Key Features**:
- API key authentication (constant-time comparison)
- Gunicorn WSGI server (production-ready)
- JSON responses with proper HTTP status codes
- Health check endpoint (no auth required)

**Configuration**:
```yaml
server:
  host: 0.0.0.0
  port: 5000
  api_key: your-secret-key
  workers: 1  # Gunicorn worker processes
```

### 2. Queue Manager

**Purpose**: Abstract interface for job queue backends

**Job Lifecycle**:
```
pending → processing → completed
                    ↘ failed
                    ↘ cancelled
```

**Job Structure**:
```python
{
  'job_id': 'uuid-v4',
  'context': 'weekly-cleanup',  # or torrent-imported, download-finished, adhoc-run, etc.
  'hash': 'abc123...',     # optional torrent hash filter
  'status': 'pending',     # pending, processing, completed, failed, cancelled
  'created_at': '2024-01-01T00:00:00',
  'started_at': '2024-01-01T00:00:05',
  'completed_at': '2024-01-01T00:00:10',
  'result': {              # execution statistics
    'total_torrents': 10,
    'rules_matched': 3,
    'actions_executed': 5
  },
  'error': null  # error traceback if failed
}
```

### 3. SQLite Backend (Default)

**Storage**: `/config/qbt-rules.db`

**Features**:
- Single-file database (easy backups)
- WAL mode (Write-Ahead Logging)
- Thread-safe (connection-per-thread)
- ACID transactions
- Auto-migration schema

**Tables**:
```sql
-- Job queue
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    context TEXT,
    hash TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result TEXT,  -- JSON
    error TEXT
);

-- Indexes for fast queries
CREATE INDEX idx_status ON jobs(status);
CREATE INDEX idx_created_at ON jobs(created_at DESC);
CREATE INDEX idx_context ON jobs(context);
```

**Pros**: Zero dependencies, simple, reliable
**Cons**: Single-writer limit (fine for home use)

### 4. Redis Backend (Optional)

**Storage**: Redis server (in-memory + persistence)

**Features**:
- High performance (in-memory operations)
- Connection pooling
- Multiple data structures (LIST, HASH, SET, ZSET)
- Atomic operations

**Data Structures**:
```
qbt_rules:queue:pending           LIST   - FIFO job queue
qbt_rules:jobs:{id}               HASH   - Job data
qbt_rules:jobs:status:{status}    SET    - Jobs by status index
qbt_rules:jobs:context:{context}  SET    - Jobs by context index
qbt_rules:jobs:by_time            ZSET   - Time-sorted for cleanup
```

**Pros**: High performance, scalable
**Cons**: Requires Redis server, more complex

### 5. Worker Thread

**Purpose**: Process queued jobs sequentially

**Key Features**:
- Runs in background thread (daemon=False for graceful shutdown)
- Single instance ensures sequential execution
- Configurable poll interval (default: 1 second)
- Exception handling with error logging

**Execution Flow**:
1. Poll queue for next job (blocking with timeout)
2. Mark job as `processing`
3. Execute via `RulesEngine.run(context, hash)`
4. Update job status with result or error
5. Repeat

### 6. Rules Engine

**Purpose**: Core automation logic (unchanged from v0.3.x)

**Key Features**:
- Context filtering (`context:` in rule conditions)
- Condition evaluation (dot notation, logical operators)
- Action execution (idempotency checks)
- Statistics collection

See [Rules Reference](../config/rules.default.yml) for syntax.

## Data Flow

### Scheduled Execution (Cron)

```
1. Cron triggers every 5 minutes
   ↓
2. curl -X POST "http://qbt-rules:5000/api/execute?context=weekly-cleanup&key=xxx"
   ↓
3. Flask enqueues job → Queue (status: pending)
   ↓
4. Returns HTTP 202 with job_id
   ↓
5. Worker dequeues job → Updates status to processing
   ↓
6. RulesEngine.run(context='weekly-cleanup', hash=None)
   ↓
7. Fetches all torrents from qBittorrent
   ↓
8. Evaluates rules with context filter
   ↓
9. Executes matching actions
   ↓
10. Worker updates job (status: completed, result: stats)
```

### Webhook Execution (qBittorrent Events)

```
1. qBittorrent fires webhook on torrent completion
   ↓
2. Webhook sends: POST /api/execute?context=download-finished&hash=abc123&key=xxx
   ↓
3. Flask enqueues job → Queue
   ↓
4. Worker dequeues and processes (same as above)
   ↓
5. RulesEngine.run(context='download-finished', hash='abc123')
   ↓
6. Fetches ONLY torrent with hash abc123
   ↓
7. Evaluates rules (only matches rules with context: download-finished)
   ↓
8. Executes actions on matched torrent
```

## Queue Backends

### Choosing a Backend

| Criteria | SQLite | Redis |
|----------|--------|-------|
| **Setup Complexity** | Minimal (built-in) | Requires Redis server |
| **Performance** | Good (sub-millisecond) | Excellent (in-memory) |
| **Persistence** | File-based | Configurable (RDB/AOF) |
| **Scalability** | Single-writer | Multi-writer ready |
| **Memory Usage** | Low (on-disk) | Higher (in-memory) |
| **Recommended For** | Home users, simple deployments | High-volume webhooks, multiple workers |

### Configuration Examples

**SQLite** (default):
```yaml
queue:
  backend: sqlite
  sqlite_path: /config/qbt-rules.db
  cleanup_after: 7d
```

**Redis**:
```yaml
queue:
  backend: redis
  redis_url: redis://localhost:6379/0
  # Or with password:
  # redis_url: redis://:password@localhost:6379/0
  cleanup_after: 7d
```

## Configuration Resolution

qbt-rules uses a **layered configuration system** with the following priority (highest to lowest):

```
1. CLI arguments      (--server-port 8080)
2. _FILE environment  (QBT_RULES_SERVER_API_KEY_FILE=/run/secrets/api_key)
3. ENV variables      (QBT_RULES_SERVER_API_KEY=my-key)
4. config.yml         (server: { api_key: my-key })
5. Defaults           (hardcoded in code)
```

### Universal _FILE Support

**All environment variables** support the `_FILE` suffix for Docker secrets:

```bash
# Direct value
QBT_RULES_SERVER_API_KEY=my-secret-key

# File reference (Docker secret)
QBT_RULES_SERVER_API_KEY_FILE=/run/secrets/api_key
```

The `_FILE` variant reads the value from the file path, making it compatible with Docker Swarm secrets.

### Environment Variable Naming

All environment variables use the `QBT_RULES_*` prefix:

```bash
# Server configuration
QBT_RULES_SERVER_HOST=0.0.0.0
QBT_RULES_SERVER_PORT=5000
QBT_RULES_SERVER_API_KEY=...
QBT_RULES_SERVER_WORKERS=1

# Queue configuration
QBT_RULES_QUEUE_BACKEND=sqlite
QBT_RULES_QUEUE_SQLITE_PATH=/config/qbt-rules.db
QBT_RULES_QUEUE_REDIS_URL=redis://...
QBT_RULES_QUEUE_CLEANUP_AFTER=7d

# Client configuration
QBT_RULES_CLIENT_SERVER_URL=http://localhost:5000
QBT_RULES_CLIENT_API_KEY=...

# qBittorrent connection
QBT_RULES_QBITTORRENT_HOST=http://localhost:8080
QBT_RULES_QBITTORRENT_USERNAME=admin
QBT_RULES_QBITTORRENT_PASSWORD=...

# Logging
LOG_LEVEL=INFO
TRACE_MODE=true
```

## Security Model

### Authentication

- **API Key**: Required for all authenticated endpoints
- **Header**: `X-API-Key: your-key` (recommended)
- **Query Parameter**: `?key=your-key` (convenience)
- **Comparison**: Constant-time (`secrets.compare_digest`)

### Health Check Endpoint

`GET /api/health` is **unauthenticated** for container orchestration health checks.

### Docker Secrets

Recommended for production deployments:

```yaml
# docker-compose.yml
services:
  qbt-rules:
    environment:
      QBT_RULES_SERVER_API_KEY_FILE: /run/secrets/api_key
      QBT_RULES_QBITTORRENT_PASSWORD_FILE: /run/secrets/qbt_password
    secrets:
      - api_key
      - qbt_password

secrets:
  api_key:
    file: ./secrets/api_key.txt
  qbt_password:
    file: ./secrets/qbt_password.txt
```

### Network Isolation

Use Docker networks to isolate components:

```yaml
networks:
  qbt-network:
    driver: bridge
    internal: true  # No external access
```

Expose only the Flask API port (5000) to the host.

## Performance Considerations

### Job Queue Sizing

- **SQLite**: Handles thousands of jobs efficiently
- **Redis**: Scales to millions of jobs

### Worker Threads

- Default: 1 worker (ensures sequential execution)
- Multiple workers: Possible but **not recommended** (race conditions)

### Cleanup

Old completed/failed jobs are cleaned up automatically:

```yaml
queue:
  cleanup_after: 7d  # Delete jobs older than 7 days
```

Cleanup runs every hour (configurable via worker).

### Monitoring

Check queue health:

```bash
# Health check
curl http://localhost:5000/api/health

# Statistics
curl http://localhost:5000/api/stats?key=your-key

# Queue depth
curl http://localhost:5000/api/stats?key=your-key | jq '.queue.depth'
```

## Migration from v0.3.x

v0.3.x users upgrading to v0.4.0:

1. **Rules**: No changes required (rules.yml syntax unchanged)
2. **Configuration**: config.yml structure changed (see config.default.yml)
3. **Deployment**: Switch from PyPI package to Docker images
4. **CLI**: Old CLI still works but deprecated (use client mode)

### Legacy CLI Compatibility

```bash
# Old (v0.3.x - deprecated)
qbt-rules --trigger weekly-cleanup

# New (v0.4.0+ - client mode, requires server running)
qbt-rules --context weekly-cleanup

# Server mode (new)
qbt-rules --serve
```

The `--trigger` flag is mapped to `--context` for backward compatibility.

## See Also

- [API Reference](./API.md)
- [Docker Deployment](./Docker.md)
- [Configuration Reference](../config/config.default.yml)
- [Rules Reference](../config/rules.default.yml)

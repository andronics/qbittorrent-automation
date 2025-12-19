# qbt-rules

A powerful client-server automation engine for qBittorrent with HTTP API, persistent job queue, and Docker-first deployment.

[![GitHub Release](https://img.shields.io/github/v/release/andronics/qbt-rules)](https://github.com/andronics/qbt-rules/releases)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io-blue)](https://github.com/andronics/qbt-rules/pkgs/container/qbt-rules)
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)

---

## What is qbt-rules?

qbt-rules is a **client-server automation engine** for qBittorrent that processes torrent management rules through a persistent job queue. Define YAML-based rules to automatically categorize, tag, pause, resume, delete, and manage torrents based on flexible conditions.

**v0.4.0 introduces a complete architectural transformation:**

- 🚀 **Client-Server Architecture** - HTTP API with background worker
- 📦 **Persistent Job Queue** - SQLite (default) or Redis backends
- 🐳 **Docker-First Deployment** - Containerized with multi-platform support (amd64, arm64)
- 🔐 **API Key Authentication** - Secure webhook endpoints
- 📊 **Job Management** - Track execution history, status, and statistics
- ⚡ **Sequential Processing** - Prevent race conditions with queue-based execution

**Key Features:**

- **Declarative YAML Rules** - No coding required
- **Multiple Execution Contexts** - Manual, weekly-cleanup (cron), webhooks (torrent-imported, download-finished)
- **Powerful Conditions** - Complex logic with AND/OR/NOT groups, 17+ operators
- **Rich Field Access** - Dot notation access to all torrent metadata (info.*, trackers.*, files.*, etc.)
- **Idempotent Actions** - Safe to run repeatedly
- **RESTful HTTP API** - Job submission, status tracking, statistics
- **Universal Docker Secrets** - All config values support `_FILE` suffix
- **Multi-Version qBittorrent Support** - v4.1+ through v5.1.4+ via qbittorrent-api

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- qBittorrent with Web UI enabled

### Installation

```bash
# Create directory structure
mkdir -p qbt-rules/config
cd qbt-rules
```

> **Note:** On first run, default configuration files (`config.yml` and `rules.yml`) will be automatically created in the `/config` directory. You can then edit them to customize your setup.

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  qbt-rules:
    image: ghcr.io/andronics/qbt-rules:latest
    container_name: qbt-rules
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./config:/config
    environment:
      # Server configuration
      QBT_RULES_SERVER_API_KEY: "your-secure-api-key-here"  # Change this!

      # qBittorrent connection
      QBT_RULES_QBITTORRENT_HOST: "http://qbittorrent:8080"
      QBT_RULES_QBITTORRENT_USERNAME: "admin"
      QBT_RULES_QBITTORRENT_PASSWORD: "adminpass"

      # Queue (SQLite default)
      QBT_RULES_QUEUE_BACKEND: "sqlite"
      QBT_RULES_QUEUE_SQLITE_PATH: "/config/qbt-rules.db"
```

### Start the Server

```bash
# Start container
docker-compose up -d

# Check health
curl http://localhost:5000/api/health

# View logs
docker-compose logs -f qbt-rules
```

### Your First Rule

Edit `config/rules.yml`:

```yaml
rules:
  - name: "Auto-categorize HD movies"
    enabled: true
    stop_on_match: true
    context: torrent-imported  # Runs when torrents are added
    conditions:
      all:
        - field: info.name
          operator: matches
          value: '(?i).*(1080p|2160p|4k).*'
    actions:
      - type: set_category
        params:
          category: "Movies-HD"
      - type: add_tag
        params:
          tags:
            - hd
            - auto-categorized
```

### Execute Rules

**Using HTTP API:**
```bash
# Queue a weekly-cleanup rules job
curl -X POST "http://localhost:5000/api/execute?context=weekly-cleanup&key=your-api-key"

# Process specific torrent (webhook)
curl -X POST "http://localhost:5000/api/execute?context=download-finished&hash=abc123...&key=your-api-key"

# Check job status
curl "http://localhost:5000/api/jobs?key=your-api-key" | jq

# Get statistics
curl "http://localhost:5000/api/stats?key=your-api-key" | jq
```

**Using CLI (client mode):**
```bash
# Install CLI client (optional)
docker exec qbt-rules qbt-rules --context weekly-cleanup --wait

# Or from host (if qbt-rules pip package installed)
pip install qbt-rules
qbt-rules --context weekly-cleanup --client-server-url http://localhost:5000 --client-api-key your-api-key
```

---

## Architecture

qbt-rules v0.4.0 uses a client-server architecture with persistent job queue:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                                │
│                                                                 │
│  Webhook → HTTP API ← Cron Container ← Manual CLI              │
│              │                                                  │
│              └──── POST /api/execute?context=X&key=Y            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SERVER LAYER                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  Flask HTTP API (Gunicorn)                          │       │
│  │  • POST /api/execute  - Queue job                   │       │
│  │  • GET  /api/jobs     - List jobs                   │       │
│  │  • GET  /api/health   - Health check                │       │
│  │  • GET  /api/stats    - Statistics                  │       │
│  └─────────────────┬───────────────────────────────────┘       │
│                    │                                            │
│                    ▼                                            │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  Queue Manager (SQLite or Redis)                    │       │
│  │  • Persistent job storage                           │       │
│  │  • Job states: pending → processing → completed     │       │
│  └─────────────────┬───────────────────────────────────┘       │
│                    │                                            │
│                    ▼                                            │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  Worker Thread (Background)                         │       │
│  │  • Dequeues jobs sequentially                       │       │
│  │  • Executes via RulesEngine                         │       │
│  │  • Updates job status with results                  │       │
│  └─────────────────┬───────────────────────────────────┘       │
│                    │                                            │
│                    ▼                                            │
│  ┌─────────────────────────────────────────────────────┐       │
│  │  Rules Engine                                       │       │
│  │  • Loads rules.yml                                  │       │
│  │  • Evaluates conditions (context filter)            │       │
│  │  • Executes actions (idempotent)                    │       │
│  └─────────────────┬───────────────────────────────────┘       │
└────────────────────┼────────────────────────────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ qBittorrent │
              │   Server    │
              └─────────────┘
```

**Benefits:**
- **Sequential Execution**: Jobs process one at a time (no race conditions)
- **Persistence**: Jobs survive server restarts
- **Monitoring**: Track job history, status, and execution stats
- **Scalability**: Optional Redis backend for high webhook volume

📖 **[Complete Architecture Documentation](docs/Architecture.md)**

---

## Core Concepts

### Execution Contexts

Contexts filter which rules execute. Rules specify a `context:` condition, and jobs are submitted with a context parameter.

```bash
# Submit job with context
curl -X POST "http://localhost:5000/api/execute?context=weekly-cleanup&key=YOUR_KEY"
```

**Common Contexts:**

| Context | Use Case | Trigger Method |
|---------|----------|----------------|
| `weekly-cleanup` | Periodic maintenance | Cron container or systemd timer |
| `torrent-imported` | Torrent added event | qBittorrent webhook |
| `download-finished` | Download completed | qBittorrent webhook |
| `adhoc-run` | Manual execution | CLI or API call |

**Example Rule with Context:**

```yaml
rules:
  - name: "Cleanup old torrents"
    context: weekly-cleanup  # Only runs when context=weekly-cleanup
    conditions:
      all:
        - field: info.completion_on
          operator: older_than
          value: "30 days"
    actions:
      - type: delete_torrent
        params:
          keep_files: true
```

📖 **[Context Documentation](docs/Architecture.md#data-flow)**

---

### Conditions

Combine conditions with logical groups:

- **all** - AND logic (all conditions must match)
- **any** - OR logic (at least one must match)
- **none** - NOT logic (no conditions can match)

**Available Operators:**

`==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `not_contains`, `matches`, `in`, `not_in`, `older_than`, `newer_than`, `smaller_than`, `larger_than`

**Example:**
```yaml
- name: "High ratio seeded torrents"
  context: weekly-cleanup
  conditions:
    all:
      - field: info.ratio
        operator: '>='
        value: 2.0
      - field: info.seeding_time
        operator: '>'
        value: 604800  # 7 days in seconds
    none:
      - field: info.category
        operator: in
        value: [seedbox, long-term]
  actions:
    - type: add_tag
      params:
        tags:
          - ready-to-remove
```

---

### Available Fields

Access torrent data using dot notation across 8 API categories:

| Prefix | Description | Example Fields |
|--------|-------------|----------------|
| `info.*` | Main torrent info | `info.name`, `info.size`, `info.ratio`, `info.state` |
| `trackers.*` | Tracker data (collection) | `trackers.url`, `trackers.status`, `trackers.msg` |
| `files.*` | File list (collection) | `files.name`, `files.size`, `files.progress` |
| `properties.*` | Extended properties | `properties.save_path`, `properties.comment` |
| `transfer.*` | Global transfer stats | `transfer.dl_speed`, `transfer.up_speed` |
| `app.*` | Application info | `app.version`, `app.encryption` |
| `peers.*` | Peer data (collection) | `peers.ip`, `peers.client`, `peers.progress` |
| `webseeds.*` | Web seed data (collection) | `webseeds.url` |

📖 **[Complete Field Reference](config/rules.default.yml)**

---

### Actions

Execute one or more actions when conditions match:

| Action | Description |
|--------|-------------|
| `stop` / `start` / `force_start` | Control torrent state |
| `recheck` / `reannounce` | Maintenance operations |
| `delete_torrent` | Remove torrent (with/without files) |
| `set_category` | Set category |
| `add_tag` / `remove_tag` / `set_tags` | Tag management |
| `set_upload_limit` / `set_download_limit` | Speed limiting |

**Example:**
```yaml
actions:
  - type: set_category
    params:
      category: "Movies-HD"
  - type: add_tag
    params:
      tags:
        - hd
        - private
  - type: set_upload_limit
    params:
      limit: 1048576  # 1 MB/s in bytes
```

---

## Deployment Scenarios

### Webhook Integration (qBittorrent)

Configure qBittorrent to fire webhooks on events:

1. **qBittorrent Settings** → Web UI → Advanced
2. **Run external program on torrent completion:**
   ```bash
   curl -X POST "http://qbt-rules:5000/api/execute?context=download-finished&hash=%I&key=YOUR_API_KEY"
   ```

**qBittorrent Variables:**
- `%I` - Torrent hash
- `%N` - Torrent name
- `%L` - Category
- `%F` - Content path

---

### Scheduled Execution (Cron Container)

Add to docker-compose.yml:

```yaml
services:
  qbt-rules-cron:
    image: alpine:latest
    restart: unless-stopped
    command: >
      sh -c "
        apk add --no-cache curl &&
        echo '*/5 * * * * curl -X POST http://qbt-rules:5000/api/execute?context=weekly-cleanup&key=YOUR_KEY' | crontab - &&
        crond -f -l 2
      "
    depends_on:
      - qbt-rules
    networks:
      - qbt-network
```

---

### Redis Queue Backend (High Performance)

For high webhook volume, use Redis:

```yaml
version: '3.8'

services:
  qbt-rules:
    image: ghcr.io/andronics/qbt-rules:latest
    environment:
      QBT_RULES_QUEUE_BACKEND: "redis"
      QBT_RULES_QUEUE_REDIS_URL: "redis://redis:6379/0"
    depends_on:
      redis:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

volumes:
  redis-data:
```

📖 **[Docker Deployment Guide](docs/Docker.md)**

---

## HTTP API Reference

### POST /api/execute

Queue a rules execution job.

**Request:**
```bash
curl -X POST "http://localhost:5000/api/execute?context=weekly-cleanup&key=YOUR_KEY"
```

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "context": "weekly-cleanup",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00.123456"
}
```

---

### GET /api/jobs

List jobs with filtering and pagination.

**Request:**
```bash
curl "http://localhost:5000/api/jobs?status=completed&limit=10&key=YOUR_KEY"
```

**Response:**
```json
{
  "total": 150,
  "jobs": [
    {
      "job_id": "...",
      "context": "weekly-cleanup",
      "status": "completed",
      "result": {
        "total_torrents": 42,
        "rules_matched": 5,
        "actions_executed": 8
      }
    }
  ]
}
```

---

### GET /api/health

Health check endpoint (no authentication required).

**Request:**
```bash
curl http://localhost:5000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.4.0",
  "queue": {
    "backend": "SQLiteQueue",
    "pending_jobs": 2
  },
  "worker": {
    "status": "running"
  }
}
```

📖 **[Complete API Reference](docs/API.md)**

---

## Configuration

### Environment Variables

All variables support `_FILE` suffix for Docker secrets:

```yaml
environment:
  # Server
  QBT_RULES_SERVER_HOST: "0.0.0.0"
  QBT_RULES_SERVER_PORT: "5000"
  QBT_RULES_SERVER_API_KEY: "your-secret-key"
  # Or use Docker secret:
  # QBT_RULES_SERVER_API_KEY_FILE: "/run/secrets/api_key"

  # Queue
  QBT_RULES_QUEUE_BACKEND: "sqlite"  # or "redis"
  QBT_RULES_QUEUE_SQLITE_PATH: "/config/qbt-rules.db"
  QBT_RULES_QUEUE_CLEANUP_AFTER: "7d"

  # qBittorrent
  QBT_RULES_QBITTORRENT_HOST: "http://qbittorrent:8080"
  QBT_RULES_QBITTORRENT_USERNAME: "admin"
  QBT_RULES_QBITTORRENT_PASSWORD: "adminpass"
  # Or use Docker secret:
  # QBT_RULES_QBITTORRENT_PASSWORD_FILE: "/run/secrets/qbt_password"

  # Logging
  LOG_LEVEL: "INFO"  # DEBUG, INFO, WARNING, ERROR
  TRACE_MODE: "false"
```

### Docker Secrets (Recommended)

```yaml
services:
  qbt-rules:
    environment:
      QBT_RULES_SERVER_API_KEY_FILE: "/run/secrets/api_key"
      QBT_RULES_QBITTORRENT_PASSWORD_FILE: "/run/secrets/qbt_password"
    secrets:
      - api_key
      - qbt_password

secrets:
  api_key:
    file: ./secrets/api_key.txt
  qbt_password:
    file: ./secrets/qbt_password.txt
```

📖 **[Configuration Reference](config/config.default.yml)**

---

## Example Rules

### Auto-Categorize TV Shows

```yaml
- name: "Categorize TV shows"
  enabled: true
  context: torrent-imported
  conditions:
    all:
      - field: info.name
        operator: matches
        value: '(?i).*[Ss]\d{2}[Ee]\d{2}.*'
  actions:
    - type: set_category
      params:
        category: "TV-Shows"
```

### Delete Old Completed Torrents

```yaml
- name: "Delete old seeded torrents"
  enabled: true
  context: weekly-cleanup
  conditions:
    all:
      - field: info.completion_on
        operator: older_than
        value: "30 days"
      - field: info.ratio
        operator: ">="
        value: 2.0
    none:
      - field: info.category
        operator: in
        value: [keep, seedbox]
  actions:
    - type: delete_torrent
      params:
        keep_files: true
```

### Pause Large Downloads

```yaml
- name: "Pause large downloads during daytime"
  enabled: true
  context: weekly-cleanup
  conditions:
    all:
      - field: info.size
        operator: larger_than
        value: "50 GB"
      - field: info.state
        operator: contains
        value: "DL"
  actions:
    - type: stop
    - type: add_tag
      params:
        tags:
          - large-download-paused
```

📖 **[More Examples](config/rules.default.yml)**

---

## Documentation

- **[Architecture Documentation](docs/Architecture.md)** - System design and components
- **[API Reference](docs/API.md)** - Complete HTTP API documentation
- **[Docker Deployment Guide](docs/Docker.md)** - Container setup and examples
- **[Configuration Examples](config/config.default.yml)** - Server/client/queue config
- **[Rules Examples](config/rules.default.yml)** - Comprehensive rule examples

---

## Migration from v0.3.x

qbt-rules v0.4.0 introduces breaking changes:

### Key Changes

1. **Distribution**: PyPI package → Docker images (ghcr.io)
2. **Architecture**: Standalone CLI → Client-server with HTTP API
3. **Terminology**: `trigger` → `context` (backward compatible flags exist)
4. **Execution**: Direct execution → Queue-based job processing

### Migration Steps

1. **Rules File**: No changes needed (rules.yml syntax unchanged)
2. **Config File**: Update structure (see config.default.yml)
3. **Deployment**: Replace cron/systemd with Docker Compose + webhooks/cron container
4. **CLI Usage**: Update to use HTTP API or client mode

### Backward Compatibility

- Rules syntax unchanged (only `trigger:` → `context:`)
- CLI flag `--trigger` mapped to `--context` automatically
- PyPI package v0.3.x remains available (deprecated)

---

## Requirements

- **Docker** and **Docker Compose**
- **qBittorrent v4.1+** with Web UI enabled
- **Optional:** Redis server (for high-performance queue backend)

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

**Latest Release:** [v0.4.0](https://github.com/andronics/qbt-rules/releases/tag/v0.4.0) - 2024-12-14

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is released into the **public domain** under the [Unlicense](http://unlicense.org/).

You are free to use, modify, and distribute this software for any purpose without attribution.

---

**Happy automating! 🚀🐳**

For complete documentation, see [docs/](docs/).

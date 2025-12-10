# qBittorrent Automation System

Automated torrent management using a rules engine with conditions and actions.

## Architecture

```
qbittorrent/
├── lib/                 # Shared library
│   ├── api.py          # qBittorrent API client
│   ├── engine.py       # Rules engine core
│   ├── config.py       # Configuration loader
│   ├── errors.py       # User-friendly error handling
│   └── utils.py        # Shared utilities
├── triggers/           # Entry points
│   ├── manual.py       # Manual/CLI execution
│   ├── scheduled.py    # Cron/scheduled execution
│   ├── on_added.py     # Webhook: torrent added
│   └── on_completed.py # Webhook: torrent completed
└── config/
    ├── config.yml      # Settings (connection, logging)
    └── rules.yml       # Rules definitions
```

## Configuration

### Environment Variables

All core settings can be configured via environment variables:

```bash
# qBittorrent Connection
QBITTORRENT_HOST=http://localhost:8080
QBITTORRENT_USER=admin
QBITTORRENT_PASS=your_password

# Logging
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
LOG_FILE=/config/logs/qbittorrent.log

# Engine
DRY_RUN=false          # Set to true to test without making changes
CONFIG_DIR=/config     # Configuration directory
```

### config.yml

Settings and connection configuration with environment variable expansion:

```yaml
qbittorrent:
  host: ${QBITTORRENT_HOST:-http://localhost:8080}
  user: ${QBITTORRENT_USER:-admin}
  pass: ${QBITTORRENT_PASS}

logging:
  level: ${LOG_LEVEL:-INFO}
  file: ${LOG_FILE:-/config/logs/qbittorrent.log}

engine:
  dry_run: ${DRY_RUN:-false}
```

### rules.yml

Rules define conditions and actions. All fields use **dot notation** with API prefix:

- `info.*` - Core torrent data (free, already loaded)
- `trackers.*` - Tracker details (per-torrent API call)
- `files.*` - File list (per-torrent API call)
- `peers.*` - Connected peers (per-torrent API call)
- `properties.*` - Extended metadata (per-torrent API call)
- `transfer.*` - Global transfer stats (single API call)
- `webseeds.*` - Web seed sources (per-torrent API call)
- `app.*` - Global application preferences (single API call)

Rules execute in order from top to bottom. Place important rules (blocking/filtering) at the top, cleanup rules at the bottom.

Example rule:

```yaml
rules:
  - name: "Auto-categorize HD movies"
    enabled: true
    stop_on_match: false
    conditions:
      all:
        - field: info.name
          operator: contains
          value: "1080p"
        - field: info.category
          operator: ==
          value: ""
    actions:
      - type: set_category
        params:
          category: movies-hd
```

## Trigger Types

Rules can filter by trigger type:

```yaml
rules:
  - name: "Auto-categorize on add"
    conditions:
      trigger: on_added  # Only runs when torrent is added
      all:
        - field: info.name
          operator: contains
          value: "1080p"
    actions:
      - type: set_category
        params:
          category: movies-hd

  - name: "Cleanup old torrents"
    conditions:
      trigger: [scheduled, manual]  # Only runs on scheduled/manual execution
      all:
        - field: info.completion_on
          operator: older_than
          value: 30 days
    actions:
      - type: delete_torrent
        params:
          keep_files: false
```

Available triggers:
- `on_added` - Torrent added webhook
- `on_completed` - Torrent completed webhook
- `scheduled` - Cron/scheduled execution
- `manual` - Manual CLI execution

## Usage

### Manual Execution

```bash
# Run all rules
python3 triggers/manual.py

# Dry-run mode (no changes)
python3 triggers/manual.py --dry-run

# Custom config directory
python3 triggers/manual.py --config /path/to/config

# Override log level
python3 triggers/manual.py --log-level DEBUG
```

### Scheduled Execution (Cron)

```bash
# Add to crontab
*/15 * * * * cd /app && python3 triggers/scheduled.py
```

### qBittorrent Webhooks

Configure in qBittorrent: **Tools → Options → Downloads**

**On torrent added:**
```
python3 /app/triggers/on_added.py "%I"
```

**On torrent completed:**
```
python3 /app/triggers/on_completed.py "%I"
```

Where `%I` is the torrent hash.

## Available Fields

### info.* (Core Torrent Data)
- `info.name`, `info.hash`, `info.state`, `info.category`, `info.tags`
- `info.size`, `info.progress`, `info.ratio`, `info.uploaded`, `info.downloaded`
- `info.dlspeed`, `info.upspeed`, `info.dl_limit`, `info.up_limit`
- `info.num_seeds`, `info.num_leechs`
- `info.added_on`, `info.completion_on`, `info.seeding_time`, `info.eta`
- `info.priority`, `info.auto_tmm`, `info.force_start`
- `info.save_path`, `info.content_path`

### trackers.* (Tracker Collection)
- `trackers.url`, `trackers.status`, `trackers.tier`
- `trackers.num_peers`, `trackers.num_seeds`, `trackers.msg`

### files.* (File Collection)
- `files.name`, `files.size`, `files.progress`, `files.priority`

### transfer.* (Global Stats)
- `transfer.dl_info_speed`, `transfer.up_info_speed`
- `transfer.dl_info_data`, `transfer.up_info_data`
- `transfer.connection_status`, `transfer.dht_nodes`

### app.* (Global Application Preferences)
- `app.save_path`, `app.temp_path`, `app.export_dir`
- `app.max_active_downloads`, `app.max_active_torrents`, `app.max_active_uploads`
- `app.dl_limit`, `app.up_limit` - Global speed limits
- `app.alt_dl_limit`, `app.alt_up_limit` - Alternative speed limits
- `app.max_connec`, `app.max_connec_per_torrent`
- `app.bittorrent_protocol`, `app.dht`, `app.pex`, `app.lsd`
- `app.encryption` - Connection encryption (0=prefer unencrypted, 1=prefer encrypted, 2=require encrypted)
- `app.anonymous_mode`, `app.proxy_type`, `app.proxy_ip`, `app.proxy_port`

## Available Operators

- **Equality:** `==`, `!=`
- **Comparison:** `>`, `<`, `>=`, `<=`
- **String:** `contains`, `not_contains`, `matches` (regex)
- **List:** `in`, `not_in`
- **Time:** `older_than`, `newer_than` (e.g., "30 days", "12 hours")

## Available Actions

- `stop` - Stop/pause torrent (qBittorrent v5.0+)
- `start` - Start/resume torrent (qBittorrent v5.0+)
- `force_start` - Force start torrent
- `recheck` - Recheck torrent files
- `reannounce` - Reannounce to trackers
- `delete_torrent` - Delete torrent (params: `keep_files`)
- `set_category` - Set category (params: `category`)
- `add_tag` - Add tags (params: `tags`)
- `remove_tag` - Remove tags (params: `tags`)
- `set_tags` - Replace all tags (params: `tags`)
- `set_upload_limit` - Set upload limit (params: `limit` in bytes/s, -1=unlimited)
- `set_download_limit` - Set download limit (params: `limit` in bytes/s, -1=unlimited)

## Error Handling

Errors are displayed in user-friendly format:

```
[AUTH-001] Cannot connect to qBittorrent
  • Host: http://localhost:8080
  • Problem: Invalid username or password
  • Fix: Check QBITTORRENT_USER and QBITTORRENT_PASS environment variables
```

No Python stack traces in normal operation.

## Migration from Old Format

Old format (field without prefix):
```yaml
- field: name
  operator: contains
  value: "1080p"
```

New format (field with API prefix):
```yaml
- field: info.name
  operator: contains
  value: "1080p"
```

Old format (special tracker syntax):
```yaml
trackers:
  any_match:
    - field: url
      operator: contains
      value: .private
```

New format (consistent syntax):
```yaml
all:
  - field: trackers.url
    operator: contains
    value: .private
```

## Testing

Always test rules with dry-run mode first:

```bash
python3 triggers/manual.py --dry-run --log-level DEBUG
```

Check logs at `/config/logs/qbittorrent.log` (or `<CONFIG_DIR>/logs/qbittorrent.log` on bare metal)

## Troubleshooting

### Log Path Issues

**Problem:** `[ERR-999] Permission denied: '/config'` or `[LOG-001] Cannot setup file logging`

**Cause:** Default log path is not writable

**Solution 1: Use CONFIG_DIR (Recommended for bare metal)**
```bash
CONFIG_DIR=./config ./triggers/manual.py
# Logs to: ./config/logs/qbittorrent.log
```

**Solution 2: Set Custom Log Path**
```bash
LOG_FILE=./my-logs/qbittorrent.log ./triggers/manual.py
# Logs to: ./my-logs/qbittorrent.log
```

**Solution 3: Console-Only Logging**
The system automatically falls back to console-only logging if file logging fails. You'll see:
```
[LOG-001] Cannot setup file logging: Permission denied
Continuing with console-only logging
```

### Log Path Resolution

Log paths are resolved in this order:
1. `LOG_FILE` environment variable (highest priority)
2. `logging.file` in config.yml
3. Default: `logs/qbittorrent.log` (relative to CONFIG_DIR)

**Relative paths** are relative to CONFIG_DIR:
```yaml
# config.yml
logging:
  file: logs/qbittorrent.log  # → <CONFIG_DIR>/logs/qbittorrent.log
```

**Absolute paths** are used as-is:
```yaml
# config.yml
logging:
  file: /var/log/qbittorrent.log  # → /var/log/qbittorrent.log
```

### Running on Bare Metal

```bash
# Set CONFIG_DIR to local directory
export CONFIG_DIR=./config
export QBITTORRENT_USER=your_username
export QBITTORRENT_PASS=your_password

# Run manually
./triggers/manual.py

# Logs will be in ./config/logs/qbittorrent.log
```

### Running in Docker

```bash
# CONFIG_DIR defaults to /config (mounted volume)
python3 triggers/manual.py

# Logs will be in /config/logs/qbittorrent.log
```

### Common Error Codes

- **[AUTH-001]** - Cannot authenticate with qBittorrent
  - Fix: Check QBITTORRENT_USER and QBITTORRENT_PASS

- **[CONN-001]** - Cannot reach qBittorrent server
  - Fix: Check QBITTORRENT_HOST and verify qBittorrent is running

- **[CFG-001]** - Cannot load configuration file
  - Fix: Check config.yml syntax and file permissions

- **[LOG-001]** - Cannot setup file logging
  - Fix: Check LOG_FILE path or set CONFIG_DIR to writable location

- **[FIELD-001]** - Invalid field reference
  - Fix: Use dot notation (e.g., info.name, trackers.url)

- **[ERR-999]** - Unexpected error
  - Fix: Check logs with --log-level DEBUG for details

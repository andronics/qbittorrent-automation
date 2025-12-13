# qbt-rules

A powerful Python-based rules engine for automating torrent management in qBittorrent using declarative YAML configuration.

[![GitHub Release](https://img.shields.io/github/v/release/andronics/qbt-rules)](https://github.com/andronics/qbt-rules/releases)
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)

---

## What is qbt-rules?

qbt-rules is a Python-based rules engine that automates torrent management through the qBittorrent Web API v5.0+. Define YAML-based rules to automatically categorize, tag, pause, resume, delete, and manage torrents based on flexible conditions.

**Key Features:**

- **Declarative YAML Rules** - No coding required, just write rules
- **Multiple Trigger Types** - Manual, scheduled (cron), webhooks (on_added, on_completed)
- **Powerful Conditions** - Complex logic with AND/OR/NOT groups, 17+ operators
- **Rich Field Access** - Dot notation access to all torrent metadata (info.*, trackers.*, files.*, etc.)
- **Idempotent Actions** - Safe to run repeatedly, actions skip if already applied
- **Dry-Run Mode** - Test rules without making changes
- **Comprehensive Logging** - Trace mode for debugging

---

## Quick Start

### Installation

**Option 1: Install from PyPI (recommended)**

```bash
# Install the package
pip install qbt-rules

# Create config directory
mkdir -p ~/.config/qbt-rules

# Download example configs
curl -o ~/.config/qbt-rules/config.yml \
  https://raw.githubusercontent.com/andronics/qbt-rules/main/config/config.example.yml
curl -o ~/.config/qbt-rules/rules.yml \
  https://raw.githubusercontent.com/andronics/qbt-rules/main/config/rules.example.yml

# Edit config with your qBittorrent credentials
nano ~/.config/qbt-rules/config.yml
```

**Option 2: Install from source**

```bash
# Clone the repository
git clone https://github.com/andronics/qbt-rules.git
cd qbt-rules

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Copy example configs
cp config/config.example.yml config/config.yml
cp config/rules.example.yml config/rules.yml

# Edit config with your qBittorrent credentials
nano config/config.yml
```

### Your First Rule

Create a simple rule in `config/rules.yml`:

```yaml
rules:
  - name: "Auto-categorize HD movies"
    enabled: true
    stop_on_match: true
    conditions:
      trigger: on_added
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
          tag: "movies"
```

### Run It

**Using console script (after pip install):**

```bash
# Test with dry-run (shows what would happen)
qbt-rules --dry-run

# Apply rules (defaults to manual trigger)
qbt-rules

# Enable trace logging for debugging
qbt-rules --trace

# Run with specific trigger
qbt-rules --trigger scheduled

# Process specific torrent
qbt-rules --trigger on_completed --torrent-hash abc123...
```

**Using Python module:**

```bash
python -m qbt_rules.cli --dry-run
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    TRIGGER ACTIVATION                       │
│  (Manual, Scheduled, on_added, on_completed)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FETCH TORRENTS FROM qBittorrent               │
│         (Optional: Apply filters by category/state)         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FOR EACH TORRENT:                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Evaluate Rules in File Order                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Check Conditions (all/any/none groups)        │  │  │
│  │  │  ├─ Access fields (info.*, trackers.*, etc.)   │  │  │
│  │  │  ├─ Apply operators (==, >, contains, etc.)    │  │  │
│  │  │  └─ Combine with AND/OR/NOT logic             │  │  │
│  │  └────────────┬───────────────────────────────────┘  │  │
│  │               │                                       │  │
│  │               ├─ Match? ──► Execute Actions          │  │
│  │               │             (stop, categorize, etc.)  │  │
│  │               │                                       │  │
│  │               └─ No Match? ──► Next Rule             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Rules execute top-to-bottom.** Use `stop_on_match: true` to prevent later rules from running after a match.

---

## Core Concepts

### Triggers

| Trigger | Description | Use Case |
|---------|-------------|----------|
| **manual** | Run on-demand via CLI | Testing, one-time bulk operations |
| **scheduled** | Run by cron/systemd timer | Regular cleanup, maintenance |
| **on_added** | Webhook when torrent added | Auto-categorize new downloads |
| **on_completed** | Webhook when download completes | Post-processing, seeding rules |

**[📖 Detailed Trigger Documentation](https://github.com/andronics/qbt-rules/wiki/Triggers)**

### Conditions

Combine conditions with logical groups:

- **all** - AND logic (all conditions must match)
- **any** - OR logic (at least one condition must match)
- **none** - NOT logic (no conditions can match)

**Available Operators:**

`==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `not_contains`, `matches`, `in`, `not_in`, `older_than`, `newer_than`, `smaller_than`, `larger_than`

**[📖 Detailed Condition Documentation](https://github.com/andronics/qbt-rules/wiki/Conditions)**

### Available Fields

Access torrent data using dot notation across 8 API categories:

| Prefix | Description | Example Fields |
|--------|-------------|----------------|
| `info.*` | Main torrent info | `info.name`, `info.size`, `info.ratio`, `info.state` |
| `trackers.*` | Tracker data (collection) | `trackers.url`, `trackers.status`, `trackers.msg` |
| `files.*` | File list (collection) | `files.name`, `files.size`, `files.progress` |
| `properties.*` | Extended properties | `properties.save_path`, `properties.comment` |
| `transfer.*` | Global transfer stats | `transfer.dl_speed_global`, `transfer.up_speed_global` |
| `app.*` | Application info | `app.version`, `app.api_version` |
| `peers.*` | Peer data (collection) | `peers.ip`, `peers.client`, `peers.progress` |
| `webseeds.*` | Web seed data (collection) | `webseeds.url` |

**[📖 Complete Field Reference](https://github.com/andronics/qbt-rules/wiki/Available-Fields)**

### Actions

Execute one or more actions when conditions match:

| Action | Description |
|--------|-------------|
| `stop` / `start` / `force_start` | Control torrent state |
| `recheck` / `reannounce` | Maintenance operations |
| `delete_torrent` | Remove torrent (optionally with files) |
| `set_category` | Set torrent category |
| `add_tag` / `remove_tag` / `set_tags` | Manage tags |
| `set_upload_limit` / `set_download_limit` | Speed limiting |

**[📖 Detailed Action Documentation](https://github.com/andronics/qbt-rules/wiki/Actions)**

---

## Example Rules

### Auto-Categorize by Content Type

```yaml
- name: "Categorize TV shows"
  enabled: true
  stop_on_match: true
  conditions:
    trigger: on_added
    all:
      - field: info.name
        operator: matches
        value: '(?i).*[Ss]\d{2}[Ee]\d{2}.*'
  actions:
    - type: set_category
      params:
        category: "TV-Shows"
```

### Cleanup Old Completed Torrents

```yaml
- name: "Delete old seeded torrents"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: info.state
        operator: in
        value: ["uploading", "pausedUP", "stalledUP"]
      - field: info.completion_on
        operator: older_than
        value: 2592000  # 30 days
      - field: info.ratio
        operator: ">="
        value: 2.0
  actions:
    - type: delete_torrent
      params:
        delete_files: false
```

### Force Seed Low-Seeded Content

```yaml
- name: "Force start underseded torrents"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: info.num_complete
        operator: "<="
        value: 2
      - field: info.state
        operator: in
        value: ["pausedUP", "stalledUP"]
  actions:
    - type: force_start
```

### Pause Large Downloads

```yaml
- name: "Pause very large downloads"
  enabled: true
  conditions:
    trigger: on_added
    all:
      - field: info.size
        operator: larger_than
        value: "50 GB"
      - field: info.state
        operator: in
        value: ["downloading", "metaDL"]
  actions:
    - type: stop
    - type: add_tag
      params:
        tag: "large-download"
```

**[📖 More Examples](https://github.com/andronics/qbt-rules/wiki/Examples)**

---

## Deployment

### Scheduled Execution with Cron

```bash
# Run every hour
0 * * * * qbt-rules --trigger scheduled

# Run daily at 3 AM
0 3 * * * qbt-rules --trigger scheduled

# Custom trigger at midnight
0 0 * * * qbt-rules --trigger nightly_cleanup
```

### Systemd Timer

Create `/etc/systemd/system/qbt-rules.service`:

```ini
[Unit]
Description=qbt-rules - qBittorrent Automation
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/qbt-rules --trigger scheduled
User=qbittorrent
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
```

Create `/etc/systemd/system/qbt-rules.timer`:

```ini
[Unit]
Description=Run qbt-rules hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable qbt-rules.timer
sudo systemctl start qbt-rules.timer
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install the package
RUN pip install qbt-rules

# Copy configuration files
COPY config/ /app/config/

# Run scheduled trigger every hour
CMD ["sh", "-c", "while true; do qbt-rules --trigger scheduled; sleep 3600; done"]
```

**[📖 Deployment Guide](https://github.com/andronics/qbt-rules/wiki/Deployment)**

---

## Documentation

**Complete documentation is available on the [GitHub Wiki](https://github.com/andronics/qbt-rules/wiki):**

- **[Getting Started](https://github.com/andronics/qbt-rules/wiki/Quick-Start)** - Installation and first rule
- **[Configuration Reference](https://github.com/andronics/qbt-rules/wiki/Configuration)** - config.yml and rules.yml
- **[Rules Architecture](https://github.com/andronics/qbt-rules/wiki/Rules-Architecture)** - How rules are evaluated
- **[Triggers](https://github.com/andronics/qbt-rules/wiki/Triggers)** - Manual, scheduled, webhooks
- **[Conditions](https://github.com/andronics/qbt-rules/wiki/Conditions)** - Operators and logical groups
- **[Available Fields](https://github.com/andronics/qbt-rules/wiki/Available-Fields)** - Complete field reference
- **[Actions](https://github.com/andronics/qbt-rules/wiki/Actions)** - All available actions
- **[Examples](https://github.com/andronics/qbt-rules/wiki/Examples)** - Real-world use cases
- **[FAQ](https://github.com/andronics/qbt-rules/wiki/FAQ)** - Common questions
- **[Troubleshooting](https://github.com/andronics/qbt-rules/wiki/Troubleshooting)** - Debug and fix issues
- **[Advanced Topics](https://github.com/andronics/qbt-rules/wiki/Advanced-Topics)** - Performance, security, extending

---

## Requirements

- **Python 3.8+**
- **qBittorrent v5.0+** with Web UI enabled
- **Dependencies:** `requests`, `pyyaml`

---

## Contributing

Contributions are welcome! Please see the [Contributing Guide](https://github.com/andronics/qbt-rules/wiki/Contributing) on the wiki.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

**Latest Release:** [v0.3.0](https://github.com/andronics/qbt-rules/releases/tag/v0.3.0) - 2024-12-13

---

## License

This project is released into the **public domain** under the [Unlicense](http://unlicense.org/).

You are free to use, modify, and distribute this software for any purpose without attribution.

---

**Happy automating! 🚀**

For detailed documentation, visit the [GitHub Wiki](https://github.com/andronics/qbt-rules/wiki).

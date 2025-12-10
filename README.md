# qBittorrent Automation

A powerful Python-based rules engine for automating torrent management in qBittorrent using declarative YAML configuration.

## Table of Contents

- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [In-Depth Configuration](#in-depth-configuration)
- [Rules Architecture](#rules-architecture)
- [Triggers](#triggers)
- [Conditions](#conditions)
- [Available Fields](#available-fields)
- [Actions](#actions)
- [Examples](#examples)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)
- [Contributing](#contributing)
- [License](#license)
- [Changelog](#changelog)

---

## Introduction

### What is qBittorrent Automation?

qBittorrent Automation is a Python-based rules engine that automates torrent management through the qBittorrent Web API v5.0+. It allows you to define declarative rules in YAML format that automatically organize, manage, and maintain your torrents based on custom conditions—no manual intervention required once configured.

### Why Use This?

**Save Time & Effort:**
- Automatically categorize torrents based on content patterns (movies, TV shows, resolution)
- Clean up old or completed torrents to save disk space
- Tag and organize torrents from specific trackers
- Enforce ratio requirements for private trackers
- Block unwanted content immediately upon arrival
- Manage bandwidth limits dynamically based on conditions
- Handle hundreds of torrents without manual work

**Flexible & Powerful:**
- Declarative YAML configuration (no coding required)
- Rich condition operators (equality, comparison, regex, time-based)
- Access to 8 different qBittorrent API endpoint categories
- Multiple trigger types (manual, scheduled, webhooks)
- Dry-run mode for safe testing
- Idempotent actions prevent unnecessary operations

### Key Features

✅ **Declarative YAML Configuration** - Define rules in easy-to-read YAML files
✅ **Multiple Trigger Types** - Manual CLI, scheduled cron, or real-time webhooks
✅ **Rich Condition Operators** - Equality, comparison, regex, time-based, list operations
✅ **Dot Notation Field Access** - Access 8 API categories: info, trackers, files, peers, properties, webseeds, transfer, app
✅ **File-Order Execution** - Rules execute top-to-bottom for predictable behavior
✅ **Idempotent Actions** - Smart skipping prevents redundant operations
✅ **Dry-Run Mode** - Test rules safely without making changes
✅ **Comprehensive Logging** - Detailed logs with optional trace mode
✅ **User-Friendly Errors** - Clear error messages with fix suggestions
✅ **Docker Ready** - Includes Docker configuration for easy deployment
✅ **qBittorrent v5.0+ Support** - Uses latest API endpoints

### Requirements

- **Python:** 3.8 or higher
- **qBittorrent:** 5.0 or higher with Web UI enabled
- **Dependencies:** PyYAML, requests
- **System:** Linux, macOS, Windows (or Docker)

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/qbittorrent-automation.git
cd qbittorrent-automation

# Install Python dependencies
pip install requests pyyaml

# Copy example configurations
cp config/config.example.yml config/config.yml
cp config/rules.example.yml config/rules.yml
```

### Basic Configuration

1. **Set qBittorrent Connection**

   Edit `config/config.yml` or set environment variables:

   ```bash
   export QBITTORRENT_HOST="http://localhost:8080"
   export QBITTORRENT_USER="admin"
   export QBITTORRENT_PASS="your_password"
   ```

2. **Enable qBittorrent Web UI**

   - Open qBittorrent → Tools → Options → Web UI
   - Check "Web User Interface (Remote control)"
   - Set username and password
   - Note the port (default: 8080)

### Your First Rule

Let's create a simple rule to auto-categorize HD movies.

**Edit `config/rules.yml`:**

```yaml
rules:
  - name: "Auto-categorize HD movies"
    enabled: true
    stop_on_match: false
    conditions:
      all:
        - field: info.name
          operator: matches
          value: '(?i).*(1080p|2160p|4k).*'
        - field: info.category
          operator: ==
          value: ""
    actions:
      - type: set_category
        params:
          category: movies-hd
      - type: add_tag
        params:
          tags:
            - hd
            - auto-categorized
```

**What this rule does:**
1. **Matches:** Torrents with "1080p", "2160p", or "4k" in the name (case-insensitive)
2. **AND:** Currently have no category assigned
3. **Actions:** Sets category to "movies-hd" and adds tags

**Important:** Create the "movies-hd" category in qBittorrent first!

### Testing Your Setup

**Dry-run mode** (see what would happen without making changes):

```bash
python3 triggers/manual.py --dry-run
```

**Expected output:**
```
2024-12-10 12:00:00 | INFO     | Successfully authenticated with qBittorrent
2024-12-10 12:00:00 | INFO     | Loaded 1 rules (execute in file order)
2024-12-10 12:00:00 | INFO     | Would set_category Movie.2160p.BluRay to movies-hd (params={'category': 'movies-hd'})
2024-12-10 12:00:00 | INFO     | Would add_tag Movie.2160p.BluRay (params={'tags': ['hd', 'auto-categorized']})
2024-12-10 12:00:00 | INFO     | Rule 'Auto-categorize HD movies' matched 1 torrent(s)
```

**Run for real** (remove `--dry-run`):

```bash
python3 triggers/manual.py
```

**Other useful commands:**

```bash
# Validate rules syntax
python3 triggers/manual.py --validate

# List all enabled rules
python3 triggers/manual.py --list-rules

# Debug with verbose logging
python3 triggers/manual.py --dry-run --log-level DEBUG
```

Congratulations! You've created your first automation rule. Continue reading for comprehensive documentation.

---

## In-Depth Configuration

### config.yml Reference

The `config.yml` file contains connection settings, logging configuration, and engine options.

| Section | Parameter | Type | Default | Description |
|---------|-----------|------|---------|-------------|
| **qbittorrent** | `host` | string | `http://localhost:8080` | qBittorrent Web UI URL |
| | `user` | string | `admin` | Username for authentication |
| | `pass` | string | *(required)* | Password (supports env vars) |
| **logging** | `level` | string | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |
| | `file` | string | `logs/qbittorrent.log` | Log file path (relative to CONFIG_DIR) |
| | `trace_mode` | boolean | `false` | Include module/function/line in logs |
| **engine** | `dry_run` | boolean | `false` | Test mode without executing actions |

**Example config.yml:**

```yaml
# qBittorrent connection settings
qbittorrent:
  host: ${QBITTORRENT_HOST:-http://localhost:8080}
  user: ${QBITTORRENT_USER:-admin}
  pass: ${QBITTORRENT_PASS}

# Logging configuration
logging:
  level: ${LOG_LEVEL:-INFO}
  file: ${LOG_FILE:-logs/qbittorrent.log}
  trace_mode: ${TRACE_MODE:-false}

# Engine settings
engine:
  dry_run: ${DRY_RUN:-false}
```

### Environment Variable Expansion

Config files support environment variable expansion using the syntax:

```yaml
parameter: ${VARIABLE_NAME:-default_value}
```

**Behavior:**
- If `VARIABLE_NAME` is set → uses its value
- If `VARIABLE_NAME` is not set → uses `default_value`
- If `VARIABLE_NAME` is not set and no default → empty string

**Precedence:**
1. Environment variable (highest priority)
2. Config file default value
3. Empty string

**Examples:**

```yaml
# Use environment variable, fallback to localhost
host: ${QBITTORRENT_HOST:-http://localhost:8080}

# Required environment variable (no default)
pass: ${QBITTORRENT_PASS}

# Boolean from environment
dry_run: ${DRY_RUN:-false}
```

### rules.yml Reference

The `rules.yml` file defines automation rules. Rules execute in **file order** (top to bottom).

**Rule Structure:**

```yaml
rules:
  - name: "Descriptive rule name"
    enabled: true
    stop_on_match: false
    conditions:
      trigger: manual  # Optional: filter by trigger type
      all: []   # All conditions must match (AND)
      any: []   # Any condition must match (OR)
      none: []  # No conditions can match (NOT)
    actions:
      - type: action_name
        params: {}
```

**Field Reference:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Human-readable rule name for logs |
| `enabled` | boolean | Yes | - | Set to `false` to disable rule |
| `stop_on_match` | boolean | Yes | `false` | If true, matched torrents skip remaining rules |
| `conditions` | object | Yes | - | Conditions object (see below) |
| `actions` | list | Yes | - | List of actions to execute |

**Conditions Object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trigger` | string or list | No | Filter rule by trigger type(s) |
| `all` | list | No | All conditions must be true (AND) |
| `any` | list | No | At least one condition must be true (OR) |
| `none` | list | No | No conditions can be true (NOT) |

**Condition Item:**

```yaml
- field: info.name
  operator: contains
  value: "1080p"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `field` | string | Yes | Dot notation field path (e.g., `info.name`, `trackers.url`) |
| `operator` | string | Yes | Comparison operator (see Operators section) |
| `value` | any | Yes | Value to compare against |

**Action Item:**

```yaml
- type: set_category
  params:
    category: movies
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Action name (see Actions section) |
| `params` | object | No | Action-specific parameters |

### Key Concepts

#### File Order Execution

Rules execute **top to bottom** in the order they appear in `rules.yml`. This provides predictable, easy-to-understand behavior.

**Best Practice:**
- **Top:** Blocking/filtering rules with `stop_on_match: true`
- **Middle:** Categorization and tagging rules
- **Bottom:** Cleanup and maintenance rules

**Example:**

```yaml
rules:
  # 1. Block unwanted content first (stops further processing)
  - name: "Block archives"
    stop_on_match: true
    # ...

  # 2. Then categorize
  - name: "Categorize movies"
    # ...

  # 3. Finally cleanup
  - name: "Remove old completed"
    # ...
```

#### stop_on_match Behavior

When `stop_on_match: true` and a torrent matches the rule:
- The rule's actions execute on that torrent
- That torrent **skips all remaining rules** in the current execution
- Other torrents continue processing normally

**Use Cases:**
- Content filtering (block unwanted, skip other rules)
- Mutually exclusive categorization
- Early exit for special cases

**Example:**

```yaml
rules:
  - name: "Block unwanted"
    stop_on_match: true  # Matched torrents stop here
    conditions:
      any:
        - field: info.name
          operator: contains
          value: "unwanted"
    actions:
      - type: stop

  - name: "Categorize all"  # Blocked torrents never reach this rule
    # ...
```

#### Empty Condition Groups

Empty condition groups are **ignored** (treated as always true):

```yaml
conditions:
  all:  # Empty - ignored
  any:
    - field: info.ratio
      operator: ">"
      value: 2.0
  # Effectively: any conditions must match
```

If **all groups are empty**, the rule matches **all torrents**:

```yaml
conditions: {}  # Matches everything
```

---

## Rules Architecture

### Execution Flow

```
┌─────────────────────────────────────────┐
│ Trigger Execution                        │
│ (manual/scheduled/on_added/on_completed) │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Load Torrent(s)                          │
│ • All torrents (manual/scheduled)        │
│ • Single torrent (webhooks)              │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Load Rules (config/rules.yml)            │
│ Rules execute in file order              │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │ For Each Rule:          │
    │ 1. Check if enabled     │
    │ 2. Check trigger filter │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │ For Each Torrent:       │
    └────────────┬────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Evaluate Conditions                      │
│ 1. Check "all" group (AND)               │
│ 2. Check "any" group (OR)                │
│ 3. Check "none" group (NOT)              │
│ All groups must pass                     │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │   Matched?      │
        └────────┬────────┘
          Yes ◄──┴──► No
           │          │
           ▼          ▼
    ┌──────────┐   Continue
    │ Execute  │   to next
    │ Actions  │   torrent
    └─────┬────┘
          │
          ▼
    ┌──────────────┐
    │ stop_on_match│
    │   = true?    │
    └──────┬───────┘
      Yes  │  No
      Skip │  Continue
      this │  rules for
      torrent  this torrent
```

### Condition Evaluation Logic

Rules support three logical groups that can be combined:

- **`all`:** Every condition in the list must be true (**AND** logic)
- **`any`:** At least one condition must be true (**OR** logic)
- **`none`:** No conditions can be true (**NOT** logic)

**Evaluation Order:**
1. All three groups are evaluated independently
2. The rule matches only if **all groups pass**
3. Empty/missing groups are skipped (treated as pass)

**Examples:**

```yaml
# Only "all" group
conditions:
  all:
    - field: info.ratio
      operator: ">="
      value: 2.0
    - field: info.state
      operator: ==
      value: uploading
# Result: ratio >= 2.0 AND state = uploading
```

```yaml
# Only "any" group
conditions:
  any:
    - field: info.state
      operator: ==
      value: error
    - field: info.state
      operator: ==
      value: missingFiles
# Result: state = error OR state = missingFiles
```

```yaml
# Combining groups
conditions:
  all:
    - field: info.ratio
      operator: ">="
      value: 2.0
  none:
    - field: info.category
      operator: ==
      value: keep
# Result: (ratio >= 2.0) AND NOT (category = keep)
```

```yaml
# Complex combination
conditions:
  all:
    - field: info.size
      operator: ">"
      value: 10737418240  # 10 GB
  any:
    - field: info.name
      operator: contains
      value: "1080p"
    - field: info.name
      operator: contains
      value: "2160p"
  none:
    - field: info.category
      operator: in
      value: [keep, seedbox]
# Result: (size > 10GB) AND (name has 1080p OR 2160p) AND NOT (category in [keep, seedbox])
```

### Field Resolution & Caching

The engine uses **dot notation** to access different qBittorrent API endpoints efficiently.

**Dot Notation Format:** `endpoint.property`

**Examples:**
- `info.name` → Torrent name from torrents/info endpoint
- `trackers.url` → Tracker URLs from torrents/trackers endpoint
- `files.name` → File names from torrents/files endpoint

**API Call Patterns:**

| Field Category | API Endpoint | When Called | Cache Scope | Cost |
|----------------|--------------|-------------|-------------|------|
| `info.*` | /torrents/info | Pre-loaded | Per execution | **Free** |
| `trackers.*` | /torrents/trackers | First use per torrent | Per execution | 1 call/torrent |
| `files.*` | /torrents/files | First use per torrent | Per execution | 1 call/torrent |
| `peers.*` | /sync/torrentPeers | First use per torrent | Per execution | 1 call/torrent |
| `properties.*` | /torrents/properties | First use per torrent | Per execution | 1 call/torrent |
| `webseeds.*` | /torrents/webseeds | First use per torrent | Per execution | 1 call/torrent |
| `transfer.*` | /transfer/info | First use (global) | Per execution | 1 call total |
| `app.*` | /app/preferences | First use (global) | Per execution | 1 call total |

**Caching Behavior:**
- **info.***: Already loaded, zero cost
- **Per-torrent fields**: Called once per torrent, then cached for that execution
- **Global fields**: Called once total, shared across all torrents

**Performance Tips:**
- Use `info.*` fields whenever possible (free)
- Avoid expensive fields (`files.*`, `trackers.*`) in high-frequency webhooks
- Global fields (`transfer.*`, `app.*`) are cheap to use

**Collection Field Behavior:**

Some fields return **lists** (collections):
- `trackers.*` - List of trackers
- `files.*` - List of files
- `peers.*` - List of peers
- `webseeds.*` - List of web seeds

**Operators check if ANY item matches:**

```yaml
- field: trackers.url
  operator: contains
  value: ".private"
# Returns TRUE if ANY tracker URL contains ".private"
```

```yaml
- field: files.name
  operator: matches
  value: '(?i)\.rar$'
# Returns TRUE if ANY file name ends with .rar
```

---

## Triggers

Triggers determine **when** and **how** rules execute.

### Overview

| Trigger | Use Case | Execution Method | Torrent Scope | Best For |
|---------|----------|------------------|---------------|----------|
| **manual** | Testing, one-off operations | CLI command | All torrents | Development, troubleshooting |
| **scheduled** | Periodic maintenance | Cron job | All torrents | Cleanup, ratio enforcement |
| **on_added** | React to new torrents | qBittorrent webhook | Single torrent | Content filtering, auto-categorization |
| **on_completed** | React to finished downloads | qBittorrent webhook | Single torrent | Post-download actions, seeding rules |

### Manual Trigger

**Description:** Direct execution from command line. Ideal for testing rules, debugging issues, and performing one-off operations.

**Script:** `triggers/manual.py`

**Usage:**

```bash
# Run all rules against all torrents
python3 triggers/manual.py

# Dry-run mode (show what would happen, make no changes)
python3 triggers/manual.py --dry-run

# Custom config directory
python3 triggers/manual.py --config-dir /path/to/config

# Override log level
python3 triggers/manual.py --log-level DEBUG

# Enable trace mode (detailed logging with module/function/line)
python3 triggers/manual.py --trace

# Validate rules syntax without execution
python3 triggers/manual.py --validate

# List all enabled rules
python3 triggers/manual.py --list-rules

# Show version
python3 triggers/manual.py --version

# Combine flags
python3 triggers/manual.py --dry-run --log-level DEBUG --trace
```

**When to Use:**
- **Testing new rules** before scheduling them
- **Debugging** issues with verbose logging
- **Manual cleanup** operations (e.g., after bulk adding torrents)
- **Validating** configuration changes
- **Learning** how rules work with --dry-run

**Example Output:**

```
2024-12-10 12:00:00 | INFO     | Successfully authenticated with qBittorrent at http://localhost:8080
2024-12-10 12:00:00 | INFO     | ============================================================
2024-12-10 12:00:00 | INFO     | Starting qBittorrent automation engine
2024-12-10 12:00:00 | INFO     | Trigger: manual
2024-12-10 12:00:00 | INFO     | Dry run mode: True
2024-12-10 12:00:00 | INFO     | ============================================================
2024-12-10 12:00:00 | INFO     | Fetched 253 torrent(s)
2024-12-10 12:00:00 | INFO     | Loaded 5 rules (execute in file order)
2024-12-10 12:00:00 | INFO     | Processing rule: Auto-categorize HD movies
2024-12-10 12:00:00 | INFO     | Would set_category Movie.2160p.BluRay to movies-hd
2024-12-10 12:00:00 | INFO     | Rule 'Auto-categorize HD movies' matched 1 torrent(s)
2024-12-10 12:00:00 | INFO     | ============================================================
2024-12-10 12:00:00 | INFO     | Execution complete - Summary:
2024-12-10 12:00:00 | INFO     |   Total torrents: 253
2024-12-10 12:00:00 | INFO     |   Processed: 0
2024-12-10 12:00:00 | INFO     |   Rules matched: 1
2024-12-10 12:00:00 | INFO     |   Actions executed: 2
2024-12-10 12:00:00 | INFO     |   Actions skipped (idempotent): 0
2024-12-10 12:00:00 | INFO     | ============================================================
```

### Scheduled Trigger

**Description:** Automated execution via cron for periodic maintenance tasks.

**Script:** `triggers/scheduled.py`

**Setup:**

```bash
# Edit crontab
crontab -e

# Run every 15 minutes
*/15 * * * * cd /app && python3 /app/triggers/scheduled.py >> /var/log/qbt-automation.log 2>&1

# Run every hour
0 * * * * cd /app && python3 /app/triggers/scheduled.py

# Run daily at 3 AM
0 3 * * * cd /app && python3 /app/triggers/scheduled.py

# Run every 6 hours
0 */6 * * * cd /app && python3 /app/triggers/scheduled.py
```

**Docker Setup:**

Add to `docker-compose.yml`:

```yaml
services:
  qbittorrent-automation:
    image: qbittorrent-automation:latest
    volumes:
      - ./config:/config
    environment:
      - QBITTORRENT_HOST=http://qbittorrent:8080
      - QBITTORRENT_USER=admin
      - QBITTORRENT_PASS=password
    command: |
      sh -c 'while true; do
        python3 /app/triggers/scheduled.py
        sleep 900
      done'
```

Or use system cron with Docker exec:

```bash
# Run inside container every 15 minutes
*/15 * * * * docker exec qbittorrent-automation python3 /app/triggers/scheduled.py
```

**Best Practices:**
- **Interval:** 15-60 minutes for most use cases
- **Monitoring:** Direct output to log file for troubleshooting
- **Testing:** Run manually first to verify behavior
- **Dry-run:** Test with cron using --dry-run initially

**When to Use:**
- **Removing old/completed torrents** automatically
- **Enforcing ratio requirements** periodically
- **Bandwidth limit adjustments** based on time/conditions
- **Periodic reannounce** operations
- **Tagging torrents** based on age or status

**Example Rules for Scheduled:**

```yaml
rules:
  - name: "Remove old completed torrents"
    enabled: true
    conditions:
      trigger: [scheduled, manual]  # Run on schedule, allow manual testing
      all:
        - field: info.completion_on
          operator: older_than
          value: 30 days
        - field: info.ratio
          operator: ">="
          value: 1.0
    actions:
      - type: delete_torrent
        params:
          keep_files: false
```

### On Added Trigger (Webhook)

**Description:** Triggered immediately when qBittorrent adds a new torrent. Executes for a **single torrent** identified by hash.

**Script:** `triggers/on_added.py`

**qBittorrent Configuration:**

1. Open qBittorrent → **Tools** → **Options** → **Downloads**
2. Scroll to **"Run external program on torrent added"**
3. Check the box to enable
4. Set command:

**Bare Metal:**
```
python3 /path/to/qbittorrent-automation/triggers/on_added.py "%I"
```

**Docker:**
```
docker exec qbittorrent-automation python3 /app/triggers/on_added.py "%I"
```

Or if automation runs inside qBittorrent container:
```
python3 /config/scripts/triggers/on_added.py "%I"
```

**Important:** `%I` is qBittorrent's placeholder for torrent info hash (required)

**Usage in Rules:**

To make a rule execute **only** on the on_added trigger:

```yaml
conditions:
  trigger: on_added
  any:
    - field: info.name
      operator: contains
      value: "unwanted"
```

**Best Practices:**
- **Keep processing lightweight** - Only single torrent, but triggered frequently
- **Avoid expensive API calls** - Don't use `files.*` or `trackers.*` unless necessary
- **Use for immediate actions** - Categorization, tagging, filtering
- **Fast decisions** - Block unwanted content before download starts

**When to Use:**
- **Content filtering** - Block/stop unwanted torrents immediately
- **Auto-categorization** - Assign category based on name/tracker
- **Initial tagging** - Tag by tracker, content type, or name pattern
- **Download priority** - Set force_start for important torrents

**Example Rules for On Added:**

```yaml
# Block unwanted file types immediately
- name: "Block archive files on add"
  enabled: true
  stop_on_match: true
  conditions:
    trigger: on_added
    any:
      - field: files.name
        operator: matches
        value: '(?i)\.(rar|zip|7z)$'
  actions:
    - type: stop
    - type: add_tag
      params:
        tags:
          - blocked-archive
```

```yaml
# Auto-categorize by name pattern
- name: "Auto-categorize new movies"
  enabled: true
  conditions:
    trigger: on_added
    all:
      - field: info.name
        operator: matches
        value: '(?i).*(1080p|2160p).*'
  actions:
    - type: set_category
      params:
        category: movies-hd
```

**Troubleshooting:**
- **Not triggering?** Check qBittorrent logs for errors
- **Wrong path?** Ensure script path is absolute and accessible
- **Permission denied?** Make script executable: `chmod +x triggers/on_added.py`
- **Test manually:** `python3 triggers/on_added.py <torrent_hash>`

### On Completed Trigger (Webhook)

**Description:** Triggered when a torrent finishes downloading. Executes for a **single torrent** identified by hash.

**Script:** `triggers/on_completed.py`

**qBittorrent Configuration:**

1. Open qBittorrent → **Tools** → **Options** → **Downloads**
2. Scroll to **"Run external program on torrent completion"**
3. Check the box to enable
4. Set command:

**Bare Metal:**
```
python3 /path/to/qbittorrent-automation/triggers/on_completed.py "%I"
```

**Docker:**
```
docker exec qbittorrent-automation python3 /app/triggers/on_completed.py "%I"
```

Or if automation runs inside qBittorrent container:
```
python3 /config/scripts/triggers/on_completed.py "%I"
```

**Important:** `%I` is qBittorrent's placeholder for torrent info hash (required)

**Usage in Rules:**

```yaml
conditions:
  trigger: on_completed
  all:
    - field: info.size
      operator: ">"
      value: 1073741824  # > 1GB
```

**Best Practices:**
- **Post-download processing** - Trigger notifications, move files, update tags
- **Seeding strategy** - Apply upload limits, set ratio goals
- **Category migration** - Move from "downloading" to "completed" categories
- **Tracking** - Tag completed torrents for organization

**When to Use:**
- **Notifications** - Trigger external notification systems
- **Seeding rules** - Apply limits or force_start for ratio requirements
- **Category changes** - Move to "completed" or "seeding" categories
- **Upload limiting** - Throttle completed torrents to prioritize active downloads
- **Tagging** - Mark as completed for tracking

**Example Rules for On Completed:**

```yaml
# Tag large completed downloads
- name: "Tag large completed downloads"
  enabled: true
  conditions:
    trigger: on_completed
    all:
      - field: info.size
        operator: ">"
        value: 10737418240  # > 10GB
  actions:
    - type: add_tag
      params:
        tags:
          - completed-large
          - needs-seeding
```

```yaml
# Move to seeding category
- name: "Move completed to seeding"
  enabled: true
  conditions:
    trigger: on_completed
  actions:
    - type: set_category
      params:
        category: seeding
```

```yaml
# Limit upload speed for private tracker torrents
- name: "Limit upload on completion for private"
  enabled: true
  conditions:
    trigger: on_completed
    all:
      - field: trackers.url
        operator: contains
        value: ".private"
  actions:
    - type: set_upload_limit
      params:
        limit: 1048576  # 1 MB/s
```

**Troubleshooting:**
- **Not triggering?** Check qBittorrent logs
- **Fires multiple times?** qBittorrent may trigger on re-check or resume
- **Test manually:** `python3 triggers/on_completed.py <torrent_hash>`

### Trigger Filtering in Rules

You can filter rules to execute **only** on specific trigger types using the `trigger` field in conditions.

**Single Trigger:**

```yaml
conditions:
  trigger: on_added
  # This rule ONLY runs when on_added.py is executed
```

**Multiple Triggers:**

```yaml
conditions:
  trigger: [scheduled, manual]
  # This rule runs when scheduled.py OR manual.py is executed
  # Does NOT run for on_added or on_completed
```

**All Triggers (Default):**

```yaml
conditions:
  # No trigger field = runs on ALL trigger types
  all:
    - field: info.ratio
      operator: ">"
      value: 2.0
```

**Available Trigger Values:**
- `manual` - Manual CLI execution
- `scheduled` - Cron/scheduled execution
- `on_added` - Torrent added webhook
- `on_completed` - Torrent completed webhook

**Use Cases:**

```yaml
# Cleanup rules: Only run on schedule (not on every webhook)
- name: "Remove old torrents"
  conditions:
    trigger: [scheduled, manual]
    # ...

# Real-time filtering: Only on torrent added
- name: "Block unwanted content"
  conditions:
    trigger: on_added
    # ...

# Seeding rules: Only on completion
- name: "Set upload limits on completion"
  conditions:
    trigger: on_completed
    # ...

# Universal rules: No trigger filter (runs always)
- name: "Tag private tracker torrents"
  conditions:
    # Runs on ALL triggers
    all:
      - field: trackers.url
        operator: contains
        value: ".private"
```

---

## Conditions

Conditions determine which torrents match a rule. Three logical groups are available: `all`, `any`, and `none`.

### Overview

**Condition Groups:**

| Group | Logic | Description | Use When |
|-------|-------|-------------|----------|
| `all` | AND | Every condition must be true | Need multiple criteria simultaneously |
| `any` | OR | At least one condition must be true | Match alternatives or broad filtering |
| `none` | NOT | No conditions can be true | Exclusions or inverse matching |

**Combining Groups:**
- All three groups can be used together
- **All groups must pass** for the rule to match
- Empty/missing groups are ignored (treated as pass)

### ALL Conditions (AND Logic)

**Description:** Every condition in the `all` list must be true for the group to pass.

**Structure:**

```yaml
conditions:
  all:
    - field: info.name
      operator: contains
      value: "1080p"
    - field: info.category
      operator: ==
      value: ""
    - field: info.size
      operator: ">"
      value: 1073741824
# ALL three must be true: name has "1080p" AND no category AND size > 1GB
```

**Use Cases:**
- **Narrow down matches** - Require multiple criteria
- **Precise filtering** - All conditions must align
- **Most common pattern** - Default choice for most rules

**Examples:**

```yaml
# HD movies without category
conditions:
  all:
    - field: info.name
      operator: matches
      value: '(?i).*(1080p|2160p).*'
    - field: info.category
      operator: ==
      value: ""
```

```yaml
# Private tracker torrents over 2.0 ratio
conditions:
  all:
    - field: info.ratio
      operator: ">="
      value: 2.0
    - field: trackers.url
      operator: contains
      value: ".private"
```

```yaml
# Old completed torrents not in keep category
conditions:
  all:
    - field: info.completion_on
      operator: older_than
      value: 30 days
    - field: info.ratio
      operator: ">="
      value: 1.0
    - field: info.category
      operator: "!="
      value: keep
```

### ANY Conditions (OR Logic)

**Description:** At least one condition in the `any` list must be true for the group to pass.

**Structure:**

```yaml
conditions:
  any:
    - field: info.state
      operator: ==
      value: error
    - field: info.state
      operator: ==
      value: missingFiles
    - field: info.state
      operator: ==
      value: stalledDL
# ANY one must be true: state=error OR state=missingFiles OR state=stalledDL
```

**Use Cases:**
- **Match alternatives** - Multiple acceptable patterns
- **Broad filtering** - "Either this OR that"
- **List of exceptions** - Match any of several values

**Examples:**

```yaml
# Remove torrents in error states
conditions:
  any:
    - field: info.state
      operator: ==
      value: error
    - field: info.state
      operator: ==
      value: missingFiles
```

```yaml
# Match either 1080p or 2160p resolution
conditions:
  any:
    - field: info.name
      operator: contains
      value: "1080p"
    - field: info.name
      operator: contains
      value: "2160p"
```

```yaml
# Block multiple file extensions
conditions:
  any:
    - field: files.name
      operator: matches
      value: '(?i)\.rar$'
    - field: files.name
      operator: matches
      value: '(?i)\.zip$'
    - field: files.name
      operator: matches
      value: '(?i)\.7z$'
```

**Tip:** For list matching, use `in` operator instead:

```yaml
# Simpler alternative to above
conditions:
  any:
    - field: info.state
      operator: in
      value: [error, missingFiles, stalledDL]
```

### NONE Conditions (NOT Logic)

**Description:** No conditions in the `none` list can be true for the group to pass.

**Structure:**

```yaml
conditions:
  none:
    - field: info.category
      operator: in
      value: [keep, seedbox]
    - field: info.tags
      operator: contains
      value: "permanent"
# NONE can be true: NOT (category in [keep, seedbox]) AND NOT (has "permanent" tag)
```

**Use Cases:**
- **Exclusions** - Exclude specific cases
- **Inverse filtering** - "Everything except..."
- **"Unless" clauses** - Do action unless condition is true

**Examples:**

```yaml
# Delete old torrents NOT in keep category
conditions:
  all:
    - field: info.completion_on
      operator: older_than
      value: 30 days
  none:
    - field: info.category
      operator: ==
      value: keep
```

```yaml
# Apply limits EXCEPT to private trackers
conditions:
  all:
    - field: info.ratio
      operator: ">="
      value: 2.0
  none:
    - field: trackers.url
      operator: contains
      value: ".private"
```

```yaml
# Stop seeding UNLESS in seedbox category
conditions:
  all:
    - field: info.ratio
      operator: ">="
      value: 3.0
    - field: info.seeding_time
      operator: ">"
      value: 2592000  # 30 days
  none:
    - field: info.category
      operator: ==
      value: seedbox
```

### Combining Condition Groups

You can use multiple groups together. **All groups must pass** for the rule to match.

**Pattern 1: all + none ("Match these, except...")**

```yaml
conditions:
  all:
    - field: info.ratio
      operator: ">="
      value: 2.0
    - field: info.completion_on
      operator: older_than
      value: 7 days
  none:
    - field: info.category
      operator: in
      value: [keep, seedbox, long-term]
# Match: ratio >= 2.0 AND completed > 7 days ago
# Except: NOT in categories keep/seedbox/long-term
```

**Pattern 2: any + all ("Match any of these, but also require...")**

```yaml
conditions:
  any:
    - field: info.name
      operator: contains
      value: "1080p"
    - field: info.name
      operator: contains
      value: "2160p"
  all:
    - field: info.size
      operator: ">"
      value: 5368709120  # > 5GB
    - field: info.category
      operator: ==
      value: ""
# Match: (1080p OR 2160p) AND size > 5GB AND no category
```

**Pattern 3: all + any + none (Complex filtering)**

```yaml
conditions:
  all:
    - field: info.completion_on
      operator: older_than
      value: 14 days
  any:
    - field: info.ratio
      operator: ">="
      value: 3.0
    - field: info.num_leechs
      operator: ==
      value: 0
  none:
    - field: info.category
      operator: in
      value: [seedbox, permanent]
    - field: trackers.url
      operator: contains
      value: ".private"
# Match: completed > 14 days ago
#    AND (ratio >= 3.0 OR no leeches)
#    AND NOT (in seedbox/permanent categories)
#    AND NOT (private tracker)
```

### Operator Reference

**Equality Operators**

| Operator | Description | Value Types | Example |
|----------|-------------|-------------|---------|
| `==` | Exact match (equals) | string, number, boolean | `info.category == "movies"` |
| `!=` | Not equal | string, number, boolean | `info.state != "error"` |

**Comparison Operators**

| Operator | Description | Value Types | Example |
|----------|-------------|-------------|---------|
| `>` | Greater than | number | `info.ratio > 2.0` |
| `<` | Less than | number | `info.size < 1073741824` |
| `>=` | Greater than or equal | number | `info.ratio >= 1.0` |
| `<=` | Less than or equal | number | `info.progress <= 0.5` |

**String Operators**

| Operator | Description | Case Sensitive | Example |
|----------|-------------|----------------|---------|
| `contains` | Substring match | Yes | `info.name contains "1080p"` |
| `not_contains` | Does not contain | Yes | `info.name not_contains "sample"` |
| `matches` | Regex pattern match | Depends on regex | `info.name matches "(?i).*s\d{2}e\d{2}.*"` |

**List Operators**

| Operator | Description | Example |
|----------|-------------|---------|
| `in` | Value is in list | `info.state in ["error", "missingFiles"]` |
| `not_in` | Value is not in list | `info.category not_in ["keep", "seedbox"]` |

**Time Operators**

| Operator | Description | Value Format | Example |
|----------|-------------|--------------|---------|
| `older_than` | Unix timestamp older than | "N days" or "N hours" | `info.added_on older_than "30 days"` |
| `newer_than` | Unix timestamp newer than | "N days" or "N hours" | `info.completion_on newer_than "7 days"` |

**Time Value Formats:**
- Days: `"7 days"`, `"30 days"`, `"1 day"`
- Hours: `"12 hours"`, `"48 hours"`, `"1 hour"`
- Minutes: `"30 minutes"`, `"90 minutes"`, `"1 minute"`

**Operator Behavior with None/Missing Values:**

| Operator Type | Behavior when field is None/missing |
|---------------|-------------------------------------|
| `!=`, `not_in`, `not_contains` | Returns `true` |
| All others | Returns `false` |

**Collection Field Behavior:**

For collection fields (`trackers.*`, `files.*`, `peers.*`, `webseeds.*`):
- Operators check if **ANY item** in the collection matches
- Returns `true` if at least one item matches

**Examples:**

```yaml
# Equality
- field: info.category
  operator: ==
  value: "movies"

# Comparison
- field: info.ratio
  operator: ">="
  value: 2.0

# String contains
- field: info.name
  operator: contains
  value: "1080p"

# Regex (case-insensitive TV show pattern)
- field: info.name
  operator: matches
  value: '(?i).*s\d{2}e\d{2}.*'

# List membership
- field: info.state
  operator: in
  value: ["error", "missingFiles", "stalledDL"]

# Time-based (older than 30 days)
- field: info.added_on
  operator: older_than
  value: "30 days"

# Collection (ANY tracker contains ".private")
- field: trackers.url
  operator: contains
  value: ".private"
```

---

*Due to length constraints, this is Part 1 of the comprehensive README. Continue reading the next section for Available Fields, Actions, Examples, FAQ, and more.*

---

## Available Fields

### Field Categories Overview

qBittorrent Automation provides access to 8 different API endpoint categories through dot notation.

| Category | API Endpoint | API Calls | Cache Scope | Description |
|----------|--------------|-----------|-------------|-------------|
| `info.*` | /torrents/info | **Pre-loaded** (free) | Per execution | Core torrent data from main list |
| `trackers.*` | /torrents/trackers | 1 per torrent | Per execution | Tracker information (collection) |
| `files.*` | /torrents/files | 1 per torrent | Per execution | File list and details (collection) |
| `peers.*` | /sync/torrentPeers | 1 per torrent | Per execution | Connected peers (collection) |
| `properties.*` | /torrents/properties | 1 per torrent | Per execution | Extended torrent metadata |
| `webseeds.*` | /torrents/webseeds | 1 per torrent | Per execution | Web seed sources (collection) |
| `transfer.*` | /transfer/info | 1 total (global) | Per execution | Global transfer statistics |
| `app.*` | /app/preferences | 1 total (global) | Per execution | Application preferences |

**Performance Notes:**
- **info.***: Already loaded, use freely
- **Per-torrent fields**: Cached after first use for that torrent
- **Global fields**: Cached after first use, shared across all torrents
- **Collection fields** (trackers, files, peers, webseeds): Return lists, operators check ANY item

### info.* (Core Torrent Data)

**No additional API calls required - already loaded**

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `info.hash` | string | Torrent info hash (40-char hex) | `"8c9a6e4f3b2d1a..."` |
| `info.name` | string | Torrent name | `"Movie.2160p.BluRay"` |
| `info.state` | string | Current state | `downloading`, `uploading`, `stalledUP`, `stalledDL`, `pausedUP`, `pausedDL`, `queuedUP`, `queuedDL`, `checkingUP`, `checkingDL`, `error`, `missingFiles`, `metaDL` |
| `info.category` | string | Category name | `"movies"`, `""` (empty) |
| `info.tags` | string | Comma-separated tags | `"hd,private"`, `""` |
| `info.size` | integer | Total size in bytes | `1073741824` (1 GB) |
| `info.progress` | float | Download progress (0.0-1.0) | `0.75` (75%) |
| `info.dlspeed` | integer | Download speed (bytes/s) | `1048576` (1 MB/s) |
| `info.upspeed` | integer | Upload speed (bytes/s) | `524288` (512 KB/s) |
| `info.downloaded` | integer | Downloaded bytes | `1073741824` |
| `info.uploaded` | integer | Uploaded bytes | `2147483648` |
| `info.ratio` | float | Upload/download ratio | `2.0` |
| `info.dl_limit` | integer | Download limit (bytes/s, -1=unlimited) | `1048576`, `-1` |
| `info.up_limit` | integer | Upload limit (bytes/s, -1=unlimited) | `524288`, `-1` |
| `info.num_seeds` | integer | Connected seeds | `5` |
| `info.num_leechs` | integer | Connected leeches | `2` |
| `info.num_complete` | integer | Complete sources (from tracker) | `50` |
| `info.num_incomplete` | integer | Incomplete sources (from tracker) | `10` |
| `info.eta` | integer | Estimated time remaining (seconds) | `3600` (1 hour) |
| `info.seeding_time` | integer | Total seeding time (seconds) | `86400` (1 day) |
| `info.added_on` | integer | Unix timestamp when added | `1609459200` |
| `info.completion_on` | integer | Unix timestamp when completed | `1609545600`, `-1` (not completed) |
| `info.tracker` | string | Primary tracker URL | `"https://tracker.example.com"` |
| `info.save_path` | string | Save directory | `"/downloads/movies"` |
| `info.content_path` | string | Full path to content | `"/downloads/movies/Movie"` |
| `info.priority` | integer | Queue priority (1=highest, 8=lowest) | `1` |
| `info.auto_tmm` | boolean | Automatic Torrent Management enabled | `true`, `false` |
| `info.force_start` | boolean | Force start enabled | `true`, `false` |

**Common Use Cases:**

```yaml
# By state
- field: info.state
  operator: ==
  value: stalledUP

# By name pattern
- field: info.name
  operator: matches
  value: '(?i).*(1080p|2160p).*'

# By category
- field: info.category
  operator: ==
  value: ""  # No category

# By ratio
- field: info.ratio
  operator: ">="
  value: 2.0

# By age
- field: info.added_on
  operator: older_than
  value: "30 days"

# By size
- field: info.size
  operator: ">"
  value: 10737418240  # > 10GB

# By completion
- field: info.completion_on
  operator: "!="
  value: -1  # Has completed
```

### trackers.* (Tracker Collection)

**One API call per torrent (cached after first use)**

**Collection:** Returns list of values. Operators check if **ANY** tracker matches.

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `trackers.url` | string | Tracker announce URL | `"https://tracker.example.com/announce"` |
| `trackers.status` | integer | Tracker status code | `0`=disabled, `1`=not contacted, `2`=working, `3`=updating, `4`=not working |
| `trackers.tier` | integer | Tracker tier (failover priority) | `0`, `1`, `2`... |
| `trackers.num_peers` | integer | Peers reported by this tracker | `50` |
| `trackers.num_seeds` | integer | Seeds reported by this tracker | `30` |
| `trackers.num_leeches` | integer | Leeches reported by this tracker | `20` |
| `trackers.num_downloaded` | integer | Times downloaded (from tracker) | `1000` |
| `trackers.msg` | string | Tracker status message | `"Success"`, `"Unregistered"`, `"Not found"` |

**Collection Behavior:**

```yaml
# Returns TRUE if ANY tracker URL contains ".private"
- field: trackers.url
  operator: contains
  value: ".private"

# Returns TRUE if ANY tracker status is 4 (not working)
- field: trackers.status
  operator: ==
  value: 4
```

**Common Use Cases:**

```yaml
# Private tracker detection
- field: trackers.url
  operator: contains
  value: ".private"

# Specific tracker
- field: trackers.url
  operator: contains
  value: "tracker.example.com"

# Working trackers only
- field: trackers.status
  operator: ==
  value: 2

# Dead trackers
- field: trackers.status
  operator: in
  value: [0, 4]
```

### files.* (File Collection)

**One API call per torrent (cached after first use)**

**Collection:** Returns list of values. Operators check if **ANY** file matches.

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `files.name` | string | File path/name within torrent | `"Movie/movie.mkv"`, `"sample.avi"` |
| `files.size` | integer | File size in bytes | `1073741824` |
| `files.progress` | float | File download progress (0.0-1.0) | `0.95` |
| `files.priority` | integer | File priority | `0`=do not download, `1`=normal, `6`=high, `7`=maximum |
| `files.is_seed` | boolean | File is complete | `true`, `false` |
| `files.piece_range` | list[int] | Piece range [start, end] | `[0, 500]` |

**Collection Behavior:**

```yaml
# Returns TRUE if ANY file name ends with .rar
- field: files.name
  operator: matches
  value: '(?i)\.rar$'

# Returns TRUE if ANY file is larger than 10GB
- field: files.size
  operator: ">"
  value: 10737418240
```

**Common Use Cases:**

```yaml
# Block specific file extensions
- field: files.name
  operator: matches
  value: '(?i)\.(rar|zip|7z)$'

# Detect sample files
- field: files.name
  operator: contains
  value: "sample"

# Find large files
- field: files.size
  operator: ">"
  value: 5368709120  # > 5GB
```

### properties.* (Extended Properties)

**One API call per torrent (cached after first use)**

Contains extended metadata not available in `info.*`.

| Field | Type | Description |
|-------|------|-------------|
| `properties.save_path` | string | Save directory path |
| `properties.creation_date` | integer | Torrent creation timestamp |
| `properties.piece_size` | integer | Piece size in bytes |
| `properties.comment` | string | Torrent comment field |
| `properties.total_wasted` | integer | Wasted bytes (hash fails) |
| `properties.total_uploaded` | integer | Total uploaded bytes |
| `properties.total_downloaded` | integer | Total downloaded bytes |
| `properties.up_limit` | integer | Upload limit (bytes/s) |
| `properties.dl_limit` | integer | Download limit (bytes/s) |
| `properties.time_elapsed` | integer | Active time (seconds) |
| `properties.seeding_time` | integer | Seeding time (seconds) |
| `properties.nb_connections` | integer | Current connections |
| `properties.nb_connections_limit` | integer | Connection limit |
| `properties.share_ratio` | float | Share ratio |
| `properties.addition_date` | integer | Date added timestamp |
| `properties.completion_date` | integer | Date completed timestamp |
| `properties.created_by` | string | Torrent creator string |
| `properties.dl_speed_avg` | integer | Average download speed |
| `properties.dl_speed` | integer | Current download speed |
| `properties.eta` | integer | ETA in seconds |
| `properties.last_seen` | integer | Last seen complete timestamp |
| `properties.peers` | integer | Connected peers |
| `properties.peers_total` | integer | Total peers in swarm |
| `properties.pieces_have` | integer | Pieces downloaded |
| `properties.pieces_num` | integer | Total pieces |
| `properties.reannounce` | integer | Seconds until next reannounce |
| `properties.seeds` | integer | Connected seeds |
| `properties.seeds_total` | integer | Total seeds in swarm |
| `properties.total_size` | integer | Total size in bytes |
| `properties.up_speed_avg` | integer | Average upload speed |
| `properties.up_speed` | integer | Current upload speed |

**Note:** Most data overlaps with `info.*`. Use `properties.*` only when you need fields not available in `info.*`.

### transfer.* (Global Transfer Info)

**Single API call per execution (cached, shared across all torrents)**

Global transfer statistics for the entire qBittorrent instance.

| Field | Type | Description |
|-------|------|-------------|
| `transfer.dl_info_speed` | integer | Global download speed (bytes/s) |
| `transfer.up_info_speed` | integer | Global upload speed (bytes/s) |
| `transfer.dl_info_data` | integer | Session downloaded bytes |
| `transfer.up_info_data` | integer | Session uploaded bytes |
| `transfer.connection_status` | string | Connection status: `"connected"`, `"firewalled"`, `"disconnected"` |
| `transfer.dht_nodes` | integer | DHT nodes connected |

**Use Cases:**

```yaml
# Pause torrents if global speed maxed
- field: transfer.dl_info_speed
  operator: ">"
  value: 10485760  # > 10 MB/s

# Check connection before operations
- field: transfer.connection_status
  operator: ==
  value: "connected"
```

### app.* (Application Preferences)

**Single API call per execution (cached, shared across all torrents)**

qBittorrent application settings.

| Field | Type | Description |
|-------|------|-------------|
| `app.save_path` | string | Default save path |
| `app.temp_path` | string | Temp path for incomplete downloads |
| `app.temp_path_enabled` | boolean | Use temp path |
| `app.max_active_downloads` | integer | Max active downloads |
| `app.max_active_torrents` | integer | Max active torrents |
| `app.max_active_uploads` | integer | Max active uploads |
| `app.dl_limit` | integer | Global download limit (bytes/s, -1=unlimited) |
| `app.up_limit` | integer | Global upload limit (bytes/s, -1=unlimited) |
| `app.max_connec` | integer | Max global connections |
| `app.max_connec_per_torrent` | integer | Max connections per torrent |
| `app.dht` | boolean | DHT enabled |
| `app.pex` | boolean | Peer Exchange enabled |
| `app.lsd` | boolean | Local Service Discovery enabled |
| `app.encryption` | integer | Encryption: `0`=prefer unencrypted, `1`=prefer encrypted, `2`=require encrypted |
| `app.proxy_type` | integer | Proxy type: `-1`=none, `1`=HTTP, `2`=SOCKS5 |
| `app.queueing_enabled` | boolean | Queueing system enabled |
| `app.autorun_enabled` | boolean | Run external program on completion |
| `app.autorun_program` | string | External program path |

**Use Cases:**

```yaml
# Check encryption requirement
- field: app.encryption
  operator: ==
  value: 2  # Require encrypted

# Verify queueing enabled
- field: app.queueing_enabled
  operator: ==
  value: true
```

---

## Actions

Actions execute when rule conditions match. Multiple actions can be specified per rule and execute sequentially.

### Overview

**Available Actions:**

| Action | Description | Idempotent | Parameters |
|--------|-------------|------------|------------|
| `stop` | Stop/pause torrent | Yes | None |
| `start` | Start/resume torrent | Yes | None |
| `force_start` | Force start (bypass queue) | No | None |
| `recheck` | Recheck torrent files | No | None |
| `reannounce` | Force reannounce to trackers | No | None |
| `delete_torrent` | Delete torrent from qBittorrent | No | `keep_files` |
| `set_category` | Set torrent category | Yes | `category` |
| `add_tag` | Add tags to torrent | Yes | `tags` |
| `remove_tag` | Remove tags from torrent | Yes | `tags` |
| `set_tags` | Replace all tags | No | `tags` |
| `set_upload_limit` | Set upload speed limit | No | `limit` |
| `set_download_limit` | Set download speed limit | No | `limit` |

**Idempotent Actions:**
- **Yes**: Skipped if already in desired state (logged as "skipped")
- **No**: Always execute

### stop

**Description:** Stop/pause torrent (qBittorrent v5.0+ terminology)

**Parameters:** None

**Idempotent:** Yes (skips if already paused/stopped)

**Syntax:**

```yaml
actions:
  - type: stop
```

**Use Cases:**
- Pause well-seeded torrents to free bandwidth
- Stop torrents in error state
- Pause torrents exceeding ratio requirements
- Stop downloading after categorization for review

**Example:**

```yaml
- name: "Pause well-seeded torrents"
  conditions:
    all:
      - field: info.ratio
        operator: ">="
        value: 3.0
      - field: info.num_leechs
        operator: ==
        value: 0
  actions:
    - type: stop
```

### start

**Description:** Start/resume torrent (qBittorrent v5.0+ terminology)

**Parameters:** None

**Idempotent:** Yes (skips if already running)

**Syntax:**

```yaml
actions:
  - type: start
```

**Use Cases:**
- Resume paused torrents
- Auto-start torrents meeting criteria
- Re-enable stopped torrents after fixes

**Example:**

```yaml
- name: "Resume torrents under ratio"
  conditions:
    all:
      - field: info.ratio
        operator: "<"
        value: 1.0
      - field: info.state
        operator: ==
        value: pausedUP
  actions:
    - type: start
```

### force_start

**Description:** Force start torrent (bypasses queue limits)

**Parameters:** None

**Idempotent:** No (always executes)

**Syntax:**

```yaml
actions:
  - type: force_start
```

**Use Cases:**
- Prioritize private tracker torrents under ratio
- Force-seed important torrents
- Override queue limits for specific content

**Example:**

```yaml
- name: "Force start private torrents under ratio"
  conditions:
    all:
      - field: info.ratio
        operator: "<"
        value: 1.0
      - field: trackers.url
        operator: contains
        value: ".private"
  actions:
    - type: force_start
```

**Note:** Use sparingly - bypasses qBittorrent's queue management

### recheck

**Description:** Recheck torrent files for integrity

**Parameters:** None

**Idempotent:** No (always executes)

**Syntax:**

```yaml
actions:
  - type: recheck
```

**Use Cases:**
- Fix stalled downloads near completion
- Verify files after external modification
- Troubleshoot corrupted data

**Example:**

```yaml
- name: "Recheck stalled downloads near completion"
  conditions:
    all:
      - field: info.state
        operator: ==
        value: stalledDL
      - field: info.progress
        operator: ">"
        value: 0.9
  actions:
    - type: recheck
```

### reannounce

**Description:** Force reannounce to all trackers

**Parameters:** None

**Idempotent:** No (always executes)

**Syntax:**

```yaml
actions:
  - type: reannounce
```

**Use Cases:**
- Update tracker stats immediately
- Fix tracker communication issues
- Refresh peer list

**Example:**

```yaml
- name: "Reannounce private torrents periodically"
  conditions:
    trigger: scheduled
    all:
      - field: trackers.url
        operator: contains
        value: ".private"
  actions:
    - type: reannounce
```

### delete_torrent

**Description:** Delete torrent from qBittorrent

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `keep_files` | boolean | No | `false` | Keep downloaded files on disk |

**Idempotent:** No (deletes permanently)

**Syntax:**

```yaml
# Delete torrent and files
actions:
  - type: delete_torrent
    params:
      keep_files: false

# Delete torrent, keep files
actions:
  - type: delete_torrent
    params:
      keep_files: true
```

**Use Cases:**
- Remove old completed torrents
- Clean up errored torrents
- Delete torrents with missing files
- Space management

**Examples:**

```yaml
# Delete old completed torrents (including files)
- name: "Delete old completed"
  conditions:
    all:
      - field: info.completion_on
        operator: older_than
        value: 30 days
      - field: info.ratio
        operator: ">="
        value: 1.0
  actions:
    - type: delete_torrent
      params:
        keep_files: false
```

```yaml
# Remove errored torrents (keep files)
- name: "Remove errored torrents"
  conditions:
    any:
      - field: info.state
        operator: ==
        value: error
      - field: info.state
        operator: ==
        value: missingFiles
  actions:
    - type: delete_torrent
      params:
        keep_files: true
```

**WARNING:** Deletion is permanent! Always test with `--dry-run` first.

### set_category

**Description:** Set torrent category

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | Yes | Category name (empty string `""` to remove) |

**Idempotent:** Yes (skips if already set)

**Syntax:**

```yaml
# Set category
actions:
  - type: set_category
    params:
      category: movies-hd

# Remove category
actions:
  - type: set_category
    params:
      category: ""
```

**Use Cases:**
- Auto-categorize by content type
- Organize by tracker
- Group by resolution or quality
- Migrate between categories

**Examples:**

```yaml
# Auto-categorize HD movies
- name: "Categorize HD movies"
  conditions:
    all:
      - field: info.name
        operator: matches
        value: '(?i).*(1080p|2160p).*'
      - field: info.category
        operator: ==
        value: ""
  actions:
    - type: set_category
      params:
        category: movies-hd
```

```yaml
# Categorize by tracker
- name: "Categorize private tracker content"
  conditions:
    all:
      - field: trackers.url
        operator: contains
        value: ".private"
  actions:
    - type: set_category
      params:
        category: private
```

**Important:** Category must exist in qBittorrent (create manually first)

### add_tag

**Description:** Add one or more tags to torrent

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tags` | list[string] | Yes | Tag names to add |

**Idempotent:** Yes (skips if all tags already present)

**Syntax:**

```yaml
actions:
  - type: add_tag
    params:
      tags:
        - hd
        - private
        - auto-tagged
```

**Use Cases:**
- Tag by content attributes
- Mark torrents by tracker
- Flag for manual review
- Track automation actions

**Examples:**

```yaml
# Tag HD content
- name: "Tag HD content"
  conditions:
    all:
      - field: info.name
        operator: matches
        value: '(?i).*(1080p|2160p|4k).*'
  actions:
    - type: add_tag
      params:
        tags:
          - hd
```

```yaml
# Tag completed large downloads
- name: "Tag large completed downloads"
  conditions:
    trigger: on_completed
    all:
      - field: info.size
        operator: ">"
        value: 10737418240  # > 10GB
  actions:
    - type: add_tag
      params:
        tags:
          - completed-large
          - needs-seeding
```

### remove_tag

**Description:** Remove one or more tags from torrent

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tags` | list[string] | Yes | Tag names to remove |

**Idempotent:** Yes (skips if tags not present)

**Syntax:**

```yaml
actions:
  - type: remove_tag
    params:
      tags:
        - temporary
        - review-needed
```

**Use Cases:**
- Clean up temporary tags
- Remove outdated markers
- Clear automation flags

**Example:**

```yaml
# Remove temporary tag after processing
- name: "Clean up temp tags"
  conditions:
    all:
      - field: info.tags
        operator: contains
        value: "temp"
      - field: info.completion_on
        operator: older_than
        value: 1 days
  actions:
    - type: remove_tag
      params:
        tags:
          - temp
```

### set_tags

**Description:** Replace all tags with new set (removes existing first)

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tags` | list[string] | Yes | Complete tag list |

**Idempotent:** No (always executes)

**Syntax:**

```yaml
actions:
  - type: set_tags
    params:
      tags:
        - hd
        - verified
```

**Use Cases:**
- Reset tagging completely
- Enforce specific tag set
- Clear all tags and apply new ones

**Example:**

```yaml
# Reset tags for completed torrents
- name: "Reset tags on completion"
  conditions:
    trigger: on_completed
  actions:
    - type: set_tags
      params:
        tags:
          - completed
          - seeding
```

### set_upload_limit

**Description:** Set per-torrent upload speed limit

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | Yes | Upload limit in bytes/s (`-1` for unlimited) |

**Idempotent:** No (always executes)

**Syntax:**

```yaml
# Limit to 100 KB/s
actions:
  - type: set_upload_limit
    params:
      limit: 102400

# Remove limit (unlimited)
actions:
  - type: set_upload_limit
    params:
      limit: -1
```

**Use Cases:**
- Throttle well-seeded torrents
- Prioritize bandwidth for new uploads
- Limit old torrents to free bandwidth
- Manage bandwidth allocation

**Examples:**

```yaml
# Throttle old torrents
- name: "Limit upload for old torrents"
  conditions:
    all:
      - field: info.ratio
        operator: ">="
        value: 5.0
      - field: info.seeding_time
        operator: ">"
        value: 2592000  # 30 days
  actions:
    - type: set_upload_limit
      params:
        limit: 102400  # 100 KB/s
```

**Common Speed Conversions:**

| Speed | Bytes/Second |
|-------|--------------|
| 50 KB/s | 51200 |
| 100 KB/s | 102400 |
| 500 KB/s | 512000 |
| 1 MB/s | 1048576 |
| 5 MB/s | 5242880 |
| 10 MB/s | 10485760 |

### set_download_limit

**Description:** Set per-torrent download speed limit

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | Yes | Download limit in bytes/s (`-1` for unlimited) |

**Idempotent:** No (always executes)

**Syntax:**

```yaml
# Limit to 1 MB/s
actions:
  - type: set_download_limit
    params:
      limit: 1048576

# Remove limit (unlimited)
actions:
  - type: set_download_limit
    params:
      limit: -1
```

**Use Cases:**
- Throttle large downloads
- Prevent bandwidth saturation
- Prioritize specific torrents
- Time-based speed management

**Example:**

```yaml
# Limit large downloads
- name: "Throttle large downloads"
  conditions:
    trigger: on_added
    all:
      - field: info.size
        operator: ">"
        value: 21474836480  # > 20GB
  actions:
    - type: set_download_limit
      params:
        limit: 2097152  # 2 MB/s
```

---

## 9. Examples

This section provides real-world rule examples organized by common use cases.

### 9.1 Content Organization

#### Auto-Categorize Movies

```yaml
- name: "Auto-categorize HD movies"
  enabled: true
  stop_on_match: true
  conditions:
    trigger: on_added
    all:
      - field: info.name
        operator: matches
        value: '(?i).*(1080p|2160p|4k).*\.(mkv|mp4|avi)$'
  actions:
    - type: set_category
      params:
        category: "Movies-HD"
    - type: add_tag
      params:
        tag: "movies"
```

#### Auto-Categorize TV Shows

```yaml
- name: "Auto-categorize TV shows"
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
    - type: add_tag
      params:
        tag: "tv"
```

#### Organize by Tracker

```yaml
- name: "Categorize private tracker content"
  enabled: true
  stop_on_match: true
  conditions:
    trigger: on_added
    any:
      - field: trackers.url
        operator: contains
        value: "privatehd.to"
      - field: trackers.url
        operator: contains
        value: "passthepopcorn.me"
  actions:
    - type: set_category
      params:
        category: "Private"
    - type: add_tag
      params:
        tag: "private-tracker"
```

### 9.2 Content Filtering

#### Block Archive Files

```yaml
- name: "Remove torrents with only archives"
  enabled: true
  stop_on_match: true
  conditions:
    trigger: on_added
    all:
      - field: files.name
        operator: matches
        value: '(?i).*\.(rar|zip|7z|tar|gz)$'
  actions:
    - type: delete_torrent
      params:
        delete_files: true
```

#### Remove Sample Files

```yaml
- name: "Delete torrents with sample files"
  enabled: true
  stop_on_match: true
  conditions:
    trigger: on_added
    any:
      - field: info.name
        operator: contains
        value: "sample"
      - field: files.name
        operator: contains
        value: "sample"
  actions:
    - type: delete_torrent
      params:
        delete_files: true
```

#### Filter by Size

```yaml
- name: "Remove torrents too small"
  enabled: true
  conditions:
    trigger: on_added
    all:
      - field: info.size
        operator: "<"
        value: 104857600  # < 100MB
      - field: info.category
        operator: "=="
        value: "Movies"
  actions:
    - type: delete_torrent
      params:
        delete_files: true
```

### 9.3 Tracker Management

#### Tag Private Trackers

```yaml
- name: "Tag all private tracker torrents"
  enabled: true
  conditions:
    trigger: manual
    all:
      - field: trackers.url
        operator: not_contains
        value: "public"
  actions:
    - type: add_tag
      params:
        tag: "private"
```

#### Force Start on Specific Tracker

```yaml
- name: "Force start low-seeded torrents on private trackers"
  enabled: true
  conditions:
    trigger: manual
    all:
      - field: trackers.url
        operator: contains
        value: "privatehd.to"
      - field: info.num_complete
        operator: "<"
        value: 3
  actions:
    - type: force_start
```

#### Reannounce Stalled Trackers

```yaml
- name: "Reannounce torrents with tracker errors"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: trackers.msg
        operator: not_contains
        value: "Working"
      - field: info.state
        operator: "=="
        value: "stalledUP"
  actions:
    - type: reannounce
```

### 9.4 Cleanup & Maintenance

#### Remove Old Completed Torrents

```yaml
- name: "Delete old completed torrents"
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
        value: 1.0
  actions:
    - type: delete_torrent
      params:
        delete_files: false
```

#### Remove Stalled Downloads

```yaml
- name: "Delete stalled downloads after 7 days"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: info.state
        operator: "=="
        value: "stalledDL"
      - field: info.added_on
        operator: older_than
        value: 604800  # 7 days
  actions:
    - type: delete_torrent
      params:
        delete_files: true
```

#### Clean Up Errored Torrents

```yaml
- name: "Remove errored torrents"
  enabled: true
  conditions:
    trigger: scheduled
    any:
      - field: info.state
        operator: "=="
        value: "error"
      - field: info.state
        operator: "=="
        value: "missingFiles"
  actions:
    - type: delete_torrent
      params:
        delete_files: false
```

### 9.5 Seeding Management

#### Pause Well-Seeded Torrents

```yaml
- name: "Pause torrents with high ratio and seeders"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: info.ratio
        operator: ">="
        value: 2.0
      - field: info.num_complete
        operator: ">"
        value: 10
      - field: info.state
        operator: "=="
        value: "uploading"
  actions:
    - type: stop
```

#### Start Underseded Torrents

```yaml
- name: "Force start torrents with low seeders"
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

#### Throttle Old Torrents

```yaml
- name: "Limit upload speed for old torrents"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: info.completion_on
        operator: older_than
        value: 1209600  # 14 days
      - field: info.ratio
        operator: ">="
        value: 1.5
  actions:
    - type: set_upload_limit
      params:
        limit: 524288  # 512 KB/s
```

### 9.6 Error Handling & Recovery

#### Recheck Missing Files

```yaml
- name: "Recheck torrents with missing files"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: info.state
        operator: "=="
        value: "missingFiles"
  actions:
    - type: recheck
```

#### Remove Errored Torrents After Retry

```yaml
- name: "Delete permanently errored torrents"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: info.state
        operator: "=="
        value: "error"
      - field: info.added_on
        operator: older_than
        value: 259200  # 3 days
  actions:
    - type: delete_torrent
      params:
        delete_files: false
```

#### Auto-Resume Paused Downloads

```yaml
- name: "Resume paused downloads with activity"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: info.state
        operator: "=="
        value: "pausedDL"
      - field: info.availability
        operator: ">"
        value: 0.5
  actions:
    - type: start
```

### 9.7 Advanced Multi-Criteria Rules

#### Complex Download Management

```yaml
- name: "Manage large, slow downloads"
  enabled: true
  conditions:
    trigger: scheduled
    all:
      - field: info.size
        operator: ">"
        value: 10737418240  # > 10GB
      - field: info.state
        operator: "=="
        value: "downloading"
      - field: info.dlspeed
        operator: "<"
        value: 102400  # < 100 KB/s
      - field: info.added_on
        operator: newer_than
        value: 86400  # < 1 day old
    none:
      - field: info.category
        operator: "=="
        value: "Priority"
  actions:
    - type: set_download_limit
      params:
        limit: 1048576  # 1 MB/s max
    - type: add_tag
      params:
        tag: "throttled"
```

#### Conditional Seeding Strategy

```yaml
- name: "Smart seeding based on ratio and time"
  enabled: true
  conditions:
    trigger: on_completed
    any:
      # High ratio achieved
      - field: info.ratio
        operator: ">="
        value: 3.0
      # OR seeded for 30 days with ratio >= 1.0
      - all:
          - field: info.completion_on
            operator: older_than
            value: 2592000  # 30 days
          - field: info.ratio
            operator: ">="
            value: 1.0
  actions:
    - type: stop
    - type: add_tag
      params:
        tag: "seeding-complete"
```

#### Private Tracker Automation

```yaml
- name: "Private tracker: force seed low-seeded content"
  enabled: true
  conditions:
    trigger: on_completed
    all:
      - field: trackers.url
        operator: contains
        value: "passthepopcorn.me"
      - field: info.num_complete
        operator: "<="
        value: 5
  actions:
    - type: force_start
    - type: set_category
      params:
        category: "Private-Important"
    - type: add_tag
      params:
        tag: "must-seed"
    - type: set_upload_limit
      params:
        limit: -1  # Unlimited
```

### 9.8 Scheduled Maintenance Example

```yaml
# Daily cleanup at 3 AM
- name: "Daily cleanup: remove completed torrents"
  enabled: true
  conditions:
    trigger: scheduled
    schedule: "0 3 * * *"
    all:
      - field: info.state
        operator: in
        value: ["pausedUP", "stalledUP"]
      - field: info.ratio
        operator: ">="
        value: 2.0
      - field: info.completion_on
        operator: older_than
        value: 604800  # 7 days
  actions:
    - type: delete_torrent
      params:
        delete_files: false

# Weekly recheck of all torrents
- name: "Weekly integrity check"
  enabled: true
  conditions:
    trigger: scheduled
    schedule: "0 4 * * 0"  # Sundays at 4 AM
    all:
      - field: info.state
        operator: in
        value: ["uploading", "stalledUP"]
  actions:
    - type: recheck
```

### 9.9 Webhook Integration Example

```yaml
# Auto-categorize on add
- name: "Webhook: Categorize new downloads"
  enabled: true
  conditions:
    trigger: on_added
    any:
      - field: info.name
        operator: matches
        value: '(?i).*\.(mkv|mp4|avi)$'
      - field: files.name
        operator: matches
        value: '(?i).*\.(mkv|mp4|avi)$'
  actions:
    - type: set_category
      params:
        category: "Videos"
    - type: add_tag
      params:
        tag: "auto-categorized"

# Post-completion actions
- name: "Webhook: Tag completed downloads"
  enabled: true
  conditions:
    trigger: on_completed
    all:
      - field: info.ratio
        operator: "<"
        value: 1.0
  actions:
    - type: add_tag
      params:
        tag: "needs-seeding"
    - type: force_start
```

---

## 10. FAQ

### 10.1 General Questions

**Q: What is qBittorrent Automation?**

A: qBittorrent Automation is a Python-based rules engine that automates torrent management tasks through the qBittorrent Web API. It allows you to define YAML-based rules that automatically categorize, tag, pause, resume, delete, and manage torrents based on conditions you specify.

**Q: Why not use qBittorrent's built-in RSS automation?**

A: qBittorrent's RSS automation only works for adding new torrents based on RSS feeds. This system provides:
- Management of **existing** torrents based on conditions
- Multiple trigger types (manual, scheduled, webhooks)
- Complex condition logic (AND/OR/NOT groups)
- Access to all torrent fields and metadata
- Idempotent actions that won't repeat unnecessarily
- Dry-run mode for safe testing

**Q: Does this work with qBittorrent v4.x?**

A: This system is designed for qBittorrent Web API **v5.0+** which introduced breaking changes (e.g., `pause`→`stop`, `resume`→`start`). If you're using qBittorrent v4.x, you'll need to modify the API client to use the old endpoint names.

**Q: Is this safe to run on my existing torrents?**

A: Yes! The system has several safety features:
- **Dry-run mode** (`--dry-run`) shows what would happen without making changes
- **Idempotent actions** skip if torrent already in desired state
- **File-order execution** allows predictable rule evaluation
- **Comprehensive logging** with trace mode for debugging
- **stop_on_match** prevents multiple rules from affecting the same torrent

**Q: Can I run this on Windows?**

A: Yes! The system is Python-based and works on Windows, Linux, and macOS. You'll need Python 3.8+ and the required dependencies (`requests`, `pyyaml`).

### 10.2 Configuration Questions

**Q: Where should I put my config files?**

A: By default, the system looks for:
- `config/config.yml` - Connection and global settings
- `config/rules.yml` - Your automation rules

You can override these with `--config` and `--rules` flags.

**Q: How do I use environment variables in config files?**

A: Use `${VARIABLE_NAME}` syntax:

```yaml
qbittorrent:
  username: ${QB_USERNAME}
  password: ${QB_PASSWORD}
```

The system expands these at runtime using `os.environ`.

**Q: Can I have multiple rule files?**

A: Currently, the system loads a single rules file. However, you can organize rules within the file using YAML comments and logical grouping:

```yaml
# ===== Content Organization =====
- name: "Categorize movies"
  # ...

# ===== Cleanup =====
- name: "Remove old torrents"
  # ...
```

**Q: What happens if qBittorrent is unreachable?**

A: The system will raise a `ConnectionError` and exit. For scheduled triggers, ensure you have proper error handling in your cron job or systemd timer.

**Q: How do I enable trace logging?**

A: Use the `--trace` flag:

```bash
python triggers/manual.py --trace
```

This logs all API calls, field accesses, and condition evaluations.

### 10.3 Field & Condition Questions

**Q: How do I know what fields are available?**

A: See the **Available Fields** section (§7) for complete tables. You can also:
1. Enable `--trace` mode to see all field accesses
2. Check qBittorrent Web API documentation
3. Use `/api/v2/torrents/info` to see raw torrent data

**Q: What's the difference between `info.size` and `info.total_size`?**

A:
- `info.size` - Total size of the torrent (all files)
- `info.total_size` - Same as `info.size` (alias in qBittorrent API)

Both return the same value in bytes.

**Q: Why is my `files.*` condition not working?**

A: `files.*` is a **collection field** - it returns a list. Operators check if **ANY** item in the list matches:

```yaml
# This checks if ANY file name contains "sample"
- field: files.name
  operator: contains
  value: "sample"
```

If you need to check ALL files, use a `none` condition with the inverse:

```yaml
# This ensures NO file is larger than 1GB
conditions:
  none:
    - field: files.size
      operator: ">"
      value: 1073741824
```

**Q: How do I check if a torrent has NO tags?**

A: Check if the tags string is empty:

```yaml
conditions:
  all:
    - field: info.tags
      operator: "=="
      value: ""
```

**Q: Can I use regex in conditions?**

A: Yes! Use the `matches` operator:

```yaml
- field: info.name
  operator: matches
  value: '(?i).*[Ss]\d{2}[Ee]\d{2}.*'  # TV show pattern
```

Use `(?i)` for case-insensitive matching.

**Q: How do `older_than` and `newer_than` work?**

A: These operators compare Unix timestamps against a relative time in seconds:

```yaml
# Torrents added more than 7 days ago
- field: info.added_on
  operator: older_than
  value: 604800  # 7 days in seconds

# Torrents completed less than 24 hours ago
- field: info.completion_on
  operator: newer_than
  value: 86400  # 24 hours in seconds
```

**Q: What does `info.state` return?**

A: The current state string, one of:
- `downloading` - Actively downloading
- `uploading` - Actively seeding
- `pausedDL` - Paused while incomplete
- `pausedUP` - Paused after completion
- `stalledDL` - No download progress
- `stalledUP` - No upload activity
- `checkingUP` - Checking files after completion
- `checkingDL` - Checking files while incomplete
- `error` - Torrent has errors
- `missingFiles` - Files missing on disk
- `forcedUP` - Force seeding
- `forcedDL` - Force downloading

### 10.4 Trigger Questions

**Q: How often do scheduled triggers run?**

A: Scheduled triggers use cron expressions. You control the schedule:

```yaml
# Every hour
schedule: "0 * * * *"

# Every day at 3 AM
schedule: "0 3 * * *"

# Every Monday at 9 AM
schedule: "0 9 * * 1"
```

Then run `triggers/scheduled.py` in your cron or systemd timer.

**Q: Can I test scheduled rules without waiting?**

A: Yes! Use manual trigger with dry-run:

```bash
python triggers/manual.py --dry-run
```

This evaluates all enabled rules immediately.

**Q: How do webhooks work?**

A: Set up qBittorrent to call your webhook server when torrents are added or completed:

1. Run the webhook listener:
```bash
python triggers/on_added.py --port 8081
```

2. Configure qBittorrent to POST to `http://your-server:8081/webhook` when torrents are added

3. Rules with `trigger: on_added` will be evaluated for the specific torrent

**Q: Can I filter which torrents a trigger processes?**

A: Yes! Use the `filter` section in trigger conditions:

```yaml
conditions:
  trigger: manual
  filter:
    category: "Movies"  # Only process Movies category
    state: "downloading"  # Only downloading torrents
  all:
    - field: info.ratio
      operator: "<"
      value: 1.0
```

**Q: What's the difference between `manual.py` and `scheduled.py`?**

A:
- **manual.py** - Run on-demand, processes all torrents matching rules (useful for testing or one-time bulk operations)
- **scheduled.py** - Same as manual but designed to be run by cron/systemd timer at regular intervals

Both use `trigger: manual` or `trigger: scheduled` in rules.

### 10.5 Action Questions

**Q: Will `stop` action pause a torrent that's already paused?**

A: No - actions are **idempotent**. The system checks the current state:

```python
if torrent["state"] in ["pausedUP", "pausedDL"]:
    logger.info(f"Torrent already stopped, skipping")
    return
```

**Q: What's the difference between `start` and `force_start`?**

A:
- **start** - Resume normal downloading/seeding (respects queue limits)
- **force_start** - Force the torrent to start regardless of queue limits (useful for private trackers or low-seeded content)

**Q: Does `delete_torrent` remove files from disk?**

A: Only if you specify `delete_files: true`:

```yaml
actions:
  - type: delete_torrent
    params:
      delete_files: true  # Remove from disk
```

If `false` or omitted, only removes from qBittorrent (files stay on disk).

**Q: Can I set multiple tags at once?**

A: Yes! Use `set_tags`:

```yaml
actions:
  - type: set_tags
    params:
      tags: "movies,hd,private"
```

This **replaces** all existing tags. To add tags while keeping existing ones, use `add_tag`.

**Q: How do I remove all tags?**

A: Use `set_tags` with an empty string:

```yaml
actions:
  - type: set_tags
    params:
      tags: ""
```

**Q: What does `limit: -1` mean for upload/download limits?**

A: `-1` means **unlimited** (removes any speed limit).

**Q: Can I run multiple actions for the same torrent?**

A: Yes! Actions execute in order:

```yaml
actions:
  - type: set_category
    params:
      category: "Movies"
  - type: add_tag
    params:
      tag: "auto-categorized"
  - type: stop
```

All three actions will execute if conditions match.

### 10.6 Performance Questions

**Q: How many API calls does the system make?**

A: The system optimizes API calls through caching:

**Per-Trigger API Calls:**
1. Initial torrent list fetch (1 call)
2. Per-torrent metadata fetches (only if fields accessed):
   - `trackers.*` → `/api/v2/torrents/trackers` (1 call per torrent)
   - `files.*` → `/api/v2/torrents/files` (1 call per torrent)
   - `properties.*` → `/api/v2/torrents/properties` (1 call per torrent)
   - `peers.*` → `/api/v2/sync/torrentPeers` (1 call per torrent)
   - `webseeds.*` → `/api/v2/torrents/webseeds` (1 call per torrent)

**Example:** If you have 100 torrents and rules only check `info.*` fields, that's **1 API call total**. If rules also check `trackers.url`, that's **1 + 100 = 101 calls**.

**Q: How can I reduce API calls?**

A: Optimize your rules:

1. **Use filters** to limit torrents processed:
```yaml
conditions:
  filter:
    category: "Movies"  # Only fetch Movies category
```

2. **Avoid expensive fields** if possible:
   - `info.*` - Free (included in main list)
   - `trackers.*`, `files.*`, `properties.*` - Expensive (1 call per torrent)

3. **Use `stop_on_match: true`** to prevent redundant rule evaluation:
```yaml
- name: "First matching rule"
  stop_on_match: true
```

**Q: Can I run this on a system with 10,000+ torrents?**

A: Yes, but optimize carefully:

1. Use aggressive filtering:
```yaml
filter:
  state: "downloading"  # Process only active torrents
```

2. Avoid expensive fields in high-frequency rules

3. Run scheduled triggers less frequently (every 6-12 hours instead of hourly)

4. Consider breaking rules into multiple files run at different intervals

**Q: How long does execution take?**

A: Depends on:
- Number of torrents
- Number of rules
- Fields accessed
- Network latency to qBittorrent

**Typical performance:**
- 100 torrents, simple rules (info.* only): **< 1 second**
- 100 torrents, complex rules (all fields): **5-10 seconds**
- 1000 torrents, simple rules: **2-5 seconds**
- 1000 torrents, complex rules: **30-60 seconds**

Use `--trace` to see timing breakdowns.

### 10.7 Error & Troubleshooting Questions

**Q: I'm getting `401 Unauthorized` errors**

A: Check your credentials in `config/config.yml`:

```yaml
qbittorrent:
  username: "admin"
  password: "your_password"
```

Also verify qBittorrent Web UI authentication is enabled.

**Q: Rules aren't matching torrents I expect**

A: Enable `--trace` mode to see condition evaluation:

```bash
python triggers/manual.py --trace
```

Look for lines like:
```
[TRACE] Evaluating condition: info.ratio >= 2.0
[TRACE] Result: False (actual value: 1.5)
```

**Q: Getting `KeyError` when accessing fields**

A: Not all fields exist for all torrents. The system handles missing fields gracefully:

```python
# If field doesn't exist, comparison returns False
```

Check that you're using correct field names from the Available Fields table.

**Q: `schedule` trigger isn't running**

A: Scheduled triggers don't run automatically - you need to set up cron or systemd timer:

**Cron example:**
```bash
0 * * * * cd /path/to/qbittorrent-automation && python triggers/scheduled.py
```

**Q: Webhook server won't start**

A: Check port availability:

```bash
# Linux: Check if port 8081 is in use
sudo netstat -tulpn | grep 8081

# Free the port or use a different one
python triggers/on_added.py --port 8082
```

**Q: Changes aren't applying to torrents**

A: Check:

1. **Dry-run mode**: Are you using `--dry-run`? Remove it to apply changes.
2. **Idempotency**: Action may be skipped if torrent already in desired state (check logs)
3. **Conditions**: Rule may not be matching (use `--trace`)
4. **stop_on_match**: Earlier rule may have matched first

### 10.8 Docker & Deployment Questions

**Q: Can I run this in Docker?**

A: Yes! Example `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install requests pyyaml

# Copy application
COPY lib/ /app/lib/
COPY triggers/ /app/triggers/
COPY config/ /app/config/

# Run scheduled trigger every hour
CMD ["sh", "-c", "while true; do python triggers/scheduled.py; sleep 3600; done"]
```

**Q: How do I deploy with systemd?**

A: Create a service file and timer:

**`/etc/systemd/system/qbittorrent-automation.service`:**
```ini
[Unit]
Description=qBittorrent Automation
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/qbittorrent-automation
ExecStart=/usr/bin/python3 triggers/scheduled.py
User=qbittorrent
```

**`/etc/systemd/system/qbittorrent-automation.timer`:**
```ini
[Unit]
Description=Run qBittorrent Automation hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable qbittorrent-automation.timer
sudo systemctl start qbittorrent-automation.timer
```

**Q: Can I run multiple instances?**

A: Yes, but ensure they don't conflict:

1. Use different rule files:
```bash
python triggers/manual.py --rules config/rules-cleanup.yml
python triggers/manual.py --rules config/rules-categorization.yml
```

2. Or use different trigger types (manual, scheduled, webhooks) simultaneously

**Q: How do I integrate with Sonarr/Radarr?**

A: Use the `on_added` webhook trigger:

1. Run webhook server:
```bash
python triggers/on_added.py --port 8081
```

2. Configure Sonarr/Radarr to send webhook to your server after adding torrents to qBittorrent

3. Create rules with `trigger: on_added` to auto-categorize/tag based on naming patterns

---

## 11. Troubleshooting

### 11.1 Common Issues

#### Issue: "Connection refused" to qBittorrent

**Symptoms:**
```
ConnectionError: Failed to connect to qBittorrent at http://localhost:8080
```

**Solutions:**

1. **Check qBittorrent Web UI is running:**
   - Open `http://localhost:8080` in browser
   - If not accessible, enable Web UI in qBittorrent settings

2. **Verify host/port in config:**
   ```yaml
   qbittorrent:
     host: http://localhost:8080  # Match your qBittorrent Web UI
   ```

3. **Check firewall rules:**
   ```bash
   # Linux: Allow port 8080
   sudo ufw allow 8080
   ```

4. **For remote qBittorrent, use full URL:**
   ```yaml
   qbittorrent:
     host: http://192.168.1.100:8080
   ```

#### Issue: Rules not matching expected torrents

**Symptoms:**
- Rule conditions look correct but torrents aren't matched
- No actions applied when they should be

**Debugging steps:**

1. **Enable trace mode:**
   ```bash
   python triggers/manual.py --trace
   ```

2. **Check condition evaluation:**
   ```
   [TRACE] Rule: "Remove old torrents"
   [TRACE]   Condition: info.ratio >= 2.0
   [TRACE]   Result: False (actual: 1.5)
   [TRACE]   Rule skipped
   ```

3. **Verify field values:**
   ```bash
   # Check actual field values
   curl -X GET "http://localhost:8080/api/v2/torrents/info" \
     --cookie "SID=your_session_id"
   ```

4. **Common mistakes:**
   - Wrong field name (`info.name` not `info.torrent_name`)
   - Wrong operator (`==` for exact match, `contains` for substring)
   - Wrong value type (string `"1.0"` vs float `1.0`)
   - Collection fields not understood (see §10.3)

#### Issue: Actions not being applied

**Symptoms:**
- Conditions match but actions don't execute
- Logs show "skipping" messages

**Possible causes:**

1. **Dry-run mode enabled:**
   ```bash
   # Remove --dry-run to apply changes
   python triggers/manual.py  # Not --dry-run
   ```

2. **Idempotent action already applied:**
   ```
   [INFO] Torrent already stopped, skipping
   [INFO] Category already set to 'Movies', skipping
   ```
   This is normal behavior - action was already applied previously.

3. **Earlier rule matched with `stop_on_match: true`:**
   ```yaml
   - name: "First rule"
     stop_on_match: true  # Prevents later rules from running
   ```

4. **Invalid action parameters:**
   ```
   [ERROR] Invalid category name: 'Invalid/Category'
   ```
   Check parameter validation in logs.

#### Issue: Regex patterns not matching

**Symptoms:**
- `matches` operator not finding expected torrents
- Pattern works in regex tester but not in rules

**Solutions:**

1. **Use raw strings in YAML:**
   ```yaml
   # Wrong: Backslashes interpreted by YAML
   value: '\d+'

   # Right: Single quotes preserve backslashes
   value: '(?i).*\d+.*'
   ```

2. **Test regex patterns:**
   ```python
   import re
   pattern = r'(?i).*[Ss]\d{2}[Ee]\d{2}.*'
   test_string = "Show.Name.S01E05.1080p"
   print(re.match(pattern, test_string))  # Should match
   ```

3. **Use `(?i)` for case-insensitive:**
   ```yaml
   - field: info.name
     operator: matches
     value: '(?i).*sample.*'  # Matches "Sample", "SAMPLE", "sample"
   ```

4. **Escape special characters:**
   ```yaml
   # To match literal dots
   value: '.*\.mkv$'  # Matches ".mkv" extension
   ```

### 11.2 Debugging Commands

#### Check qBittorrent API access

```bash
# Test authentication
curl -X POST "http://localhost:8080/api/v2/auth/login" \
  -d "username=admin&password=your_password"

# Get torrent list
curl -X GET "http://localhost:8080/api/v2/torrents/info" \
  --cookie "SID=your_session_id"

# Get specific torrent details
curl -X GET "http://localhost:8080/api/v2/torrents/properties?hash=TORRENT_HASH" \
  --cookie "SID=your_session_id"
```

#### Test config file syntax

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/config.yml'))"
python -c "import yaml; yaml.safe_load(open('config/rules.yml'))"
```

#### Test module imports

```bash
# Verify all modules load correctly
python -c "from lib.api import QBittorrentAPI; print('✓ API')"
python -c "from lib.config import load_config; print('✓ Config')"
python -c "from lib.engine import RulesEngine; print('✓ Engine')"
```

#### Run with maximum verbosity

```bash
# Enable all logging
python triggers/manual.py --trace --dry-run
```

#### Check Python environment

```bash
# Verify Python version (3.8+ required)
python --version

# Check dependencies
pip list | grep -E '(requests|pyyaml)'
```

### 11.3 Log Analysis

#### Understanding log levels

```python
[DEBUG]  # Development information (not shown by default)
[INFO]   # Normal operation messages
[WARNING]  # Potential issues that don't stop execution
[ERROR]  # Errors that prevent specific actions
[TRACE]  # Detailed execution flow (--trace flag required)
```

#### Common log messages

**Normal operation:**
```
[INFO] Loaded 5 rules from config/rules.yml
[INFO] Processing 42 torrents
[INFO] Rule "Remove old torrents" matched torrent "Example.Torrent"
[INFO] Executing action: delete_torrent
[INFO] Deleted torrent: Example.Torrent (hash: abc123...)
```

**Idempotent skips (normal):**
```
[INFO] Torrent already stopped, skipping
[INFO] Category already set to 'Movies', skipping
[INFO] Tag 'auto' already exists, skipping
```

**Errors:**
```
[ERROR] Failed to delete torrent abc123: 404 Torrent not found
[ERROR] Invalid category name: 'Invalid/Category'
[ERROR] Connection timeout after 30s
```

**Trace mode (debugging):**
```
[TRACE] Fetching trackers for torrent: abc123
[TRACE] API call: /api/v2/torrents/trackers?hash=abc123
[TRACE] Response: [{'url': 'udp://tracker.example.com:80', ...}]
[TRACE] Evaluating condition: trackers.url contains "example.com"
[TRACE] Result: True
```

### 11.4 Performance Issues

#### Slow execution with many torrents

**Symptoms:**
- Rules take minutes to run
- High API call volume

**Solutions:**

1. **Add filters to reduce torrent set:**
   ```yaml
   conditions:
     filter:
       category: "Movies"  # Only process specific category
       state: "downloading"  # Only active torrents
   ```

2. **Avoid expensive fields:**
   ```yaml
   # Fast: Uses cached info.* data
   - field: info.ratio
     operator: ">="
     value: 2.0

   # Slow: Requires API call per torrent
   - field: files.name
     operator: contains
     value: "sample"
   ```

3. **Use `stop_on_match`:**
   ```yaml
   - name: "First match wins"
     stop_on_match: true  # Don't evaluate remaining rules
   ```

4. **Run less frequently:**
   ```bash
   # Cron: Every 6 hours instead of hourly
   0 */6 * * * python triggers/scheduled.py
   ```

#### High memory usage

**Symptoms:**
- Python process using excessive RAM
- Out of memory errors

**Solutions:**

1. **Process torrents in batches** (requires code modification)
2. **Reduce concurrent API calls**
3. **Clear caches more frequently**

---

## 12. Advanced Topics

### 12.1 Performance Optimization

#### Field Access Optimization

The system caches API responses per-torrent to minimize calls:

```python
# First access to trackers.url: API call made and cached
if torrent["trackers.url"] contains "example.com":
    ...

# Second access to trackers.url: Uses cached data (no API call)
if torrent["trackers.url"] contains "private":
    ...
```

**Best practices:**

1. **Access fields in order of expense:**
   ```yaml
   # Check cheap fields first
   all:
     - field: info.category    # Free
       operator: "=="
       value: "Movies"
     - field: files.name        # Expensive, but only if category matches
       operator: matches
       value: '.*\.mkv$'
   ```

2. **Reuse field references:**
   ```yaml
   # BAD: Multiple string operations
   any:
     - field: info.name
       operator: contains
       value: "1080p"
     - field: info.name
       operator: contains
       value: "2160p"

   # GOOD: Single regex
   any:
     - field: info.name
       operator: matches
       value: '(?i).*(1080p|2160p).*'
   ```

#### Rule Ordering

Rules execute top-to-bottom. Order matters for performance:

```yaml
# GOOD: Specific rules first, then general
- name: "High-priority: Private trackers"
  stop_on_match: true
  conditions:
    all:
      - field: trackers.url
        operator: contains
        value: "privatehd.to"

- name: "General cleanup"
  conditions:
    # This only runs if private tracker rule didn't match
```

### 12.2 Security Best Practices

#### Credential Management

**Never** hardcode credentials in config files:

```yaml
# BAD
qbittorrent:
  username: admin
  password: MyPassword123

# GOOD
qbittorrent:
  username: ${QB_USERNAME}
  password: ${QB_PASSWORD}
```

Set environment variables:
```bash
export QB_USERNAME="admin"
export QB_PASSWORD="secure_password"
```

#### File Permissions

Protect config files containing credentials:

```bash
# Restrict access to config files
chmod 600 config/config.yml
chown qbittorrent:qbittorrent config/config.yml
```

#### Network Security

If running webhook listeners:

1. **Use authentication** (implement token validation)
2. **Bind to localhost** if qBittorrent is local:
   ```bash
   python triggers/on_added.py --host 127.0.0.1 --port 8081
   ```
3. **Use reverse proxy** with HTTPS for remote access
4. **Implement rate limiting** to prevent abuse

### 12.3 Integration Patterns

#### Integration with Sonarr/Radarr

**Scenario:** Auto-categorize torrents added by Sonarr/Radarr

1. **Run webhook listener:**
   ```bash
   python triggers/on_added.py --port 8081
   ```

2. **Configure qBittorrent webhook** (if supported by your setup)

3. **Create categorization rules:**
   ```yaml
   - name: "Categorize Sonarr downloads"
     conditions:
       trigger: on_added
       all:
         - field: info.category
           operator: "=="
           value: "tv-sonarr"
     actions:
       - type: add_tag
         params:
           tag: "sonarr"
   ```

#### Integration with External Scripts

**Scenario:** Run custom script after specific condition

While the system doesn't directly support script execution, you can:

1. **Tag torrents** with automation rules
2. **Monitor tags** with external script:
   ```bash
   #!/bin/bash
   # Watch for "process-me" tag
   TAGGED=$(curl -s http://localhost:8080/api/v2/torrents/info | \
     jq -r '.[] | select(.tags | contains("process-me")) | .hash')

   for hash in $TAGGED; do
     # Run your custom logic
     ./process-torrent.sh "$hash"
   done
   ```

#### Integration with Notification Services

**Scenario:** Send notifications when rules match

Implement custom action type (requires code modification):

```python
# lib/actions.py
def send_notification(torrent, params):
    import requests
    message = params.get("message", "Rule matched")
    requests.post("https://ntfy.sh/qbittorrent",
                  data=message.encode('utf-8'))
```

Then use in rules:
```yaml
actions:
  - type: send_notification
    params:
      message: "Torrent {info.name} completed!"
```

### 12.4 Extending the System

#### Adding Custom Operators

Edit `lib/engine.py` to add new comparison operators:

```python
def evaluate_condition(torrent, condition):
    # ... existing code ...

    elif operator == "starts_with":
        return str(field_value).startswith(str(value))
    elif operator == "ends_with":
        return str(field_value).endswith(str(value))
```

Then use in rules:
```yaml
- field: info.name
  operator: starts_with
  value: "Ubuntu"
```

#### Adding Custom Actions

Edit `lib/actions.py`:

```python
def set_priority(api, torrent_hash, params):
    """Set torrent priority"""
    priority = params.get("priority", "normal")
    # Implement priority logic
    api.post(f"/api/v2/torrents/setPriority",
             data={"hashes": torrent_hash, "priority": priority})
```

Register in action mapping:
```python
ACTION_MAP = {
    # ... existing actions ...
    "set_priority": set_priority,
}
```

Use in rules:
```yaml
actions:
  - type: set_priority
    params:
      priority: "high"
```

#### Adding Custom Triggers

Create new trigger file `triggers/on_error.py`:

```python
#!/usr/bin/env python3
from lib.config import load_config
from lib.api import QBittorrentAPI
from lib.engine import RulesEngine

def main():
    config = load_config()
    api = QBittorrentAPI(config["qbittorrent"])
    api.login()

    # Fetch only errored torrents
    torrents = api.get("/api/v2/torrents/info",
                       params={"filter": "errored"})

    # Load and execute rules with trigger: on_error
    engine = RulesEngine(config["rules"], trigger_type="on_error")
    engine.execute(api, torrents)

if __name__ == "__main__":
    main()
```

Use in rules:
```yaml
- name: "Handle errored torrents"
  conditions:
    trigger: on_error
    all:
      - field: info.state
        operator: "=="
        value: "error"
  actions:
    - type: recheck
```

### 12.5 Scaling Strategies

#### Horizontal Scaling

Run multiple instances with different rule subsets:

**Instance 1 - Categorization (runs frequently):**
```bash
python triggers/scheduled.py --rules config/rules-categorization.yml
```

**Instance 2 - Cleanup (runs daily):**
```bash
python triggers/scheduled.py --rules config/rules-cleanup.yml
```

**Instance 3 - Webhooks (always running):**
```bash
python triggers/on_added.py --port 8081
```

#### Batch Processing

For very large torrent libraries (10,000+), implement batch processing:

```python
# Process torrents in chunks of 100
BATCH_SIZE = 100
for i in range(0, len(all_torrents), BATCH_SIZE):
    batch = all_torrents[i:i+BATCH_SIZE]
    engine.execute(api, batch)
    time.sleep(1)  # Rate limiting
```

---

## 13. Contributing

We welcome contributions to qBittorrent Automation!

### 13.1 How to Contribute

1. **Fork the repository** on GitHub
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. **Make your changes** with clear commit messages:
   ```bash
   git commit -m "feat: Add custom operator for field comparison"
   ```
4. **Test your changes:**
   ```bash
   python -m py_compile lib/*.py triggers/*.py
   python triggers/manual.py --dry-run
   ```
5. **Push to your fork:**
   ```bash
   git push origin feature/my-new-feature
   ```
6. **Create a Pull Request** with description of changes

### 13.2 Code Style

- Follow PEP 8 style guide
- Use descriptive variable names
- Add docstrings to functions
- Keep functions focused and modular

### 13.3 Testing

Before submitting PR:

```bash
# Validate Python syntax
python -m py_compile lib/*.py triggers/*.py

# Test imports
python -c "from lib.api import QBittorrentAPI"
python -c "from lib.engine import RulesEngine"

# Validate example configs
python -c "import yaml; yaml.safe_load(open('config/rules.example.yml'))"

# Run with dry-run
python triggers/manual.py --dry-run
```

### 13.4 Reporting Issues

When reporting bugs, include:

1. **Environment details:**
   - Python version
   - qBittorrent version
   - Operating system

2. **Configuration:**
   - Sanitized `config.yml` (remove credentials!)
   - Relevant rules from `rules.yml`

3. **Error output:**
   - Full error message
   - Traceback if applicable
   - Logs with `--trace` flag

4. **Steps to reproduce**

---

## 14. License

This project is released into the **public domain** under the [Unlicense](https://unlicense.org/).

You are free to:
- Use commercially
- Modify
- Distribute
- Use privately

**No attribution required.**

See the [LICENSE](LICENSE) file for full details.

---

## 15. Changelog

For detailed release history and version changes, see [CHANGELOG.md](CHANGELOG.md).

### Latest Release

**v0.0.1** - 2024-12-10

Initial release with core functionality:
- Complete qBittorrent Web API v2 client (v5.0+ support)
- Rules engine with file-order execution
- Multiple trigger types (manual, scheduled, on_added, on_completed)
- Comprehensive condition logic and operators
- Idempotent actions
- Dry-run mode and trace logging

See [CHANGELOG.md](CHANGELOG.md) for full release notes.

---

**Happy automating! 🚀**

For questions, issues, or contributions, visit the [GitHub repository](https://github.com/YOUR_USERNAME/qbittorrent-automation).

# Feature: Resolver Layer

## Overview

Introduces a unified reference system with typed groups, variable substitution, and explicit path resolution. This creates a composable foundation that scales from simple variable reuse to a full automation framework.

---

## Core Concepts

### The `refs` Block

All reusable components live under a single `refs` key, grouped by type:

```yaml
refs:
  vars:
    # Scalar values, lists, simple config
    min_ratio: 1.0
    cleanup_age: "30 days"
    protected_categories: ["keep", "archive"]
  
  conditions:
    # Condition groups: {all|any|none: [...]}
    private-tracker:
      any:
        - field: trackers.0.url
          operator: contains
          value: "privatehd.to"
        - field: trackers.0.url
          operator: contains
          value: "torrentleech.org"
    
    well-seeded:
      all:
        - field: info.ratio
          operator: ">="
          value: ${vars.min_ratio}
        - field: info.completion_on
          operator: older_than
          value: ${vars.cleanup_age}
  
  actions:
    # Action sequences: [{type, params}, ...]
    safe-delete:
      - type: add_tag
        params:
          tags: ["pending-delete"]
      - type: stop
    
    force-seed:
      - type: force_start
      - type: add_tag
        params:
          tags: ["force-seeding"]
```

### Why Grouping Matters

The group name tells you the schema:

| Group | Structure | Validation |
|-------|-----------|------------|
| `vars` | Scalars, lists | Key-value pairs |
| `conditions` | `{all\|any\|none: [...]}` | Nested condition groups |
| `actions` | `[{type, params}, ...]` | Action sequence array |

This enables:
- **Type-specific validation** at load time
- **Schema-aware tooling** (web UI renders each group differently)
- **Self-documenting config** (structure implies meaning)
- **Future extensibility** (new groups slot in cleanly)

---

## Path Resolution

### Explicit Dot Notation

All references use explicit paths:

```yaml
# Variable substitution
${vars.min_ratio}
${vars.cleanup_age}
${vars.protected_categories}

# Reference expansion
$ref: conditions.private-tracker
$ref: conditions.well-seeded
$ref: actions.safe-delete
```

### Why Explicit Paths?

**Prevents ambiguity.** Consider future expansion:

```yaml
refs:
  vars:
    timeout: 30
  schedules:
    cleanup:
      timeout: 60
  scripts:
    notify:
      timeout: 10
```

With explicit paths, `${vars.timeout}`, `${schedules.cleanup.timeout}`, and `${scripts.notify.timeout}` are unambiguous.

**Self-documenting.** Reading `${vars.min_ratio}` tells you exactly where the value comes from.

---

## Two Resolution Mechanisms

### 1. Variable Substitution (`${path}`)

Replaces placeholders with values. Type-aware:

```yaml
# Source
refs:
  vars:
    min_ratio: 1.0
    protected: ["keep", "archive"]

# Usage
value: ${vars.min_ratio}        # → 1.0 (float)
value: ${vars.protected}        # → ["keep", "archive"] (list)
value: "Ratio: ${vars.min_ratio}" # → "Ratio: 1.0" (string interpolation)
```

**Rule:** If `${...}` is the entire value, preserve original type. If embedded in a string, interpolate as string.

### 2. Reference Expansion (`$ref: path`)

Replaces node with referenced structure:

```yaml
# Source
refs:
  conditions:
    private-tracker:
      any:
        - field: trackers.0.url
          operator: contains
          value: "privatehd.to"

# Usage
conditions:
  - $ref: conditions.private-tracker

# Resolves to
conditions:
  - any:
      - field: trackers.0.url
        operator: contains
        value: "privatehd.to"
```

---

## Instance-Scoped Overrides

Instances can override `refs.vars`:

```yaml
refs:
  vars:
    min_ratio: 1.0
    cleanup_age: "30 days"

instances:
  seedbox:
    host: "http://seedbox:8080"
    refs:
      vars:
        min_ratio: 2.0
        cleanup_age: "90 days"
  
  homelab:
    host: "http://nas:8080"
    refs:
      vars:
        min_ratio: 0.5
        cleanup_age: "14 days"
```

Resolution precedence:
1. `instances.{id}.refs.vars` (if running against specific instance)
2. `refs.vars` (global defaults)

Same rule, different behaviour per instance:

```yaml
- name: "Cleanup well-seeded"
  conditions:
    - all:
        - field: info.ratio
          operator: ">="
          value: ${vars.min_ratio}  # 2.0 on seedbox, 0.5 on homelab
```

---

## Resolution Pipeline

```
┌─────────────────┐
│    Raw Rule     │
│   (from config) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────────────────────┐
│  Expand $ref    │◄────│ refs.conditions, refs.actions   │
│    (recursive)  │     └─────────────────────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────────────────────┐
│ Substitute ${…} │◄────│ refs.vars + instance overrides  │
│  (type-aware)   │     └─────────────────────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Resolved Rule  │
│ (ready to eval) │
└─────────────────┘
```

**Order matters:** `$ref` expansion happens first, so referenced conditions can contain `${vars.*}` placeholders.

---

## Full Example

```yaml
refs:
  vars:
    min_ratio: 1.0
    high_ratio: 2.5
    cleanup_age: "30 days"
    hd_pattern: '(?i).*(1080p|2160p|4k).*'
    protected_categories: ["keep", "seedbox", "archive"]
  
  conditions:
    private-tracker:
      any:
        - field: trackers.0.url
          operator: contains
          value: "privatehd.to"
        - field: trackers.0.url
          operator: contains
          value: "torrentleech.org"
        - field: trackers.0.url
          operator: contains
          value: "iptorrents.com"
    
    well-seeded:
      all:
        - field: info.ratio
          operator: ">="
          value: ${vars.min_ratio}
        - field: info.completion_on
          operator: older_than
          value: ${vars.cleanup_age}
    
    hd-content:
      all:
        - field: info.name
          operator: matches
          value: ${vars.hd_pattern}
    
    protected:
      any:
        - field: info.category
          operator: in
          value: ${vars.protected_categories}
        - field: info.tags
          operator: contains
          value: "keep"
  
  actions:
    safe-delete:
      - type: add_tag
        params:
          tags: ["pending-delete"]
      - type: stop
    
    force-seed:
      - type: force_start
      - type: add_tag
        params:
          tags: ["force-seeding"]

instances:
  seedbox:
    host: "http://seedbox:8080"
    username: admin
    refs:
      vars:
        min_ratio: 2.0
        cleanup_age: "90 days"
  
  homelab:
    host: "http://nas:8080"
    username: admin
    refs:
      vars:
        min_ratio: 0.5
        cleanup_age: "14 days"

rules:
  - name: "Cleanup well-seeded private tracker torrents"
    enabled: true
    context: weekly-cleanup
    priority: 50
    conditions:
      - $ref: conditions.private-tracker
      - $ref: conditions.well-seeded
      - none:
          - $ref: conditions.protected
    actions:
      - $ref: actions.safe-delete

  - name: "Force seed private tracker under ratio"
    enabled: true
    context: download-finished
    conditions:
      - $ref: conditions.private-tracker
      - all:
          - field: info.ratio
            operator: "<"
            value: ${vars.min_ratio}
    actions:
      - $ref: actions.force-seed
```

---

## Future Expansion

The `refs` structure is designed to grow. Planned groups:

```yaml
refs:
  vars: ...        # 0.5.0 ✓
  conditions: ...  # 0.5.0 ✓
  actions: ...     # 0.5.0 ✓
  
  schedules:       # 0.6.0 - Cron definitions
    weekly-cleanup:
      cron: "0 3 * * 0"
      context: weekly-cleanup
  
  notifications:   # 0.7.0 - Alert channels
    discord-alert:
      type: discord
      webhook: ${vars.discord_webhook}
  
  trackers:        # 0.8.0 - Tracker profiles
    privatehd:
      url_pattern: "privatehd.to"
      type: private
      min_ratio: 1.0
  
  scripts:         # 0.9.0 - External commands
    pre-delete:
      command: "/scripts/backup.sh"
      timeout: 30
  
  webhooks:        # 0.9.0 - Outbound HTTP
    sonarr-notify:
      url: "http://sonarr:8989/api/..."
      method: POST
```

Each group has its own schema. The resolver validates accordingly.

---

## Implementation Changes

### Resolver Updates

```python
class RuleResolver:
    def __init__(self, config: dict, instance_id: Optional[str] = None):
        refs = config.get('refs', {})
        
        # Extract typed groups
        self.vars = dict(refs.get('vars', {}))
        self.conditions = refs.get('conditions', {})
        self.actions = refs.get('actions', {})
        
        # Apply instance overrides
        if instance_id:
            instance = config.get('instances', {}).get(instance_id, {})
            instance_refs = instance.get('refs', {})
            instance_vars = instance_refs.get('vars', {})
            self.vars.update(instance_vars)
    
    def _lookup_ref(self, path: str) -> Any:
        """
        Resolve dot-notation path: 'conditions.private-tracker'
        """
        parts = path.split('.', 1)
        if len(parts) != 2:
            raise InvalidRefError(f"Invalid ref path: '{path}'. Expected 'group.name'")
        
        group, name = parts
        
        if group == 'conditions':
            if name not in self.conditions:
                raise UnknownRefError(path, list(self.conditions.keys()))
            return self.conditions[name]
        
        if group == 'actions':
            if name not in self.actions:
                raise UnknownRefError(path, list(self.actions.keys()))
            return self.actions[name]
        
        raise InvalidRefError(f"Unknown ref group: '{group}'")
    
    def _resolve_var_path(self, path: str) -> Any:
        """
        Resolve dot-notation variable path: 'vars.min_ratio'
        """
        parts = path.split('.', 1)
        if len(parts) != 2 or parts[0] != 'vars':
            raise InvalidVariableError(f"Invalid variable path: '{path}'. Expected 'vars.name'")
        
        name = parts[1]
        if name not in self.vars:
            raise UnknownVariableError(name, list(self.vars.keys()))
        
        return self.vars[name]
```

### Variable Pattern Update

```python
# Old: ${variable_name}
# New: ${vars.variable_name}

VAR_PATTERN = re.compile(r'\$\{(vars\.\w+)\}')
```

---

## Migration from 0.4.x

### Before (0.4.x)

```yaml
variables:
  min_ratio: 1.0

condition_sets:
  private-tracker:
    any:
      - field: trackers.0.url
        operator: contains
        value: "privatehd.to"

action_templates:
  safe-delete:
    - type: add_tag
      params:
        tags: ["pending-delete"]

rules:
  - conditions:
      - $ref: private-tracker
      - all:
          - field: info.ratio
            operator: ">="
            value: ${min_ratio}
    actions:
      - $ref: safe-delete
```

### After (0.5.0)

```yaml
refs:
  vars:
    min_ratio: 1.0
  
  conditions:
    private-tracker:
      any:
        - field: trackers.0.url
          operator: contains
          value: "privatehd.to"
  
  actions:
    safe-delete:
      - type: add_tag
        params:
          tags: ["pending-delete"]

rules:
  - conditions:
      - $ref: conditions.private-tracker
      - all:
          - field: info.ratio
            operator: ">="
            value: ${vars.min_ratio}
    actions:
      - $ref: actions.safe-delete
```


---

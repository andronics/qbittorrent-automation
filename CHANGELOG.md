# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2024-12-10

### Changed
- **BREAKING**: Project renamed from `qbittorrent-automation` to `qbt-rules`
- **BREAKING**: Package name changed from `qbittorrent-automation` to `qbt-rules` on PyPI
- **BREAKING**: Import paths changed from `qbittorrent_automation.*` to `qbt_rules.*`
- **BREAKING**: Package directory renamed from `src/qbittorrent_automation/` to `src/qbt_rules/`
- All GitHub repository URLs updated to reflect new name
- All documentation links updated to point to new repository
- Console scripts remain unchanged (`qbt-manual`, `qbt-scheduled`, etc.) - perfect alignment with new name
- Configuration directory recommendation changed to `~/.config/qbt-rules/`

### Migration Guide for v0.2.0
**If upgrading from v0.1.0:**

1. **Update imports in your code** (if you imported the package directly):
   ```python
   # Old (v0.1.0)
   from qbittorrent_automation.api import QBittorrentAPI
   from qbittorrent_automation.config import load_config

   # New (v0.2.0)
   from qbt_rules.api import QBittorrentAPI
   from qbt_rules.config import load_config
   ```

2. **Reinstall package**:
   ```bash
   pip uninstall qbittorrent-automation
   pip install qbt-rules
   ```

3. **Console scripts unchanged** - `qbt-manual`, `qbt-scheduled`, etc. work exactly the same
4. **Configuration files unchanged** - No changes needed to `config.yml` or `rules.yml`
5. **Legacy trigger scripts** still work if using `python triggers/manual.py` approach

**Why this change?**
- Shorter, more memorable name
- Perfect alignment with existing `qbt-*` console script naming
- Clearer branding and easier to communicate
- More concise package name on PyPI

## [0.1.0] - 2024-12-10

### Added
- **Complete Python package restructuring to src layout**
- PyPI installable package with `pip install qbittorrent-automation`
- Console script entry points: `qbt-manual`, `qbt-scheduled`, `qbt-on-added`, `qbt-on-completed`
- `pyproject.toml` with modern build system (PEP 517/518)
- `LICENSE` file (Unlicense/Public Domain)
- `requirements-dev.txt` with development dependencies
- Test suite infrastructure with pytest
- Type hints support with `py.typed` marker
- Legacy wrapper scripts for backward compatibility
- GitHub Actions workflows for CI and releases
- Automated version bumping script
- Release automation with changelog generation

### Changed
- **BREAKING**: Project structure migrated from flat layout to src layout
- **BREAKING**: Import paths changed from `from lib.X` to `from qbittorrent_automation.X`
- Moved `lib/*` → `src/qbittorrent_automation/*`
- Moved `triggers/*` → `src/qbittorrent_automation/cli/*`
- Updated all internal imports to use new package structure
- Version bumped to 0.1.0 to reflect major restructuring

### Fixed
- Removed duplicate PyYAML entries in requirements.txt
- Updated .gitignore for build artifacts (.mypy_cache, .ruff_cache, etc.)

### Backward Compatibility
- Legacy `triggers/*.py` scripts still work (as thin wrappers)
- Existing deployments using `python triggers/manual.py` continue to function
- Configuration files and rules syntax unchanged

### Migration Guide
- **For users cloning the repo**: Run `pip install -e .` to install in editable mode
- **For new installations**: Use `pip install qbittorrent-automation` from PyPI
- **For cron jobs**: Update to use `qbt-scheduled` instead of `python triggers/scheduled.py`
- **For systemd**: Update ExecStart to use `/usr/local/bin/qbt-scheduled`
- **For Docker**: Update Dockerfile to `pip install qbittorrent-automation`

## [0.0.1] - 2024-12-10

### Added
- Initial release of qBittorrent Automation System
- Complete qBittorrent Web API v2 client (v5.0+ support)
- Rules engine with file-order execution
- Dot notation field access (info.*, trackers.*, files.*, peers.*, etc.)
- Multiple trigger types: manual, scheduled, on_added, on_completed
- Centralized logging with trace mode
- Centralized argument parsing with utility flags
- Environment variable expansion in config files
- Comprehensive operators and condition logic
- Dry-run mode for safe testing
- Idempotency detection for actions

### Fixed
- Updated API endpoints for qBittorrent v5.0 (pause→stop, resume→start)
- Proper boolean parsing in configuration files

### Changed
- Renamed action types to match qBittorrent v5.0 API terminology
- Action 'pause' → 'stop'
- Action 'resume' → 'start'

[Unreleased]: https://github.com/andronics/qbt-rules/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/andronics/qbt-rules/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/andronics/qbt-rules/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/andronics/qbt-rules/releases/tag/v0.0.1

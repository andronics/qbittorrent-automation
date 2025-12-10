# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/YOUR_USERNAME/qbittorrent-automation/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/YOUR_USERNAME/qbittorrent-automation/releases/tag/v0.0.1

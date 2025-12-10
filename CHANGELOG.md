# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions workflows for CI and releases
- Automated version bumping script
- Release automation with changelog generation

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

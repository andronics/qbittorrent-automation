"""Tests for CLI main entry point."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

import pytest

from qbt_rules.cli import main


class TestMain:
    """Test main CLI entry point."""

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    @patch('qbt_rules.cli.QBittorrentAPI')
    @patch('qbt_rules.cli.RulesEngine')
    def test_normal_execution_with_manual_trigger(
        self, mock_rules_engine, mock_api, mock_handle_util, mock_setup_logging,
        mock_load_config, mock_process_args, mock_create_parser
    ):
        """Normal execution with manual trigger."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger=None,
            torrent_hash=None,
            dry_run=False,
            trace=False,
            validate=False,
            list_rules=False
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = False
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {
            'host': 'http://localhost:8080',
            'user': 'admin',
            'pass': 'secret'
        }
        mock_config.is_dry_run.return_value = False
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = False  # No utility args

        # Setup API and engine
        mock_api_instance = Mock()
        mock_api.return_value = mock_api_instance
        mock_engine_instance = Mock()
        mock_rules_engine.return_value = mock_engine_instance

        # Run main
        with patch('sys.exit') as mock_exit:
            main()

        # Verify execution flow
        mock_create_parser.assert_called_once()
        mock_parser.parse_args.assert_called_once()
        mock_process_args.assert_called_once_with(mock_args)
        mock_load_config.assert_called_once_with(Path('/config'))
        mock_setup_logging.assert_called_once_with(mock_config, False)
        mock_handle_util.assert_called_once_with(mock_args, mock_config)

        # Should use manual trigger by default
        mock_engine_instance.run.assert_called_once_with(trigger='manual', torrent_hash=None)
        mock_exit.assert_called_once_with(0)

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    def test_validate_flag_exits_early(
        self, mock_handle_util, mock_setup_logging, mock_load_config,
        mock_process_args, mock_create_parser
    ):
        """--validate flag exits early with code 0."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger=None,
            torrent_hash=None,
            dry_run=False,
            trace=False,
            validate=True,  # Validation flag set
            list_rules=False
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = False
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = True  # Utility arg handled

        # Run main - should exit early
        with patch('sys.exit', side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()

        # Should exit early without creating API/Engine
        mock_exit.assert_called_once_with(0)

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    def test_list_rules_flag_exits_early(
        self, mock_handle_util, mock_setup_logging, mock_load_config,
        mock_process_args, mock_create_parser
    ):
        """--list-rules flag exits early with code 0."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger=None,
            torrent_hash=None,
            dry_run=False,
            trace=False,
            validate=False,
            list_rules=True  # List rules flag set
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = False
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = True  # Utility arg handled

        # Run main - should exit early
        with patch('sys.exit', side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()

        # Should exit early without creating API/Engine
        mock_exit.assert_called_once_with(0)

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    @patch('qbt_rules.cli.validate_torrent_hash')
    @patch('qbt_rules.cli.QBittorrentAPI')
    @patch('qbt_rules.cli.RulesEngine')
    def test_with_torrent_hash_validates_hash(
        self, mock_rules_engine, mock_api, mock_validate_hash, mock_handle_util,
        mock_setup_logging, mock_load_config, mock_process_args, mock_create_parser
    ):
        """With torrent hash, validates the hash."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger='manual',
            torrent_hash='a' * 40,
            dry_run=False,
            trace=False,
            validate=False,
            list_rules=False
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = False
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = False
        mock_validate_hash.return_value = 'a' * 40  # Validated hash

        # Setup API and engine
        mock_api_instance = Mock()
        mock_api.return_value = mock_api_instance
        mock_engine_instance = Mock()
        mock_rules_engine.return_value = mock_engine_instance

        # Run main
        with patch('sys.exit') as mock_exit:
            main()

        # Should validate hash
        mock_validate_hash.assert_called_once_with('a' * 40)

        # Should run with validated hash
        mock_engine_instance.run.assert_called_once_with(trigger='manual', torrent_hash='a' * 40)
        mock_exit.assert_called_once_with(0)

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    @patch('qbt_rules.cli.validate_torrent_hash')
    def test_invalid_torrent_hash_exits_with_error(
        self, mock_validate_hash, mock_handle_util, mock_setup_logging,
        mock_load_config, mock_process_args, mock_create_parser
    ):
        """Invalid torrent hash exits with code 1."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger='manual',
            torrent_hash='invalid',
            dry_run=False,
            trace=False,
            validate=False,
            list_rules=False
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = False
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = False
        mock_validate_hash.side_effect = ValueError("Invalid torrent hash")

        # Run main - should exit with code 1
        with patch('sys.exit', side_effect=SystemExit) as mock_exit:
            with pytest.raises(SystemExit):
                main()

        mock_exit.assert_called_once_with(1)

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    @patch('qbt_rules.cli.QBittorrentAPI')
    @patch('qbt_rules.cli.RulesEngine')
    def test_trigger_agnostic_mode(
        self, mock_rules_engine, mock_api, mock_handle_util, mock_setup_logging,
        mock_load_config, mock_process_args, mock_create_parser
    ):
        """Torrent hash without trigger uses trigger-agnostic mode (trigger=None)."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger=None,  # No trigger specified
            torrent_hash='a' * 40,  # But hash provided
            dry_run=False,
            trace=False,
            validate=False,
            list_rules=False
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = False
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = False

        # Setup API and engine
        mock_api_instance = Mock()
        mock_api.return_value = mock_api_instance
        mock_engine_instance = Mock()
        mock_rules_engine.return_value = mock_engine_instance

        # Run main
        with patch('sys.exit') as mock_exit:
            main()

        # Should use trigger=None (trigger-agnostic mode)
        mock_engine_instance.run.assert_called_once_with(trigger=None, torrent_hash='a' * 40)
        mock_exit.assert_called_once_with(0)

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    @patch('qbt_rules.cli.QBittorrentAPI')
    @patch('qbt_rules.cli.RulesEngine')
    def test_trace_mode_enabled(
        self, mock_rules_engine, mock_api, mock_handle_util, mock_setup_logging,
        mock_load_config, mock_process_args, mock_create_parser
    ):
        """--trace flag enables trace mode in logging."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger=None,
            torrent_hash=None,
            dry_run=False,
            trace=True,  # Trace mode enabled
            validate=False,
            list_rules=False
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = True  # Trace mode enabled in config
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = False
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = False

        # Setup API and engine
        mock_api_instance = Mock()
        mock_api.return_value = mock_api_instance
        mock_engine_instance = Mock()
        mock_rules_engine.return_value = mock_engine_instance

        # Run main
        with patch('sys.exit') as mock_exit:
            main()

        # Should enable trace mode in logging
        mock_setup_logging.assert_called_once_with(mock_config, True)
        mock_exit.assert_called_once_with(0)

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    @patch('qbt_rules.cli.QBittorrentAPI')
    @patch('qbt_rules.cli.RulesEngine')
    def test_dry_run_mode_passed_to_engine(
        self, mock_rules_engine, mock_api, mock_handle_util, mock_setup_logging,
        mock_load_config, mock_process_args, mock_create_parser
    ):
        """--dry-run flag is passed to RulesEngine."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger=None,
            torrent_hash=None,
            dry_run=True,  # Dry run enabled
            trace=False,
            validate=False,
            list_rules=False
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = True  # Dry run enabled in config
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = False

        # Setup API and engine
        mock_api_instance = Mock()
        mock_api.return_value = mock_api_instance
        mock_engine_instance = Mock()
        mock_rules_engine.return_value = mock_engine_instance

        # Run main
        with patch('sys.exit') as mock_exit:
            main()

        # Should pass dry_run to RulesEngine
        mock_rules_engine.assert_called_once_with(mock_api_instance, mock_config, True)
        mock_exit.assert_called_once_with(0)

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    @patch('qbt_rules.cli.QBittorrentAPI')
    @patch('qbt_rules.cli.RulesEngine')
    def test_api_initialized_with_config(
        self, mock_rules_engine, mock_api, mock_handle_util, mock_setup_logging,
        mock_load_config, mock_process_args, mock_create_parser
    ):
        """QBittorrentAPI is initialized with config values."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger=None,
            torrent_hash=None,
            dry_run=False,
            trace=False,
            validate=False,
            list_rules=False
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = False
        mock_config.get_qbittorrent_config.return_value = {
            'host': 'http://localhost:8080',
            'user': 'admin',
            'pass': 'secret'
        }
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = False

        # Setup API and engine
        mock_api_instance = Mock()
        mock_api.return_value = mock_api_instance
        mock_engine_instance = Mock()
        mock_rules_engine.return_value = mock_engine_instance

        # Run main
        with patch('sys.exit') as mock_exit:
            main()

        # Should initialize API with config
        mock_api.assert_called_once_with(
            host='http://localhost:8080',
            username='admin',
            password='secret'
        )
        mock_exit.assert_called_once_with(0)

    @patch('qbt_rules.cli.create_parser')
    @patch('qbt_rules.cli.process_args')
    @patch('qbt_rules.cli.load_config')
    @patch('qbt_rules.cli.setup_logging')
    @patch('qbt_rules.cli.handle_utility_args')
    @patch('qbt_rules.cli.QBittorrentAPI')
    @patch('qbt_rules.cli.RulesEngine')
    def test_with_custom_trigger(
        self, mock_rules_engine, mock_api, mock_handle_util, mock_setup_logging,
        mock_load_config, mock_process_args, mock_create_parser
    ):
        """Custom trigger name is passed to engine."""
        # Setup parser
        mock_parser = Mock()
        mock_create_parser.return_value = mock_parser
        mock_args = Namespace(
            trigger='my_custom_trigger',  # Custom trigger
            torrent_hash=None,
            dry_run=False,
            trace=False,
            validate=False,
            list_rules=False
        )
        mock_parser.parse_args.return_value = mock_args

        # Setup other mocks
        mock_process_args.return_value = Path('/config')
        mock_config = Mock()
        mock_config.get_trace_mode.return_value = False
        mock_config.get_qbittorrent_config.return_value = {"host": "http://localhost:8080", "user": "admin", "pass": "secret"}
        mock_config.is_dry_run.return_value = False
        mock_load_config.return_value = mock_config
        mock_handle_util.return_value = False

        # Setup API and engine
        mock_api_instance = Mock()
        mock_api.return_value = mock_api_instance
        mock_engine_instance = Mock()
        mock_rules_engine.return_value = mock_engine_instance

        # Run main
        with patch('sys.exit') as mock_exit:
            main()

        # Should use custom trigger
        mock_engine_instance.run.assert_called_once_with(trigger='my_custom_trigger', torrent_hash=None)
        mock_exit.assert_called_once_with(0)

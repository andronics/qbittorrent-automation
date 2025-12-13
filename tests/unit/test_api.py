"""Tests for QBittorrentAPI class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from qbt_rules.api import QBittorrentAPI
from qbt_rules.errors import AuthenticationError, ConnectionError, APIError


class TestQBittorrentAPIInit:
    """Test QBittorrentAPI initialization and authentication."""

    @patch('qbt_rules.api.requests.Session')
    def test_successful_initialization_and_login(self, mock_session_class):
        """Successful initialization with valid credentials."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock successful login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'Ok.'
        mock_session.post.return_value = mock_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')

        assert api.host == 'http://localhost:8080'
        assert api.username == 'admin'
        assert api.password == 'password'
        mock_session.post.assert_called_once_with(
            'http://localhost:8080/api/v2/auth/login',
            data={'username': 'admin', 'password': 'password'},
            timeout=10
        )

    @patch('qbt_rules.api.requests.Session')
    def test_init_strips_trailing_slash_from_host(self, mock_session_class):
        """Host URL has trailing slash removed."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'Ok.'
        mock_session.post.return_value = mock_response

        api = QBittorrentAPI('http://localhost:8080/', 'admin', 'password')

        assert api.host == 'http://localhost:8080'

    @patch('qbt_rules.api.requests.Session')
    def test_authentication_failure(self, mock_session_class):
        """Authentication fails with wrong credentials."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock failed login response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = 'Fails.'
        mock_session.post.return_value = mock_response

        with pytest.raises(AuthenticationError, match="Cannot connect to qBittorrent"):
            QBittorrentAPI('http://localhost:8080', 'admin', 'wrongpass')

    @patch('qbt_rules.api.requests.Session')
    def test_connection_error_on_unreachable_host(self, mock_session_class):
        """Connection error when host is unreachable."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock connection error
        mock_session.post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(ConnectionError, match="Cannot reach qBittorrent server"):
            QBittorrentAPI('http://unreachable:8080', 'admin', 'password')

    @patch('qbt_rules.api.requests.Session')
    def test_timeout_during_login(self, mock_session_class):
        """Timeout during login attempt."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock timeout
        mock_session.post.side_effect = requests.exceptions.Timeout("Timeout")

        with pytest.raises(ConnectionError, match="Cannot reach qBittorrent server"):
            QBittorrentAPI('http://slow-host:8080', 'admin', 'password')


class TestAPICallMethod:
    """Test the core _api_call method."""

    @patch('qbt_rules.api.requests.Session')
    def test_successful_get_request(self, mock_session_class):
        """Successful GET request returns data."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock login
        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        # Mock GET request
        get_response = Mock()
        get_response.status_code = 200
        get_response.json.return_value = {'result': 'success'}

        mock_session.post.return_value = login_response
        mock_session.get.return_value = get_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api._api_call('/api/v2/test', method='GET')

        assert result.json() == {'result': 'success'}
        mock_session.get.assert_called_once()

    @patch('qbt_rules.api.requests.Session')
    def test_successful_post_request(self, mock_session_class):
        """Successful POST request returns data."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock login
        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        # Mock POST request
        post_response = Mock()
        post_response.status_code = 201
        post_response.json.return_value = {'created': True}

        mock_session.post.side_effect = [login_response, post_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api._api_call('/api/v2/test', method='POST', data={'key': 'value'})

        assert result.json() == {'created': True}

    @patch('qbt_rules.api.requests.Session')
    def test_session_expiry_with_successful_retry(self, mock_session_class):
        """Session expiry (403) triggers re-login and retry."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock login
        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        # Mock 403 response followed by successful response
        expired_response = Mock()
        expired_response.status_code = 403

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'data': 'after retry'}

        mock_session.post.side_effect = [login_response, login_response]
        mock_session.get.side_effect = [expired_response, success_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api._api_call('/api/v2/test', method='GET')

        assert result.json() == {'data': 'after retry'}
        assert mock_session.post.call_count == 2  # Initial login + re-login

    @patch('qbt_rules.api.requests.Session')
    def test_session_expiry_with_post_retry_successful(self, mock_session_class):
        """Session expiry (403) on POST request triggers re-login and successful retry."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock login
        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        # Mock 403 response followed by successful response (for POST requests)
        expired_response = Mock()
        expired_response.status_code = 403

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'data': 'after retry'}

        # First post is login, second returns 403, third is re-login, fourth succeeds
        mock_session.post.side_effect = [login_response, expired_response, login_response, success_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api._api_call('/api/v2/test', method='POST', data={'key': 'value'})

        assert result.json() == {'data': 'after retry'}
        assert mock_session.post.call_count == 4  # Initial login + POST (403) + re-login + POST retry

    @patch('qbt_rules.api.requests.Session')
    def test_session_expiry_with_failed_retry(self, mock_session_class):
        """Session expiry with failed re-login raises error."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock initial login success
        login_success = Mock()
        login_success.status_code = 200
        login_success.text = 'Ok.'

        # Mock re-login failure
        login_fail = Mock()
        login_fail.status_code = 403
        login_fail.text = 'Fails.'

        # Mock 403 response
        expired_response = Mock()
        expired_response.status_code = 403

        mock_session.post.side_effect = [login_success, login_fail]
        mock_session.get.return_value = expired_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')

        with pytest.raises(AuthenticationError):
            api._api_call('/api/v2/test', method='GET')

    @patch('qbt_rules.api.requests.Session')
    def test_api_error_on_400_status(self, mock_session_class):
        """400 status code raises APIError."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        error_response = Mock()
        error_response.status_code = 400
        error_response.text = 'Bad Request'

        mock_session.post.return_value = login_response
        mock_session.get.return_value = error_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')

        with pytest.raises(APIError, match="qBittorrent API request failed"):
            api._api_call('/api/v2/test', method='GET')

    @patch('qbt_rules.api.requests.Session')
    def test_api_error_on_500_status(self, mock_session_class):
        """500 status code raises APIError."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        error_response = Mock()
        error_response.status_code = 500
        error_response.text = 'Internal Server Error'

        mock_session.post.return_value = login_response
        mock_session.get.return_value = error_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')

        with pytest.raises(APIError, match="qBittorrent API request failed"):
            api._api_call('/api/v2/test', method='GET')

    @patch('qbt_rules.api.requests.Session')
    def test_connection_error_during_api_call(self, mock_session_class):
        """Connection error during API call raises ConnectionError."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        mock_session.post.return_value = login_response
        mock_session.get.side_effect = requests.exceptions.ConnectionError("Network error")

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')

        with pytest.raises(ConnectionError, match="Cannot reach qBittorrent server"):
            api._api_call('/api/v2/test', method='GET')

    @patch('qbt_rules.api.requests.Session')
    def test_timeout_during_api_call(self, mock_session_class):
        """Timeout during API call raises ConnectionError."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        mock_session.post.return_value = login_response
        mock_session.get.side_effect = requests.exceptions.Timeout("Request timeout")

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')

        with pytest.raises(ConnectionError, match="Cannot reach qBittorrent server"):
            api._api_call('/api/v2/test', method='GET')


class TestTorrentInformationMethods:
    """Test torrent information retrieval methods."""

    @patch('qbt_rules.api.requests.Session')
    def test_get_torrents_no_filters(self, mock_session_class):
        """get_torrents with no filters."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        torrents_response = Mock()
        torrents_response.status_code = 200
        torrents_response.json.return_value = [{'hash': 'abc123', 'name': 'Test'}]

        mock_session.post.return_value = login_response
        mock_session.get.return_value = torrents_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api.get_torrents()

        assert result == [{'hash': 'abc123', 'name': 'Test'}]
        # Verify params were passed correctly
        call_args = mock_session.get.call_args
        assert 'params' in call_args.kwargs
        assert call_args.kwargs['params'] == {}

    @patch('qbt_rules.api.requests.Session')
    def test_get_torrents_with_filter_type(self, mock_session_class):
        """get_torrents with filter_type parameter."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        torrents_response = Mock()
        torrents_response.status_code = 200
        torrents_response.json.return_value = []

        mock_session.post.return_value = login_response
        mock_session.get.return_value = torrents_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.get_torrents(filter_type='downloading')

        call_args = mock_session.get.call_args
        assert call_args.kwargs['params'] == {'filter': 'downloading'}

    @patch('qbt_rules.api.requests.Session')
    def test_get_torrents_with_category(self, mock_session_class):
        """get_torrents with category parameter."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        torrents_response = Mock()
        torrents_response.status_code = 200
        torrents_response.json.return_value = []

        mock_session.post.return_value = login_response
        mock_session.get.return_value = torrents_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.get_torrents(category='movies')

        call_args = mock_session.get.call_args
        assert call_args.kwargs['params'] == {'category': 'movies'}

    @patch('qbt_rules.api.requests.Session')
    def test_get_torrents_with_tag(self, mock_session_class):
        """get_torrents with tag parameter."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        torrents_response = Mock()
        torrents_response.status_code = 200
        torrents_response.json.return_value = []

        mock_session.post.return_value = login_response
        mock_session.get.return_value = torrents_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.get_torrents(tag='important')

        call_args = mock_session.get.call_args
        assert call_args.kwargs['params'] == {'tag': 'important'}

    @patch('qbt_rules.api.requests.Session')
    def test_get_torrents_with_multiple_filters(self, mock_session_class):
        """get_torrents with multiple filter parameters."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        torrents_response = Mock()
        torrents_response.status_code = 200
        torrents_response.json.return_value = []

        mock_session.post.return_value = login_response
        mock_session.get.return_value = torrents_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.get_torrents(filter_type='seeding', category='tv', tag='hd')

        call_args = mock_session.get.call_args
        assert call_args.kwargs['params'] == {
            'filter': 'seeding',
            'category': 'tv',
            'tag': 'hd'
        }

    @patch('qbt_rules.api.requests.Session')
    def test_get_properties(self, mock_session_class):
        """get_properties returns torrent properties."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        props_response = Mock()
        props_response.status_code = 200
        props_response.json.return_value = {'save_path': '/downloads'}

        mock_session.post.return_value = login_response
        mock_session.get.return_value = props_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api.get_properties('abc123')

        assert result == {'save_path': '/downloads'}
        call_args = mock_session.get.call_args
        assert call_args.kwargs['params']['hash'] == 'abc123'

    @patch('qbt_rules.api.requests.Session')
    def test_get_trackers(self, mock_session_class):
        """get_trackers returns tracker list."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        trackers_response = Mock()
        trackers_response.status_code = 200
        trackers_response.json.return_value = [{'url': 'http://tracker.example.com'}]

        mock_session.post.return_value = login_response
        mock_session.get.return_value = trackers_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api.get_trackers('abc123')

        assert result == [{'url': 'http://tracker.example.com'}]

    @patch('qbt_rules.api.requests.Session')
    def test_get_files(self, mock_session_class):
        """get_files returns file list."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        files_response = Mock()
        files_response.status_code = 200
        files_response.json.return_value = [{'name': 'file1.txt'}]

        mock_session.post.return_value = login_response
        mock_session.get.return_value = files_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api.get_files('abc123')

        assert result == [{'name': 'file1.txt'}]

    @patch('qbt_rules.api.requests.Session')
    def test_get_webseeds(self, mock_session_class):
        """get_webseeds returns webseed list."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        webseeds_response = Mock()
        webseeds_response.status_code = 200
        webseeds_response.json.return_value = [{'url': 'http://webseed.example.com'}]

        mock_session.post.return_value = login_response
        mock_session.get.return_value = webseeds_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api.get_webseeds('abc123')

        assert result == [{'url': 'http://webseed.example.com'}]

    @patch('qbt_rules.api.requests.Session')
    def test_get_peers_transforms_dict_to_list(self, mock_session_class):
        """get_peers transforms dict response to list with injected IDs."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        # Mock response as dict (qBittorrent format)
        peers_response = Mock()
        peers_response.status_code = 200
        peers_response.json.return_value = {'peers': {
            'peer1': {'ip': '192.168.1.1', 'port': 6881},
            'peer2': {'ip': '192.168.1.2', 'port': 6882}}
        }

        mock_session.post.return_value = login_response
        mock_session.get.return_value = peers_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api.get_peers('abc123')

        # Should return list with id injected
        assert isinstance(result, list)
        assert len(result) == 2
        assert {'id': 'peer1', 'ip': '192.168.1.1', 'port': 6881} in result
        assert {'id': 'peer2', 'ip': '192.168.1.2', 'port': 6882} in result


class TestGlobalInformationMethods:
    """Test global information methods."""

    @patch('qbt_rules.api.requests.Session')
    def test_get_transfer_info(self, mock_session_class):
        """get_transfer_info returns transfer statistics."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        transfer_response = Mock()
        transfer_response.status_code = 200
        transfer_response.json.return_value = {'dl_info_speed': 1000000}

        mock_session.post.return_value = login_response
        mock_session.get.return_value = transfer_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api.get_transfer_info()

        assert result == {'dl_info_speed': 1000000}

    @patch('qbt_rules.api.requests.Session')
    def test_get_app_preferences(self, mock_session_class):
        """get_app_preferences returns application preferences."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        prefs_response = Mock()
        prefs_response.status_code = 200
        prefs_response.json.return_value = {'max_connec': 500}

        mock_session.post.return_value = login_response
        mock_session.get.return_value = prefs_response

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api.get_app_preferences()

        assert result == {'max_connec': 500}


class TestTorrentControlMethods:
    """Test torrent control methods."""

    @patch('qbt_rules.api.requests.Session')
    def test_stop_torrents_single_hash(self, mock_session_class):
        """stop_torrents with single hash."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        stop_response = Mock()
        stop_response.status_code = 200
        stop_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, stop_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        result = api.stop_torrents(['abc123'])

        assert result is True
        # Verify hashes were pipe-joined
        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data'] == {'hashes': 'abc123'}

    @patch('qbt_rules.api.requests.Session')
    def test_stop_torrents_multiple_hashes(self, mock_session_class):
        """stop_torrents with multiple hashes uses pipe separator."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        stop_response = Mock()
        stop_response.status_code = 200
        stop_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, stop_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.stop_torrents(['abc123', 'def456', 'ghi789'])

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data'] == {'hashes': 'abc123|def456|ghi789'}

    @patch('qbt_rules.api.requests.Session')
    def test_start_torrents(self, mock_session_class):
        """start_torrents sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        start_response = Mock()
        start_response.status_code = 200
        start_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, start_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.start_torrents(['abc123'])

        call_args = mock_session.post.call_args_list[1]
        assert '/api/v2/torrents/start' in call_args.args[0]

    @patch('qbt_rules.api.requests.Session')
    def test_force_start_torrents(self, mock_session_class):
        """force_start_torrents sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        force_start_response = Mock()
        force_start_response.status_code = 200
        force_start_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, force_start_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.force_start_torrents(['abc123'])

        call_args = mock_session.post.call_args_list[1]
        assert '/api/v2/torrents/setForceStart' in call_args.args[0]
        assert call_args.kwargs['data'] == {'hashes': 'abc123', 'value': 'true'}

    @patch('qbt_rules.api.requests.Session')
    def test_recheck_torrents(self, mock_session_class):
        """recheck_torrents sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        recheck_response = Mock()
        recheck_response.status_code = 200
        recheck_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, recheck_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.recheck_torrents(['abc123'])

        call_args = mock_session.post.call_args_list[1]
        assert '/api/v2/torrents/recheck' in call_args.args[0]

    @patch('qbt_rules.api.requests.Session')
    def test_reannounce_torrents(self, mock_session_class):
        """reannounce_torrents sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        reannounce_response = Mock()
        reannounce_response.status_code = 200
        reannounce_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, reannounce_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.reannounce_torrents(['abc123'])

        call_args = mock_session.post.call_args_list[1]
        assert '/api/v2/torrents/reannounce' in call_args.args[0]

    @patch('qbt_rules.api.requests.Session')
    def test_delete_torrents_keep_files(self, mock_session_class):
        """delete_torrents with delete_files=False."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        delete_response = Mock()
        delete_response.status_code = 200
        delete_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, delete_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.delete_torrents(['abc123'], delete_files=False)

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data'] == {
            'hashes': 'abc123',
            'deleteFiles': 'false'
        }

    @patch('qbt_rules.api.requests.Session')
    def test_delete_torrents_delete_files(self, mock_session_class):
        """delete_torrents with delete_files=True."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        delete_response = Mock()
        delete_response.status_code = 200
        delete_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, delete_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.delete_torrents(['abc123'], delete_files=True)

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data']['deleteFiles'] == 'true'


class TestCategoryAndTagMethods:
    """Test category and tag management methods."""

    @patch('qbt_rules.api.requests.Session')
    def test_set_category(self, mock_session_class):
        """set_category sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        category_response = Mock()
        category_response.status_code = 200
        category_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, category_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.set_category(['abc123'], 'movies')

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data'] == {
            'hashes': 'abc123',
            'category': 'movies'
        }

    @patch('qbt_rules.api.requests.Session')
    def test_add_tags_single_tag(self, mock_session_class):
        """add_tags with single tag."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        tags_response = Mock()
        tags_response.status_code = 200
        tags_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, tags_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.add_tags(['abc123'], ['important'])

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data'] == {
            'hashes': 'abc123',
            'tags': 'important'
        }

    @patch('qbt_rules.api.requests.Session')
    def test_add_tags_multiple_tags(self, mock_session_class):
        """add_tags with multiple tags uses comma separator."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        tags_response = Mock()
        tags_response.status_code = 200
        tags_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, tags_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.add_tags(['abc123'], ['tag1', 'tag2', 'tag3'])

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data']['tags'] == 'tag1,tag2,tag3'

    @patch('qbt_rules.api.requests.Session')
    def test_remove_tags(self, mock_session_class):
        """remove_tags sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        tags_response = Mock()
        tags_response.status_code = 200
        tags_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, tags_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.remove_tags(['abc123'], ['old-tag'])

        call_args = mock_session.post.call_args_list[1]
        assert '/api/v2/torrents/removeTags' in call_args.args[0]


class TestLimitMethods:
    """Test limit setting methods."""

    @patch('qbt_rules.api.requests.Session')
    def test_set_upload_limit(self, mock_session_class):
        """set_upload_limit sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        limit_response = Mock()
        limit_response.status_code = 200
        limit_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, limit_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.set_upload_limit(['abc123'], 1000000)

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data'] == {
            'hashes': 'abc123',
            'limit': 1000000
        }

    @patch('qbt_rules.api.requests.Session')
    def test_set_download_limit(self, mock_session_class):
        """set_download_limit sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        limit_response = Mock()
        limit_response.status_code = 200
        limit_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, limit_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.set_download_limit(['abc123'], 500000)

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data'] == {
            'hashes': 'abc123',
            'limit': 500000
        }

    @patch('qbt_rules.api.requests.Session')
    def test_set_share_limits_default_values(self, mock_session_class):
        """set_share_limits with default values (-2)."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        limits_response = Mock()
        limits_response.status_code = 200
        limits_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, limits_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.set_share_limits(['abc123'])

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data'] == {
            'hashes': 'abc123',
            'ratioLimit': -2,
            'seedingTimeLimit': -2
        }

    @patch('qbt_rules.api.requests.Session')
    def test_set_share_limits_custom_values(self, mock_session_class):
        """set_share_limits with custom ratio and time limits."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        limits_response = Mock()
        limits_response.status_code = 200
        limits_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, limits_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.set_share_limits(['abc123'], ratio_limit=2.0, seeding_time_limit=1440)

        call_args = mock_session.post.call_args_list[1]
        assert call_args.kwargs['data'] == {
            'hashes': 'abc123',
            'ratioLimit': 2.0,
            'seedingTimeLimit': 1440
        }


class TestPriorityMethods:
    """Test priority management methods."""

    @patch('qbt_rules.api.requests.Session')
    def test_increase_priority(self, mock_session_class):
        """increase_priority sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        priority_response = Mock()
        priority_response.status_code = 200
        priority_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, priority_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.increase_priority(['abc123'])

        call_args = mock_session.post.call_args_list[1]
        assert '/api/v2/torrents/increasePrio' in call_args.args[0]

    @patch('qbt_rules.api.requests.Session')
    def test_decrease_priority(self, mock_session_class):
        """decrease_priority sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        priority_response = Mock()
        priority_response.status_code = 200
        priority_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, priority_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.decrease_priority(['abc123'])

        call_args = mock_session.post.call_args_list[1]
        assert '/api/v2/torrents/decreasePrio' in call_args.args[0]

    @patch('qbt_rules.api.requests.Session')
    def test_set_top_priority(self, mock_session_class):
        """set_top_priority sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        priority_response = Mock()
        priority_response.status_code = 200
        priority_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, priority_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.set_top_priority(['abc123'])

        call_args = mock_session.post.call_args_list[1]
        assert '/api/v2/torrents/topPrio' in call_args.args[0]

    @patch('qbt_rules.api.requests.Session')
    def test_set_bottom_priority(self, mock_session_class):
        """set_bottom_priority sends correct API call."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        login_response = Mock()
        login_response.status_code = 200
        login_response.text = 'Ok.'

        priority_response = Mock()
        priority_response.status_code = 200
        priority_response.json.return_value = {}

        mock_session.post.side_effect = [login_response, priority_response]

        api = QBittorrentAPI('http://localhost:8080', 'admin', 'password')
        api.set_bottom_priority(['abc123'])

        call_args = mock_session.post.call_args_list[1]
        assert '/api/v2/torrents/bottomPrio' in call_args.args[0]

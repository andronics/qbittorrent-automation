"""
qBittorrent Web API client
Complete implementation of qBittorrent Web API v2 (>= v5.0)
"""

import requests
from typing import List, Dict, Any, Optional

from qbt_rules.errors import AuthenticationError, ConnectionError, APIError
from qbt_rules.logging import get_logger

logger = get_logger(__name__)


class QBittorrentAPI:
    """qBittorrent Web API client"""

    def __init__(self, host: str, username: str, password: str):
        """
        Initialize API client and authenticate

        Args:
            host: qBittorrent host URL (e.g., 'http://localhost:8080')
            username: qBittorrent username
            password: qBittorrent password

        Raises:
            AuthenticationError: If login fails
            ConnectionError: If cannot reach server
        """
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._login()

    def _login(self):
        """Authenticate with qBittorrent"""
        try:
            response = self.session.post(
                f"{self.host}/api/v2/auth/login",
                data={"username": self.username, "password": self.password},
                timeout=10
            )

            if response.text != "Ok.":
                raise AuthenticationError(self.host, response.text)

            logger.info(f"Successfully authenticated with qBittorrent at {self.host}")

        except requests.exceptions.RequestException as e:
            raise ConnectionError(self.host, str(e))

    def _api_call(self, endpoint: str, method: str = 'POST', data: Optional[Dict] = None,
                  params: Optional[Dict] = None, timeout: int = 30) -> requests.Response:
        """
        Generic API call wrapper with error handling

        Args:
            endpoint: API endpoint (e.g., '/api/v2/torrents/info')
            method: HTTP method ('GET' or 'POST')
            data: POST data
            params: URL parameters
            timeout: Request timeout in seconds

        Returns:
            Response object

        Raises:
            ConnectionError: If cannot reach server
            APIError: If API returns error status
        """
        url = f"{self.host}{endpoint}"

        try:
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=timeout)
            else:
                response = self.session.post(url, data=data, params=params, timeout=timeout)

            # Check for common error status codes
            if response.status_code == 403:
                # Re-login and retry once
                logger.warning("Session expired, re-authenticating...")
                self._login()

                if method == 'GET':
                    response = self.session.get(url, params=params, timeout=timeout)
                else:
                    response = self.session.post(url, data=data, params=params, timeout=timeout)

            if response.status_code not in [200, 201]:
                raise APIError(endpoint, response.status_code, response.text)

            return response

        except requests.exceptions.RequestException as e:
            raise ConnectionError(self.host, str(e))

    # Torrent Information Methods

    def get_torrents(self, filter_type: Optional[str] = None, category: Optional[str] = None,
                     tag: Optional[str] = None) -> List[Dict]:
        """
        Get list of torrents

        Args:
            filter_type: Filter by state (e.g., 'downloading', 'seeding', 'completed')
            category: Filter by category
            tag: Filter by tag

        Returns:
            List of torrent dictionaries
        """
        params = {}
        if filter_type:
            params['filter'] = filter_type
        if category:
            params['category'] = category
        if tag:
            params['tag'] = tag

        response = self._api_call('/api/v2/torrents/info', method='GET', params=params)
        return response.json()

    def get_properties(self, torrent_hash: str) -> Dict:
        """
        Get detailed torrent properties

        Args:
            torrent_hash: Torrent hash

        Returns:
            Properties dictionary
        """
        response = self._api_call(
            '/api/v2/torrents/properties',
            method='GET',
            params={'hash': torrent_hash}
        )
        return response.json()

    def get_trackers(self, torrent_hash: str) -> List[Dict]:
        """
        Get tracker information for a torrent

        Args:
            torrent_hash: Torrent hash

        Returns:
            List of tracker dictionaries
        """
        response = self._api_call(
            '/api/v2/torrents/trackers',
            method='GET',
            params={'hash': torrent_hash}
        )
        return response.json()

    def get_files(self, torrent_hash: str) -> List[Dict]:
        """
        Get file list for a torrent

        Args:
            torrent_hash: Torrent hash

        Returns:
            List of file dictionaries
        """
        response = self._api_call(
            '/api/v2/torrents/files',
            method='GET',
            params={'hash': torrent_hash}
        )
        return response.json()

    def get_webseeds(self, torrent_hash: str) -> List[Dict]:
        """
        Get web seeds for a torrent

        Args:
            torrent_hash: Torrent hash

        Returns:
            List of web seed dictionaries
        """
        response = self._api_call(
            '/api/v2/torrents/webseeds',
            method='GET',
            params={'hash': torrent_hash}
        )
        return response.json()

    def get_peers(self, torrent_hash: str) -> List[Dict]:
        """
        Get peer information for a torrent

        Args:
            torrent_hash: Torrent hash

        Returns:
            Dictionary of peers (peer_id -> peer_data)
        """
        response = self._api_call(
            '/api/v2/sync/torrentPeers',
            method='GET',
            params={'hash': torrent_hash}
        )
        # Convert peers dict to list of dicts for consistency
        peers_dict = response.json().get('peers', {})
        return [{'id': peer_id, **peer_data} for peer_id, peer_data in peers_dict.items()]

    # Global Information Methods

    def get_transfer_info(self) -> Dict:
        """
        Get global transfer information

        Returns:
            Transfer info dictionary with speeds, data transferred, etc.
        """
        response = self._api_call('/api/v2/transfer/info', method='GET')
        return response.json()

    def get_app_preferences(self) -> Dict:
        """
        Get application preferences

        Returns:
            Preferences dictionary
        """
        response = self._api_call('/api/v2/app/preferences', method='GET')
        return response.json()

    # Torrent Control Methods

    def stop_torrents(self, hashes: List[str]) -> bool:
        """Stop torrents (pause in qBittorrent v5.0+)"""
        self._api_call(
            '/api/v2/torrents/stop',
            data={'hashes': '|'.join(hashes)}
        )
        return True

    def start_torrents(self, hashes: List[str]) -> bool:
        """Start torrents (resume in qBittorrent v5.0+)"""
        self._api_call(
            '/api/v2/torrents/start',
            data={'hashes': '|'.join(hashes)}
        )
        return True

    def force_start_torrents(self, hashes: List[str]) -> bool:
        """Force start torrents"""
        self._api_call(
            '/api/v2/torrents/setForceStart',
            data={'hashes': '|'.join(hashes), 'value': 'true'}
        )
        return True

    def recheck_torrents(self, hashes: List[str]) -> bool:
        """Recheck torrents"""
        self._api_call(
            '/api/v2/torrents/recheck',
            data={'hashes': '|'.join(hashes)}
        )
        return True

    def reannounce_torrents(self, hashes: List[str]) -> bool:
        """Reannounce torrents to trackers"""
        self._api_call(
            '/api/v2/torrents/reannounce',
            data={'hashes': '|'.join(hashes)}
        )
        return True

    def delete_torrents(self, hashes: List[str], delete_files: bool) -> bool:
        """Delete torrents"""
        self._api_call(
            '/api/v2/torrents/delete',
            data={
                'hashes': '|'.join(hashes),
                'deleteFiles': 'true' if delete_files else 'false'
            }
        )
        return True

    # Category and Tag Methods

    def set_category(self, hashes: List[str], category: str) -> bool:
        """Set category"""
        self._api_call(
            '/api/v2/torrents/setCategory',
            data={'hashes': '|'.join(hashes), 'category': category}
        )
        return True

    def add_tags(self, hashes: List[str], tags: List[str]) -> bool:
        """Add tags"""
        self._api_call(
            '/api/v2/torrents/addTags',
            data={'hashes': '|'.join(hashes), 'tags': ','.join(tags)}
        )
        return True

    def remove_tags(self, hashes: List[str], tags: List[str]) -> bool:
        """Remove tags"""
        self._api_call(
            '/api/v2/torrents/removeTags',
            data={'hashes': '|'.join(hashes), 'tags': ','.join(tags)}
        )
        return True

    # Limit Methods

    def set_upload_limit(self, hashes: List[str], limit: int) -> bool:
        """Set upload limit (bytes/s, -1 for unlimited)"""
        self._api_call(
            '/api/v2/torrents/setUploadLimit',
            data={'hashes': '|'.join(hashes), 'limit': limit}
        )
        return True

    def set_download_limit(self, hashes: List[str], limit: int) -> bool:
        """Set download limit (bytes/s, -1 for unlimited)"""
        self._api_call(
            '/api/v2/torrents/setDownloadLimit',
            data={'hashes': '|'.join(hashes), 'limit': limit}
        )
        return True

    def set_share_limits(self, hashes: List[str], ratio_limit: float = -2,
                         seeding_time_limit: int = -2) -> bool:
        """
        Set share limits

        Args:
            hashes: List of torrent hashes
            ratio_limit: Max ratio (-2=global, -1=unlimited, >=0=limit)
            seeding_time_limit: Max seeding time in minutes (-2=global, -1=unlimited, >=0=limit)
        """
        self._api_call(
            '/api/v2/torrents/setShareLimits',
            data={
                'hashes': '|'.join(hashes),
                'ratioLimit': ratio_limit,
                'seedingTimeLimit': seeding_time_limit
            }
        )
        return True

    # Priority Methods

    def increase_priority(self, hashes: List[str]) -> bool:
        """Increase torrent priority"""
        self._api_call(
            '/api/v2/torrents/increasePrio',
            data={'hashes': '|'.join(hashes)}
        )
        return True

    def decrease_priority(self, hashes: List[str]) -> bool:
        """Decrease torrent priority"""
        self._api_call(
            '/api/v2/torrents/decreasePrio',
            data={'hashes': '|'.join(hashes)}
        )
        return True

    def set_top_priority(self, hashes: List[str]) -> bool:
        """Set maximum priority"""
        self._api_call(
            '/api/v2/torrents/topPrio',
            data={'hashes': '|'.join(hashes)}
        )
        return True

    def set_bottom_priority(self, hashes: List[str]) -> bool:
        """Set minimum priority"""
        self._api_call(
            '/api/v2/torrents/bottomPrio',
            data={'hashes': '|'.join(hashes)}
        )
        return True

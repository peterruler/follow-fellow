#!/usr/bin/env python3
"""
Unit Tests für Follow-Fellow
Umfassende Tests für GitHubFollowManager und FollowAnalyzer
"""

import pytest
import json
import os
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests

# Import der zu testenden Module
from follow_fellow import GitHubFollowManager, FollowAnalyzer, app


class TestGitHubFollowManager:
    """Tests für die GitHubFollowManager Klasse"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.username = "testuser"
        self.token = "test_token_123"
        self.manager = GitHubFollowManager(self.username, self.token)
    
    def test_init(self):
        """Test der Initialisierung"""
        assert self.manager.username == "testuser"
        assert self.manager.token == "test_token_123"
        assert self.manager.base_url == "https://api.github.com"
        assert self.manager.request_count == 0
        assert self.manager.max_requests == int(os.getenv('MAX_API_REQUESTS', 2500))
        assert self.manager.max_users_to_process == int(os.getenv('MAX_USERS_TO_PROCESS', 200))
        
        # Test Header
        expected_headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Follow-Fellow/1.0"
        }
        assert self.manager.headers == expected_headers
    
    @patch.dict(os.environ, {'MAX_API_REQUESTS': '1000', 'MAX_USERS_TO_PROCESS': '50'})
    def test_init_with_env_vars(self):
        """Test Initialisierung mit Umgebungsvariablen"""
        manager = GitHubFollowManager("user", "token")
        assert manager.max_requests == 1000
        assert manager.max_users_to_process == 50
    
    @patch('follow_fellow.requests.Session.request')
    def test_make_request_success(self, mock_request):
        """Test erfolgreiche API-Anfrage"""
        # Mock Response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'X-RateLimit-Remaining': '4999',
            'X-RateLimit-Limit': '5000',
            'X-RateLimit-Reset': str(int(time.time()) + 3600)
        }
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Test
        result = self.manager._make_request("https://api.github.com/test")
        
        # Assertions
        assert self.manager.request_count == 1
        assert self.manager.last_rate_limit_remaining == 4999
        assert self.manager.last_rate_limit_total == 5000
        assert result == mock_response
        mock_request.assert_called_once()
    
    @patch('follow_fellow.requests.Session.request')
    def test_make_request_rate_limit_tracking(self, mock_request):
        """Test Rate Limit Tracking"""
        mock_response = Mock()
        mock_response.headers = {
            'X-RateLimit-Remaining': '10',
            'X-RateLimit-Limit': '5000',
            'X-RateLimit-Reset': str(int(time.time()) + 3600)
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        self.manager._make_request("https://api.github.com/test")
        
        assert self.manager.last_rate_limit_remaining == 10
        assert self.manager.last_rate_limit_total == 5000
    
    @patch('follow_fellow.requests.Session.request')
    def test_make_request_api_error(self, mock_request):
        """Test API-Fehlerbehandlung"""
        # Mock Response für erfolgreichen Request, aber raise_for_status() wirft Fehler
        mock_response = MagicMock()
        mock_response.headers = {
            'X-RateLimit-Remaining': '5000',
            'X-RateLimit-Limit': '5000',
            'X-RateLimit-Reset': str(int(time.time()) + 3600)
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_request.return_value = mock_response
        
        with pytest.raises(requests.exceptions.HTTPError):
            self.manager._make_request("https://api.github.com/test")
        
        assert self.manager.request_count == 1
    
    def test_get_request_status(self):
        """Test Request-Status Abruf"""
        self.manager.request_count = 100
        self.manager.max_requests = 2500
        self.manager.last_rate_limit_remaining = 4900
        self.manager.last_rate_limit_total = 5000
        self.manager.last_rate_limit_reset = int(time.time()) + 3600
        
        status = self.manager.get_request_status()
        
        assert status['current_requests'] == 100
        assert status['max_requests'] == 2500
        assert status['remaining_requests'] == 2400
        assert status['usage_percentage'] == 4.0
        assert status['max_users_to_process'] == int(os.getenv('MAX_USERS_TO_PROCESS', 200))
        assert 'github_rate_limit' in status
        assert status['github_rate_limit']['remaining'] == 4900
    
    @patch('follow_fellow.GitHubFollowManager._make_request')
    def test_get_all_paginated_single_page(self, mock_request):
        """Test paginierte Anfrage mit einer Seite"""
        mock_response = Mock()
        mock_response.json.return_value = [{"login": "user1"}, {"login": "user2"}]
        mock_response.headers = {'Link': ''}
        mock_request.return_value = mock_response
        
        result = self.manager.get_all_paginated("/test/endpoint")
        
        assert len(result) == 2
        assert result[0]["login"] == "user1"
        assert result[1]["login"] == "user2"
        mock_request.assert_called_once_with("https://api.github.com/test/endpoint")
    
    @patch('follow_fellow.GitHubFollowManager._make_request')
    def test_get_all_paginated_multiple_pages(self, mock_request):
        """Test paginierte Anfrage mit mehreren Seiten"""
        # Erste Seite
        mock_response1 = Mock()
        mock_response1.json.return_value = [{"login": "user1"}]
        mock_response1.headers = {'Link': '<https://api.github.com/test/endpoint?page=2>; rel="next"'}
        
        # Zweite Seite
        mock_response2 = Mock()
        mock_response2.json.return_value = [{"login": "user2"}]
        mock_response2.headers = {'Link': ''}
        
        mock_request.side_effect = [mock_response1, mock_response2]
        
        result = self.manager.get_all_paginated("/test/endpoint")
        
        assert len(result) == 2
        assert result[0]["login"] == "user1"
        assert result[1]["login"] == "user2"
        assert mock_request.call_count == 2
    
    @patch('follow_fellow.GitHubFollowManager.get_all_paginated')
    def test_get_followers(self, mock_paginated):
        """Test Follower-Abruf"""
        mock_paginated.return_value = [
            {"login": "follower1"},
            {"login": "follower2"},
            {"login": "follower3"}
        ]
        
        followers = self.manager.get_followers()
        
        assert len(followers) == 3
        assert "follower1" in followers
        assert "follower2" in followers
        assert "follower3" in followers
        mock_paginated.assert_called_once_with("/users/testuser/followers")
    
    @patch('follow_fellow.GitHubFollowManager.get_all_paginated')
    def test_get_following(self, mock_paginated):
        """Test Following-Abruf"""
        mock_paginated.return_value = [
            {"login": "following1"},
            {"login": "following2"}
        ]
        
        following = self.manager.get_following()
        
        assert len(following) == 2
        assert "following1" in following
        assert "following2" in following
        mock_paginated.assert_called_once_with("/users/testuser/following")
    
    @patch('follow_fellow.GitHubFollowManager._make_request')
    def test_unfollow_user_success(self, mock_request):
        """Test erfolgreiches Entfolgen"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response
        
        result = self.manager.unfollow_user("testuser")
        
        assert result is True
        mock_request.assert_called_once_with("https://api.github.com/user/following/testuser", "DELETE")
    
    @patch('follow_fellow.GitHubFollowManager._make_request')
    def test_unfollow_user_failure(self, mock_request):
        """Test fehlgeschlagenes Entfolgen"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        result = self.manager.unfollow_user("testuser")
        
        assert result is False
    
    @patch('follow_fellow.GitHubFollowManager._make_request')
    def test_unfollow_user_exception(self, mock_request):
        """Test Exception beim Entfolgen"""
        mock_request.side_effect = Exception("API Error")
        
        result = self.manager.unfollow_user("testuser")
        
        assert result is False
    
    @patch('follow_fellow.GitHubFollowManager._make_request')
    def test_get_user_info_success(self, mock_request):
        """Test erfolgreicher User-Info Abruf"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "login": "testuser",
            "name": "Test User",
            "bio": "Test bio",
            "followers": 100,
            "following": 50,
            "public_repos": 25
        }
        mock_request.return_value = mock_response
        
        user_info = self.manager.get_user_info("testuser")
        
        assert user_info["login"] == "testuser"
        assert user_info["name"] == "Test User"
        assert user_info["followers"] == 100
        mock_request.assert_called_once_with("https://api.github.com/users/testuser")
    
    @patch('follow_fellow.GitHubFollowManager._make_request')
    def test_get_user_info_exception(self, mock_request):
        """Test Exception beim User-Info Abruf"""
        mock_request.side_effect = Exception("API Error")
        
        user_info = self.manager.get_user_info("testuser")
        
        assert user_info == {}


class TestFollowAnalyzer:
    """Tests für die FollowAnalyzer Klasse"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.manager = Mock(spec=GitHubFollowManager)
        self.manager.username = "testuser"
        self.manager.max_users_to_process = 200
        self.analyzer = FollowAnalyzer(self.manager)
    
    def test_init(self):
        """Test der Initialisierung"""
        assert self.analyzer.manager == self.manager
    
    def test_analyze_follows(self):
        """Test der Follow-Analyse"""
        # Mock Daten
        followers = {"user1", "user2", "user3", "user4"}
        following = {"user2", "user3", "user5", "user6"}
        
        self.manager.get_followers.return_value = followers
        self.manager.get_following.return_value = following
        
        one_way, mutual, followers_result, not_following_back = self.analyzer.analyze_follows()
        
        # Assertions
        assert one_way == {"user5", "user6"}  # Following but not followers
        assert mutual == {"user2", "user3"}   # Both following and followers
        assert followers_result == followers
        assert not_following_back == {"user1", "user4"}  # Followers but not following
    
    @patch('follow_fellow.GitHubFollowManager.get_user_info')
    def test_generate_report(self, mock_get_user_info):
        """Test der Report-Generierung"""
        # Setup
        followers = {"user1", "user2"}
        following = {"user2", "user3"}
        
        self.manager.get_followers.return_value = followers
        self.manager.get_following.return_value = following
        self.manager.last_rate_limit_remaining = 4000
        
        # Mock User Info
        mock_get_user_info.return_value = {
            "name": "Test User",
            "bio": "Test bio",
            "followers": 100,
            "following": 50,
            "public_repos": 25,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "html_url": "https://github.com/testuser"
        }
        
        # Mock Request Status
        self.manager.get_request_status.return_value = {
            "current_requests": 10,
            "max_requests": 2500,
            "remaining_requests": 2490,
            "usage_percentage": 0.4,
            "max_users_to_process": 200
        }
        
        report = self.analyzer.generate_report()
        
        # Assertions
        assert report["user"] == "testuser"
        assert "timestamp" in report
        assert "request_status" in report
        assert "processing_limits" in report
        assert "stats" in report
        assert "one_way_follows" in report
        assert "not_following_back" in report
        assert "mutual_follows" in report
        
        # Stats prüfen
        stats = report["stats"]
        assert stats["total_followers"] == 2
        assert stats["total_following"] == 2
        assert stats["mutual_follows"] == 1
        assert stats["one_way_follows"] == 1
        assert stats["not_following_back"] == 1
    
    def test_analyze_follows_empty_sets(self):
        """Test Analyse mit leeren Sets"""
        self.manager.get_followers.return_value = set()
        self.manager.get_following.return_value = set()
        
        one_way, mutual, followers, not_following_back = self.analyzer.analyze_follows()
        
        assert len(one_way) == 0
        assert len(mutual) == 0
        assert len(followers) == 0
        assert len(not_following_back) == 0
    
    def test_analyze_follows_all_mutual(self):
        """Test Analyse wo alle Follows gegenseitig sind"""
        users = {"user1", "user2", "user3"}
        self.manager.get_followers.return_value = users
        self.manager.get_following.return_value = users
        
        one_way, mutual, followers, not_following_back = self.analyzer.analyze_follows()
        
        assert len(one_way) == 0
        assert mutual == users
        assert len(not_following_back) == 0


class TestFlaskApp:
    """Tests für die Flask-Anwendung"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_route(self):
        """Test der Hauptseite"""
        response = self.app.get('/')
        assert response.status_code == 200
        assert b'Follow-Fellow Dashboard' in response.data
        assert b'<!DOCTYPE html>' in response.data
    
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token', 'GITHUB_USERNAME': 'testuser'})
    @patch('follow_fellow.GitHubFollowManager')
    def test_api_status_success(self, mock_manager_class):
        """Test API-Status Endpoint"""
        # Mock Manager
        mock_manager = Mock()
        mock_manager.get_request_status.return_value = {
            "current_requests": 10,
            "max_requests": 2500,
            "remaining_requests": 2490,
            "usage_percentage": 0.4
        }
        mock_manager_class.return_value = mock_manager
        
        response = self.app.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'message' in data
    
    def test_api_status_no_token(self):
        """Test API-Status ohne Token"""
        with patch.dict(os.environ, {}, clear=True):
            response = self.app.get('/api/status')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert 'GitHub Token nicht gefunden' in data['error']
    
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token', 'GITHUB_USERNAME': 'testuser'})
    @patch('follow_fellow.FollowAnalyzer')
    @patch('follow_fellow.GitHubFollowManager')
    def test_api_analyze_success(self, mock_manager_class, mock_analyzer_class):
        """Test API-Analyse Endpoint"""
        # Mock Manager
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        # Mock Analyzer
        mock_analyzer = Mock()
        mock_analyzer.generate_report.return_value = {
            "user": "testuser",
            "stats": {"total_followers": 100, "total_following": 120}
        }
        mock_analyzer_class.return_value = mock_analyzer
        
        response = self.app.get('/api/analyze')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user'] == 'testuser'
        assert 'stats' in data
    
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token', 'GITHUB_USERNAME': 'testuser'})
    @patch('follow_fellow.FollowAnalyzer')
    @patch('follow_fellow.GitHubFollowManager')
    def test_api_cleanup_dry_run(self, mock_manager_class, mock_analyzer_class):
        """Test API-Cleanup im Dry-Run Modus"""
        # Mock Manager
        mock_manager = Mock()
        mock_manager.last_rate_limit_remaining = 4000
        mock_manager_class.return_value = mock_manager
        
        # Mock Analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_follows.return_value = (
            {"user1", "user2"},  # one_way_follows
            {"user3"},           # mutual_follows
            {"user3", "user4"},  # followers
            {"user4"}            # not_following_back
        )
        mock_analyzer_class.return_value = mock_analyzer
        
        response = self.app.post('/api/cleanup', 
                                json={'dry_run': True},
                                content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['dry_run'] is True
        assert data['processed'] == 2
        assert 'user1' in data['users']
        assert 'user2' in data['users']


class TestIntegration:
    """Integrationstests"""
    
    @patch('follow_fellow.requests.Session.request')
    def test_end_to_end_analysis(self, mock_request):
        """End-to-End Test der Analyse"""
        # Mock API Responses
        followers_response = Mock()
        followers_response.json.return_value = [{"login": "follower1"}, {"login": "follower2"}]
        followers_response.headers = {'Link': '', 'X-RateLimit-Remaining': '4999', 'X-RateLimit-Limit': '5000', 'X-RateLimit-Reset': str(int(time.time()) + 3600)}
        followers_response.raise_for_status.return_value = None
        
        following_response = Mock()
        following_response.json.return_value = [{"login": "follower1"}, {"login": "following1"}]
        following_response.headers = {'Link': '', 'X-RateLimit-Remaining': '4998', 'X-RateLimit-Limit': '5000', 'X-RateLimit-Reset': str(int(time.time()) + 3600)}
        following_response.raise_for_status.return_value = None
        
        mock_request.side_effect = [followers_response, following_response]
        
        # Test
        manager = GitHubFollowManager("testuser", "test_token")
        analyzer = FollowAnalyzer(manager)
        
        one_way, mutual, followers, not_following_back = analyzer.analyze_follows()
        
        # Assertions
        assert "following1" in one_way  # Folgt ihm, aber er folgt nicht zurück
        assert "follower1" in mutual    # Gegenseitig
        assert "follower2" in not_following_back  # Folgt mir, ich folge nicht zurück
        assert len(followers) == 2
        assert len(one_way) == 1
        assert len(mutual) == 1
        assert len(not_following_back) == 1


# Pytest Fixtures
@pytest.fixture
def mock_response():
    """Fixture für Mock Response"""
    response = Mock()
    response.status_code = 200
    response.headers = {
        'X-RateLimit-Remaining': '4999',
        'X-RateLimit-Limit': '5000',
        'X-RateLimit-Reset': str(int(time.time()) + 3600),
        'Link': ''
    }
    response.json.return_value = []
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def sample_followers():
    """Fixture für Beispiel-Follower"""
    return [
        {"login": "follower1", "id": 1},
        {"login": "follower2", "id": 2},
        {"login": "follower3", "id": 3}
    ]


@pytest.fixture
def sample_following():
    """Fixture für Beispiel-Following"""
    return [
        {"login": "follower1", "id": 1},
        {"login": "following1", "id": 4},
        {"login": "following2", "id": 5}
    ]


# Parametrisierte Tests
@pytest.mark.parametrize("followers,following,expected_one_way,expected_mutual,expected_not_following_back", [
    (
        {"user1", "user2", "user3"},
        {"user2", "user3", "user4"},
        {"user4"},
        {"user2", "user3"},
        {"user1"}
    ),
    (
        set(),
        {"user1", "user2"},
        {"user1", "user2"},
        set(),
        set()
    ),
    (
        {"user1", "user2"},
        set(),
        set(),
        set(),
        {"user1", "user2"}
    ),
    (
        {"user1", "user2"},
        {"user1", "user2"},
        set(),
        {"user1", "user2"},
        set()
    )
])
def test_follow_analysis_scenarios(followers, following, expected_one_way, expected_mutual, expected_not_following_back):
    """Parametrisierte Tests für verschiedene Follow-Szenarien"""
    manager = Mock(spec=GitHubFollowManager)
    manager.get_followers.return_value = followers
    manager.get_following.return_value = following
    
    analyzer = FollowAnalyzer(manager)
    one_way, mutual, _, not_following_back = analyzer.analyze_follows()
    
    assert one_way == expected_one_way
    assert mutual == expected_mutual
    assert not_following_back == expected_not_following_back


if __name__ == "__main__":
    pytest.main([__file__])

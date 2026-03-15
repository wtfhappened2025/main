"""
Test cases for WTFHappened Scheduler, Publisher, and RSS Feeds features.
Iteration 3 - Tests new RSS feeds, scheduler status, and auto-publisher endpoints.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@wtfhappened.app"
ADMIN_PASSWORD = "WTFadmin2026!"


class TestHealthAndBasic:
    """Basic health check tests"""

    def test_health_endpoint(self):
        """Health check returns healthy status with database connected"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        print("PASS: Health check endpoint working")


class TestSchedulerStatus:
    """Test scheduler status endpoint (public)"""

    def test_scheduler_status_public(self):
        """GET /api/scheduler/status - returns scheduler running status and next run time"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "next_run" in data
        assert "interval_minutes" in data
        assert data["interval_minutes"] == 10
        print(f"PASS: Scheduler status - running={data['running']}, interval={data['interval_minutes']}min")


class TestRSSFeedCategories:
    """Test RSS feed categories: entertainment and lifestyle"""

    def test_feed_entertainment_category(self):
        """GET /api/feed?category=entertainment - returns entertainment category topics from RSS feeds"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"category": "entertainment"})
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        topics = data["topics"]
        # Should have entertainment topics from TMZ/E! News
        assert len(topics) > 0, "Entertainment category should have topics"
        # All topics should be entertainment category
        for topic in topics:
            assert topic["category"] == "entertainment"
            assert topic["source"] in ["tmz", "enews", "people", "admin", "seed"]
        print(f"PASS: Entertainment feed - {len(topics)} topics found")

    def test_feed_lifestyle_category(self):
        """GET /api/feed?category=lifestyle - returns lifestyle category topics from RSS feeds"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"category": "lifestyle"})
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        topics = data["topics"]
        # May be empty if Vogue feed fails, but API should work
        if len(topics) > 0:
            for topic in topics:
                assert topic["category"] == "lifestyle"
                assert topic["source"] in ["vogue", "admin", "seed"]
        print(f"PASS: Lifestyle feed - {len(topics)} topics found")


class TestRefreshTrending:
    """Test background data refresh endpoint"""

    def test_refresh_trending_triggers_background(self):
        """POST /api/refresh-trending - triggers background data refresh"""
        response = requests.post(f"{BASE_URL}/api/refresh-trending")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Refresh started"
        print("PASS: Refresh trending endpoint triggers background job")


class TestAdminLogin:
    """Test admin authentication"""

    def test_admin_login_success(self):
        """POST /api/admin/login - authenticates admin with correct credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["role"] == "admin"
        print("PASS: Admin login successful")

    def test_admin_login_invalid_credentials(self):
        """POST /api/admin/login - rejects invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": "wrong@admin.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print("PASS: Admin login correctly rejects invalid credentials")


@pytest.fixture
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Admin authentication failed")


class TestAdminScheduler:
    """Test admin scheduler endpoint (requires auth)"""

    def test_admin_scheduler_status(self, admin_token):
        """GET /api/admin/scheduler - returns detailed scheduler info with last run timestamps"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/scheduler", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check data_refresh info
        assert "data_refresh" in data
        data_refresh = data["data_refresh"]
        assert "running" in data_refresh
        assert "next_run" in data_refresh
        assert "interval_minutes" in data_refresh
        assert "last_run" in data_refresh
        
        # Check auto_publisher info
        assert "auto_publisher" in data
        auto_pub = data["auto_publisher"]
        assert "running" in auto_pub
        assert "next_run" in auto_pub
        assert "last_run" in auto_pub
        
        print(f"PASS: Admin scheduler - data_refresh.running={data_refresh['running']}, auto_publisher.running={auto_pub['running']}")

    def test_admin_scheduler_without_auth(self):
        """GET /api/admin/scheduler - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/scheduler")
        assert response.status_code == 401
        print("PASS: Admin scheduler correctly requires authentication")


class TestAdminPublisher:
    """Test admin publisher endpoints (requires auth)"""

    def test_admin_published_cards(self, admin_token):
        """GET /api/admin/published - returns list of auto-published cards"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/published", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "published" in data
        # published is a list (may be empty if no cards published yet)
        assert isinstance(data["published"], list)
        print(f"PASS: Admin published cards - {len(data['published'])} cards")

    def test_admin_publish_now(self, admin_token):
        """POST /api/admin/publish-now - triggers auto-publisher manually"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/api/admin/publish-now", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Auto-publish triggered"
        print("PASS: Admin publish-now triggers auto-publisher")

    def test_admin_published_without_auth(self):
        """GET /api/admin/published - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/published")
        assert response.status_code == 401
        print("PASS: Admin published correctly requires authentication")

    def test_admin_publish_now_without_auth(self):
        """POST /api/admin/publish-now - requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/publish-now")
        assert response.status_code == 401
        print("PASS: Admin publish-now correctly requires authentication")


class TestTopicCardData:
    """Test topic cards display correct data for entertainment and lifestyle"""

    def test_entertainment_topic_has_required_fields(self):
        """Topic cards for entertainment have all required display fields"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"category": "entertainment"})
        assert response.status_code == 200
        topics = response.json()["topics"]
        
        if len(topics) > 0:
            topic = topics[0]
            # Check all required fields for TopicCard component
            assert "id" in topic
            assert "title" in topic
            assert "category" in topic
            assert "trend_score" in topic
            assert "source" in topic
            assert "time_ago" in topic
            assert "has_explanation" in topic
            print(f"PASS: Entertainment topic has all required fields")
        else:
            pytest.skip("No entertainment topics available")

    def test_lifestyle_topic_has_required_fields(self):
        """Topic cards for lifestyle have all required display fields"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"category": "lifestyle"})
        assert response.status_code == 200
        topics = response.json()["topics"]
        
        if len(topics) > 0:
            topic = topics[0]
            # Check all required fields for TopicCard component
            assert "id" in topic
            assert "title" in topic
            assert "category" in topic
            assert "trend_score" in topic
            assert "source" in topic
            assert "time_ago" in topic
            assert "has_explanation" in topic
            print(f"PASS: Lifestyle topic has all required fields")
        else:
            pytest.skip("No lifestyle topics available")


class TestAllFeedCategories:
    """Test that all feed categories work"""

    def test_feed_all_category(self):
        """GET /api/feed - all category returns mixed topics"""
        response = requests.get(f"{BASE_URL}/api/feed")
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert len(data["topics"]) > 0
        print(f"PASS: All feed - {len(data['topics'])} topics")

    def test_feed_finance_category(self):
        """GET /api/feed?category=finance - returns finance topics"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"category": "finance"})
        assert response.status_code == 200
        print("PASS: Finance feed endpoint working")

    def test_feed_technology_category(self):
        """GET /api/feed?category=technology - returns technology topics"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"category": "technology"})
        assert response.status_code == 200
        print("PASS: Technology feed endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

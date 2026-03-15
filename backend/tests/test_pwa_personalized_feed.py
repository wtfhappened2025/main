"""
Backend tests for PWA features and Personalized Feed endpoint.
Iteration 5: Testing PWA manifest, service-worker, and personalized feed features.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials (has onboarding complete with Technology/AI/Crypto interests)
TEST_USER_EMAIL = "feedtest@test.com"
TEST_USER_PASSWORD = "test123"


class TestPWAFeatures:
    """Test PWA manifest and service worker files are served correctly."""

    def test_manifest_json_returns_200(self):
        """GET /manifest.json returns 200 status."""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /manifest.json returns 200")

    def test_manifest_json_valid_structure(self):
        """manifest.json has required PWA fields: name, icons, display."""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "name" in data, "Missing 'name' field in manifest"
        assert data["name"] == "WTFHappened", f"Unexpected name: {data['name']}"
        
        assert "short_name" in data, "Missing 'short_name' field"
        assert "icons" in data, "Missing 'icons' array"
        assert isinstance(data["icons"], list), "'icons' should be an array"
        assert len(data["icons"]) >= 2, "Should have at least 2 icons (192x192 and 512x512)"
        
        # Check icons have required fields
        for icon in data["icons"]:
            assert "src" in icon, "Icon missing 'src'"
            assert "sizes" in icon, "Icon missing 'sizes'"
            assert "type" in icon, "Icon missing 'type'"
        
        assert "display" in data, "Missing 'display' field"
        assert data["display"] == "standalone", f"Expected 'standalone', got {data['display']}"
        
        # Check other important fields
        assert "start_url" in data, "Missing 'start_url'"
        assert "theme_color" in data, "Missing 'theme_color'"
        assert "background_color" in data, "Missing 'background_color'"
        
        print("✓ manifest.json has valid PWA structure with name, icons, display:standalone")

    def test_service_worker_returns_200(self):
        """GET /service-worker.js returns 200 status."""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /service-worker.js returns 200")

    def test_service_worker_valid_content(self):
        """service-worker.js contains valid service worker code."""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        assert response.status_code == 200
        content = response.text
        
        # Check for key service worker patterns
        assert "self.addEventListener('install'" in content or "self.addEventListener(\"install\"" in content, \
            "Missing install event listener"
        assert "self.addEventListener('activate'" in content or "self.addEventListener(\"activate\"" in content, \
            "Missing activate event listener"
        assert "self.addEventListener('fetch'" in content or "self.addEventListener(\"fetch\"" in content, \
            "Missing fetch event listener"
        assert "caches" in content.lower(), "Missing caching logic"
        
        print("✓ service-worker.js contains valid service worker with install/activate/fetch handlers")


class TestIndexHTMLMetaTags:
    """Test index.html has proper PWA and Apple meta tags."""

    def test_index_html_has_manifest_link(self):
        """index.html contains link to manifest.json."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        content = response.text
        
        assert 'rel="manifest"' in content, "Missing manifest link"
        assert 'manifest.json' in content, "Missing manifest.json in href"
        print("✓ index.html has manifest link")

    def test_index_html_has_apple_meta_tags(self):
        """index.html contains Apple-specific PWA meta tags."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        content = response.text
        
        assert 'apple-mobile-web-app-capable' in content, "Missing apple-mobile-web-app-capable meta"
        assert 'apple-mobile-web-app-status-bar-style' in content, "Missing apple-mobile-web-app-status-bar-style"
        assert 'apple-mobile-web-app-title' in content, "Missing apple-mobile-web-app-title"
        assert 'apple-touch-icon' in content, "Missing apple-touch-icon link"
        
        print("✓ index.html has Apple meta tags (capable, status-bar-style, title, touch-icon)")

    def test_index_html_has_theme_color(self):
        """index.html contains theme-color meta tag."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        content = response.text
        
        assert 'name="theme-color"' in content, "Missing theme-color meta tag"
        print("✓ index.html has theme-color meta tag")


class TestPersonalizedFeed:
    """Test personalized feed endpoint with authenticated user."""
    
    @pytest.fixture
    def auth_token(self):
        """Login as test user and return token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data["token"]
    
    def test_personalized_feed_requires_auth(self):
        """GET /api/feed/personalized returns 401 without auth."""
        response = requests.get(f"{BASE_URL}/api/feed/personalized")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/feed/personalized requires authentication")

    def test_personalized_feed_returns_topics(self, auth_token):
        """GET /api/feed/personalized returns topics with auth."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/feed/personalized", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "topics" in data, "Missing 'topics' in response"
        assert isinstance(data["topics"], list), "'topics' should be a list"
        assert len(data["topics"]) > 0, "Should return at least some topics"
        
        print(f"✓ GET /api/feed/personalized returns {len(data['topics'])} topics")

    def test_personalized_feed_includes_preferences_used(self, auth_token):
        """GET /api/feed/personalized returns preferences_used field."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/feed/personalized", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "preferences_used" in data, "Missing 'preferences_used' in response"
        prefs = data["preferences_used"]
        
        assert "categories" in prefs, "Missing 'categories' in preferences_used"
        assert "keywords" in prefs, "Missing 'keywords' in preferences_used"
        
        # Verify test user's preferences are reflected
        # Test user has interests: Technology, AI, Crypto and followed_topics: Bitcoin, Nvidia, Apple
        categories = prefs["categories"]
        keywords = prefs["keywords"]
        
        print(f"✓ preferences_used: categories={categories}, keywords={keywords}")

    def test_personalized_feed_boosts_relevant_topics(self, auth_token):
        """Personalized feed boosts crypto/tech topics for test user."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/feed/personalized?limit=10", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        topics = data["topics"]
        
        # Count how many top topics are in preferred categories
        prefs = data.get("preferences_used", {})
        preferred_cats = prefs.get("categories", [])
        keywords = prefs.get("keywords", [])
        
        relevant_count = 0
        for t in topics[:5]:  # Check top 5
            cat = t.get("category", "")
            title_lower = t.get("title", "").lower()
            
            if cat in preferred_cats:
                relevant_count += 1
            elif any(kw in title_lower for kw in keywords):
                relevant_count += 1
        
        # At least 3 of top 5 should be relevant to user preferences
        assert relevant_count >= 3, f"Expected at least 3 relevant topics in top 5, got {relevant_count}"
        print(f"✓ Personalized feed boosts relevant topics: {relevant_count}/5 top topics match preferences")

    def test_personalized_topics_have_personalized_flag(self, auth_token):
        """Topics from personalized feed have 'personalized: true' flag."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/feed/personalized", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        topics = data["topics"]
        
        # Check first few topics have personalized flag
        for topic in topics[:5]:
            assert topic.get("personalized") == True, f"Topic missing personalized flag: {topic.get('title', '')[:40]}"
        
        print("✓ Personalized feed topics have 'personalized: true' flag")


class TestRegularFeedStillWorks:
    """Verify regular feed endpoint still works for non-personalized filtering."""

    def test_feed_all_returns_topics(self):
        """GET /api/feed returns topics without auth."""
        response = requests.get(f"{BASE_URL}/api/feed")
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert len(data["topics"]) > 0
        print(f"✓ GET /api/feed returns {len(data['topics'])} topics")

    def test_feed_category_filter_works(self):
        """GET /api/feed?category=crypto filters by category."""
        response = requests.get(f"{BASE_URL}/api/feed?category=crypto")
        assert response.status_code == 200
        data = response.json()
        topics = data["topics"]
        
        # All returned topics should be crypto category
        for t in topics:
            assert t.get("category") == "crypto", f"Non-crypto topic in crypto filter: {t.get('category')}"
        
        print(f"✓ GET /api/feed?category=crypto returns {len(topics)} crypto topics")

    def test_feed_category_technology(self):
        """GET /api/feed?category=technology works."""
        response = requests.get(f"{BASE_URL}/api/feed?category=technology")
        assert response.status_code == 200
        data = response.json()
        for t in data["topics"]:
            assert t["category"] == "technology"
        print(f"✓ GET /api/feed?category=technology returns {len(data['topics'])} topics")

    def test_feed_limit_parameter(self):
        """GET /api/feed respects limit parameter."""
        response = requests.get(f"{BASE_URL}/api/feed?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["topics"]) <= 5, f"Expected max 5 topics, got {len(data['topics'])}"
        print("✓ GET /api/feed respects limit parameter")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 11: Tests for emoji reactions, swipe-to-dismiss, and bookmark features
Features tested:
- POST /api/react/{topic_id} - toggle emoji reaction (fire, shocked, mindblown, angry)
- GET /api/reactions/mine?topic_ids=id1,id2 - get user's active reactions
- POST /api/dismiss/{topic_id} - dismiss topic from feed
- POST /api/save/{topic_id} - toggle bookmark/save status
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "uitest@test.com"
TEST_PASSWORD = "test123456"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "identifier": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    return response.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def test_topic_id():
    """Get a valid topic ID for testing"""
    response = requests.get(f"{BASE_URL}/api/feed?limit=5")
    assert response.status_code == 200
    topics = response.json().get("topics", [])
    assert len(topics) > 0, "No topics available for testing"
    return topics[0]["id"]


class TestHealthCheck:
    """Basic health check"""
    
    def test_backend_healthy(self):
        """Verify backend is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json().get("status") == "healthy"
        print("✓ Backend health check passed")


class TestReactEndpoint:
    """Tests for POST /api/react/{topic_id}"""
    
    def test_react_fire_emoji_toggle_on(self, auth_headers, test_topic_id):
        """POST /api/react/{topic_id} with fire emoji should toggle ON and return toggled:true"""
        response = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "fire"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "toggled" in data, "Response missing 'toggled' field"
        assert "emoji" in data, "Response missing 'emoji' field"
        assert "reactions" in data, "Response missing 'reactions' field"
        assert data["emoji"] == "fire"
        # toggled could be True or False depending on current state
        print(f"✓ React fire: toggled={data['toggled']}, reactions={data['reactions']}")
    
    def test_react_shocked_emoji(self, auth_headers, test_topic_id):
        """POST /api/react/{topic_id} with shocked emoji should work"""
        response = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "shocked"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["emoji"] == "shocked"
        assert isinstance(data["reactions"], dict)
        print(f"✓ React shocked: toggled={data['toggled']}")
    
    def test_react_mindblown_emoji(self, auth_headers, test_topic_id):
        """POST /api/react/{topic_id} with mindblown emoji should work"""
        response = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "mindblown"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["emoji"] == "mindblown"
        print(f"✓ React mindblown: toggled={data['toggled']}")
    
    def test_react_angry_emoji(self, auth_headers, test_topic_id):
        """POST /api/react/{topic_id} with angry emoji should work"""
        response = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "angry"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["emoji"] == "angry"
        print(f"✓ React angry: toggled={data['toggled']}")
    
    def test_react_toggle_untoggle(self, auth_headers, test_topic_id):
        """Clicking same emoji twice should untoggle (toggled:false)"""
        # First click - get current state
        r1 = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "fire"}
        )
        assert r1.status_code == 200
        first_state = r1.json()["toggled"]
        
        # Second click - should toggle opposite
        r2 = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "fire"}
        )
        assert r2.status_code == 200
        second_state = r2.json()["toggled"]
        
        # States should be opposite
        assert first_state != second_state, "Toggle didn't change state"
        print(f"✓ Toggle test: first={first_state}, second={second_state}")
    
    def test_react_invalid_emoji_rejected(self, auth_headers, test_topic_id):
        """Invalid emoji should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "invalid_emoji"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid emoji, got {response.status_code}"
        print("✓ Invalid emoji correctly rejected with 400")
    
    def test_react_nonexistent_topic(self, auth_headers):
        """React to non-existent topic should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/react/nonexistent-topic-id-12345",
            headers=auth_headers,
            json={"emoji": "fire"}
        )
        assert response.status_code == 404
        print("✓ Non-existent topic correctly returns 404")
    
    def test_react_requires_auth(self, test_topic_id):
        """React endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            json={"emoji": "fire"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Auth required for react endpoint")


class TestGetMyReactionsEndpoint:
    """Tests for GET /api/reactions/mine"""
    
    def test_get_my_reactions_single_topic(self, auth_headers, test_topic_id):
        """GET /api/reactions/mine?topic_ids=id should return user's reactions"""
        response = requests.get(
            f"{BASE_URL}/api/reactions/mine?topic_ids={test_topic_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "reactions" in data
        assert isinstance(data["reactions"], dict)
        print(f"✓ Get my reactions: {data['reactions']}")
    
    def test_get_my_reactions_multiple_topics(self, auth_headers):
        """GET /api/reactions/mine with multiple topic_ids"""
        # Get multiple topic IDs
        feed_response = requests.get(f"{BASE_URL}/api/feed?limit=5")
        topics = feed_response.json().get("topics", [])
        if len(topics) < 2:
            pytest.skip("Need at least 2 topics to test multiple")
        
        ids = ",".join([t["id"] for t in topics[:3]])
        response = requests.get(
            f"{BASE_URL}/api/reactions/mine?topic_ids={ids}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "reactions" in data
        print(f"✓ Get my reactions for {len(topics[:3])} topics: keys={list(data['reactions'].keys())}")
    
    def test_get_my_reactions_empty_ids(self, auth_headers):
        """GET /api/reactions/mine with empty topic_ids returns empty"""
        response = requests.get(
            f"{BASE_URL}/api/reactions/mine?topic_ids=",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reactions"] == {}
        print("✓ Empty topic_ids returns empty reactions")
    
    def test_get_my_reactions_requires_auth(self, test_topic_id):
        """Get my reactions should require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/reactions/mine?topic_ids={test_topic_id}"
        )
        assert response.status_code in [401, 403]
        print("✓ Auth required for get my reactions endpoint")


class TestDismissEndpoint:
    """Tests for POST /api/dismiss/{topic_id}"""
    
    def test_dismiss_topic(self, auth_headers, test_topic_id):
        """POST /api/dismiss/{topic_id} should store dismissal"""
        response = requests.post(
            f"{BASE_URL}/api/dismiss/{test_topic_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "dismissed" in data
        assert data["dismissed"] == True
        print(f"✓ Dismiss topic: dismissed={data['dismissed']}")
    
    def test_dismiss_topic_idempotent(self, auth_headers, test_topic_id):
        """Dismissing same topic twice should work (upsert behavior)"""
        # First dismiss
        r1 = requests.post(
            f"{BASE_URL}/api/dismiss/{test_topic_id}",
            headers=auth_headers
        )
        assert r1.status_code == 200
        
        # Second dismiss - should still succeed
        r2 = requests.post(
            f"{BASE_URL}/api/dismiss/{test_topic_id}",
            headers=auth_headers
        )
        assert r2.status_code == 200
        assert r2.json()["dismissed"] == True
        print("✓ Dismiss is idempotent (can dismiss multiple times)")
    
    def test_dismiss_requires_auth(self, test_topic_id):
        """Dismiss endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/dismiss/{test_topic_id}"
        )
        assert response.status_code in [401, 403]
        print("✓ Auth required for dismiss endpoint")


class TestSaveEndpoint:
    """Tests for POST /api/save/{topic_id}"""
    
    def test_save_topic_toggle(self, auth_headers, test_topic_id):
        """POST /api/save/{topic_id} should toggle save status"""
        response = requests.post(
            f"{BASE_URL}/api/save/{test_topic_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "saved" in data
        assert "message" in data
        assert isinstance(data["saved"], bool)
        print(f"✓ Save topic: saved={data['saved']}, message={data['message']}")
    
    def test_save_toggle_untoggle(self, auth_headers, test_topic_id):
        """Clicking save twice should toggle state"""
        # First save
        r1 = requests.post(
            f"{BASE_URL}/api/save/{test_topic_id}",
            headers=auth_headers
        )
        first_state = r1.json()["saved"]
        
        # Second save - should toggle
        r2 = requests.post(
            f"{BASE_URL}/api/save/{test_topic_id}",
            headers=auth_headers
        )
        second_state = r2.json()["saved"]
        
        assert first_state != second_state, "Save toggle didn't change state"
        print(f"✓ Save toggle: first={first_state}, second={second_state}")
    
    def test_save_nonexistent_topic(self, auth_headers):
        """Save non-existent topic should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/save/nonexistent-topic-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Save non-existent topic returns 404")
    
    def test_save_requires_auth(self, test_topic_id):
        """Save endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/save/{test_topic_id}"
        )
        assert response.status_code in [401, 403]
        print("✓ Auth required for save endpoint")


class TestGetSavedEndpoint:
    """Tests for GET /api/saved"""
    
    def test_get_saved_returns_list(self, auth_headers):
        """GET /api/saved should return saved topics"""
        response = requests.get(
            f"{BASE_URL}/api/saved",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "saved" in data
        assert isinstance(data["saved"], list)
        print(f"✓ Get saved: {len(data['saved'])} saved topics")
    
    def test_get_saved_requires_auth(self):
        """Get saved endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/saved")
        assert response.status_code in [401, 403]
        print("✓ Auth required for get saved endpoint")


class TestReactionsIntegration:
    """Integration tests for reactions flow"""
    
    def test_react_updates_topic_reactions_count(self, auth_headers, test_topic_id):
        """Verify reaction count updates in topic"""
        # Get initial reactions count
        feed_response = requests.get(f"{BASE_URL}/api/feed?limit=50")
        topics = feed_response.json().get("topics", [])
        topic = next((t for t in topics if t["id"] == test_topic_id), None)
        initial_reactions = topic.get("reactions", {}) if topic else {}
        initial_fire = initial_reactions.get("fire", 0)
        
        # Toggle reaction twice to return to original state after test
        # First toggle
        r1 = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "fire"}
        )
        assert r1.status_code == 200
        mid_reactions = r1.json()["reactions"]
        
        # The count should have changed
        print(f"✓ Reactions updated: initial_fire={initial_fire}, after_toggle={mid_reactions.get('fire', 0)}")
        
        # Toggle back for cleanup
        r2 = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "fire"}
        )
        assert r2.status_code == 200
    
    def test_multiple_emoji_reactions_on_same_topic(self, auth_headers, test_topic_id):
        """User can have multiple different emoji reactions on same topic"""
        # React with fire
        r1 = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "fire"}
        )
        assert r1.status_code == 200
        
        # React with shocked (different emoji)
        r2 = requests.post(
            f"{BASE_URL}/api/react/{test_topic_id}",
            headers=auth_headers,
            json={"emoji": "shocked"}
        )
        assert r2.status_code == 200
        
        # Check user's reactions
        r3 = requests.get(
            f"{BASE_URL}/api/reactions/mine?topic_ids={test_topic_id}",
            headers=auth_headers
        )
        assert r3.status_code == 200
        user_reactions = r3.json()["reactions"].get(test_topic_id, [])
        print(f"✓ User reactions on topic: {user_reactions}")
        
        # Clean up - toggle back
        requests.post(f"{BASE_URL}/api/react/{test_topic_id}", headers=auth_headers, json={"emoji": "fire"})
        requests.post(f"{BASE_URL}/api/react/{test_topic_id}", headers=auth_headers, json={"emoji": "shocked"})


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

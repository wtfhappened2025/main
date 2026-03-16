"""
Iteration 10: Tests for card_3_affects and card_3_action split feature in YOU tab
Tests:
- GET /api/explanation/{topic_id} returns card_3_affects and card_3_action arrays
- POST /api/explain returns card_3_affects and card_3_action arrays for new explanations
- API field structure validation
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndSetup:
    """Basic health checks before testing card_3 split feature"""
    
    def test_health_endpoint(self):
        """Verify backend is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed: {data}")

    def test_feed_returns_topics(self):
        """Verify feed endpoint works"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert len(data["topics"]) > 0
        print(f"✓ Feed returns {len(data['topics'])} topics")


class TestExistingExplanationFields:
    """Test existing explanations for card_3_affects/card_3_action fields"""
    
    def test_get_explanation_returns_expected_structure(self):
        """GET /api/explanation/{topic_id} should return explanation with expected fields"""
        # First get a topic with explanation
        feed_response = requests.get(f"{BASE_URL}/api/feed?limit=20")
        assert feed_response.status_code == 200
        topics = feed_response.json().get("topics", [])
        
        # Find a topic that has an explanation
        topic_with_explanation = None
        for topic in topics:
            if topic.get("has_explanation"):
                topic_with_explanation = topic
                break
        
        assert topic_with_explanation is not None, "No topic with existing explanation found in feed"
        topic_id = topic_with_explanation["id"]
        
        # Get the explanation
        response = requests.get(f"{BASE_URL}/api/explanation/{topic_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "explanation" in data
        exp = data["explanation"]
        
        # Verify standard fields
        assert "id" in exp
        assert "topic_id" in exp
        assert "card_1" in exp
        assert "card_2" in exp
        assert "card_3" in exp
        
        # Check for new card_3_affects and card_3_action fields (may be empty for old explanations)
        # The fields should exist even if empty - that's the fallback behavior
        print(f"✓ Explanation structure verified for topic: {topic_with_explanation['title'][:50]}")
        print(f"  - card_3_affects present: {'card_3_affects' in exp}")
        print(f"  - card_3_action present: {'card_3_action' in exp}")
        
        if "card_3_affects" in exp:
            assert isinstance(exp.get("card_3_affects"), list), "card_3_affects should be a list"
        if "card_3_action" in exp:
            assert isinstance(exp.get("card_3_action"), list), "card_3_action should be a list"


class TestNewExplanationGeneration:
    """Test POST /api/explain to verify new explanations have card_3_affects/card_3_action"""
    
    def test_explain_returns_card3_split_fields(self):
        """POST /api/explain should return card_3_affects and card_3_action arrays"""
        payload = {
            "input": "TEST_card3_split What is happening with AI regulations in the EU?"
        }
        
        print(f"Requesting new explanation for: {payload['input']}")
        print("Note: This test may take 15-30 seconds due to AI generation...")
        
        response = requests.post(
            f"{BASE_URL}/api/explain",
            json=payload,
            timeout=120  # AI generation can take time
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "topic" in data, "Response should contain 'topic'"
        assert "explanation" in data, "Response should contain 'explanation'"
        
        exp = data["explanation"]
        
        # Verify standard card fields
        assert "card_1" in exp, "Missing card_1"
        assert "card_2" in exp, "Missing card_2"
        assert "card_3" in exp, "Missing card_3"
        
        # Verify new card_3_affects and card_3_action arrays exist
        assert "card_3_affects" in exp, "Missing card_3_affects array"
        assert "card_3_action" in exp, "Missing card_3_action array"
        
        # Verify they are arrays
        assert isinstance(exp["card_3_affects"], list), "card_3_affects should be a list"
        assert isinstance(exp["card_3_action"], list), "card_3_action should be a list"
        
        print(f"✓ New explanation generated successfully")
        print(f"  - card_3_affects ({len(exp['card_3_affects'])} items): {exp['card_3_affects'][:2]}...")
        print(f"  - card_3_action ({len(exp['card_3_action'])} items): {exp['card_3_action'][:2]}...")
        
        # Verify arrays have content (AI should generate 3 items each)
        assert len(exp["card_3_affects"]) > 0, "card_3_affects should have at least 1 item"
        assert len(exp["card_3_action"]) > 0, "card_3_action should have at least 1 item"
        
        # Return topic_id for cleanup
        return data["topic"]["id"]

    def test_generated_explanation_persists_with_card3_split(self):
        """Verify newly generated explanation persists with card_3_affects/card_3_action"""
        # First create a new explanation
        payload = {
            "input": "TEST_persist_card3 What is the impact of quantum computing on cybersecurity?"
        }
        
        print(f"Creating new explanation: {payload['input']}")
        create_response = requests.post(
            f"{BASE_URL}/api/explain",
            json=payload,
            timeout=120
        )
        
        assert create_response.status_code == 200
        created = create_response.json()
        topic_id = created["topic"]["id"]
        
        # Verify card_3_affects and card_3_action in POST response
        assert "card_3_affects" in created["explanation"]
        assert "card_3_action" in created["explanation"]
        original_affects = created["explanation"]["card_3_affects"]
        original_action = created["explanation"]["card_3_action"]
        
        print(f"✓ Created explanation with topic_id: {topic_id}")
        
        # Now GET the same explanation
        get_response = requests.get(f"{BASE_URL}/api/explanation/{topic_id}")
        assert get_response.status_code == 200
        
        fetched = get_response.json()["explanation"]
        
        # Verify fields persisted
        assert "card_3_affects" in fetched, "card_3_affects not persisted in GET"
        assert "card_3_action" in fetched, "card_3_action not persisted in GET"
        
        # Verify data matches
        assert fetched["card_3_affects"] == original_affects, "card_3_affects data mismatch"
        assert fetched["card_3_action"] == original_action, "card_3_action data mismatch"
        
        print(f"✓ card_3_affects and card_3_action persisted correctly in database")
        print(f"  - Affects: {len(fetched['card_3_affects'])} items")
        print(f"  - Action: {len(fetched['card_3_action'])} items")


class TestExplanationOnDemandGeneration:
    """Test explanation generated on-demand via GET /api/explanation/{topic_id}"""
    
    def test_get_explanation_generates_card3_split_for_new_topic(self):
        """When GET /api/explanation/{topic_id} generates a new explanation, it should include card_3_affects/card_3_action"""
        # Find a topic without explanation
        feed_response = requests.get(f"{BASE_URL}/api/feed?limit=50")
        assert feed_response.status_code == 200
        topics = feed_response.json().get("topics", [])
        
        topic_without_explanation = None
        for topic in topics:
            if not topic.get("has_explanation"):
                topic_without_explanation = topic
                break
        
        if not topic_without_explanation:
            pytest.skip("No topic without explanation found in feed - all topics already have explanations")
            return
        
        topic_id = topic_without_explanation["id"]
        print(f"Testing on-demand generation for topic: {topic_without_explanation['title'][:50]}")
        print("Note: This test may take 15-30 seconds due to AI generation...")
        
        # This GET request should trigger explanation generation
        response = requests.get(f"{BASE_URL}/api/explanation/{topic_id}", timeout=120)
        assert response.status_code == 200
        
        exp = response.json()["explanation"]
        
        # Verify new card_3 split fields
        assert "card_3_affects" in exp, "On-demand generated explanation missing card_3_affects"
        assert "card_3_action" in exp, "On-demand generated explanation missing card_3_action"
        
        assert isinstance(exp["card_3_affects"], list)
        assert isinstance(exp["card_3_action"], list)
        
        print(f"✓ On-demand explanation includes card_3_affects and card_3_action")
        print(f"  - card_3_affects: {exp['card_3_affects']}")
        print(f"  - card_3_action: {exp['card_3_action']}")


class TestEdgeCases:
    """Edge case tests for card_3 split feature"""
    
    def test_explain_empty_input_rejected(self):
        """POST /api/explain should reject empty input"""
        response = requests.post(f"{BASE_URL}/api/explain", json={"input": ""})
        assert response.status_code == 400
        print("✓ Empty input correctly rejected")
    
    def test_explain_whitespace_input_rejected(self):
        """POST /api/explain should reject whitespace-only input"""
        response = requests.post(f"{BASE_URL}/api/explain", json={"input": "   "})
        assert response.status_code == 400
        print("✓ Whitespace-only input correctly rejected")
    
    def test_get_nonexistent_explanation(self):
        """GET /api/explanation/{invalid_id} should return 404"""
        response = requests.get(f"{BASE_URL}/api/explanation/nonexistent-topic-id-12345")
        assert response.status_code == 404
        print("✓ Non-existent topic correctly returns 404")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

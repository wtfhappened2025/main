#!/usr/bin/env python3
"""
Backend API Testing for WTFHappened App
Tests all backend endpoints for functionality and integration.
"""

import requests
import sys
import json
import time
from datetime import datetime

class WTFHappenedAPITester:
    def __init__(self):
        self.base_url = "https://web-pulse-4.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_topic_id = None
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        self.log(f"🔍 Testing {name} - {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Response: {error_data}")
                except:
                    self.log(f"   Response: {response.text[:200]}...")
                return False, {}
                
        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_health_endpoint(self):
        """Test API health check"""
        success, response = self.run_test(
            "Health Check",
            "GET", 
            "health",
            200
        )
        if success:
            if response.get('status') == 'healthy':
                self.log("   Health status: HEALTHY")
                return True
            else:
                self.log(f"   Health status: {response.get('status', 'unknown')}")
        return success

    def test_feed_endpoint(self):
        """Test trending feed endpoint"""
        success, response = self.run_test(
            "Feed - Default",
            "GET",
            "feed",
            200
        )
        if success:
            topics = response.get('topics', [])
            self.log(f"   Retrieved {len(topics)} topics")
            
            if len(topics) >= 8:  # Should have 8 seed topics
                self.log("   ✓ Expected number of seed topics found")
                # Store first topic ID for later tests
                self.test_topic_id = topics[0].get('id')
                self.log(f"   Using topic ID for further tests: {self.test_topic_id}")
            else:
                self.log(f"   ⚠️ Expected at least 8 topics, got {len(topics)}")
            
            # Test topics are sorted by trend_score
            scores = [t.get('trend_score', 0) for t in topics]
            if scores == sorted(scores, reverse=True):
                self.log("   ✓ Topics correctly sorted by trend_score")
            else:
                self.log("   ⚠️ Topics not properly sorted by trend_score")
                
        return success

    def test_feed_with_category(self):
        """Test feed filtering by category"""
        categories = ['technology', 'finance', 'ai', 'crypto']
        passed = 0
        
        for category in categories:
            success, response = self.run_test(
                f"Feed - Category: {category}",
                "GET",
                "feed",
                200,
                params={'category': category}
            )
            if success:
                topics = response.get('topics', [])
                if all(t.get('category') == category for t in topics):
                    self.log(f"   ✓ All topics belong to {category} category")
                    passed += 1
                else:
                    self.log(f"   ⚠️ Some topics don't match {category} category")
        
        return passed == len(categories)

    def test_explanation_endpoint(self):
        """Test explanation retrieval"""
        if not self.test_topic_id:
            self.log("❌ No topic ID available for explanation test")
            return False
            
        success, response = self.run_test(
            "Get Explanation",
            "GET",
            f"explanation/{self.test_topic_id}",
            200
        )
        
        if success:
            explanation = response.get('explanation', {})
            required_fields = ['card_1', 'card_2', 'card_3', 'topic_title']
            
            missing_fields = [field for field in required_fields if not explanation.get(field)]
            if not missing_fields:
                self.log("   ✓ All required explanation fields present")
                self.log(f"   Topic: {explanation.get('topic_title')}")
                self.log(f"   Card 1: {explanation.get('card_1')[:50]}...")
            else:
                self.log(f"   ⚠️ Missing fields: {missing_fields}")
                
        return success

    def test_trending_endpoint(self):
        """Test trending topics endpoint"""
        success, response = self.run_test(
            "Trending Topics",
            "GET", 
            "trending",
            200
        )
        
        if success:
            trending = response.get('trending', [])
            self.log(f"   Retrieved {len(trending)} trending topics")
            
            if trending:
                # Check if topics have time_ago field
                if all('time_ago' in topic for topic in trending):
                    self.log("   ✓ All topics have time_ago field")
                else:
                    self.log("   ⚠️ Some topics missing time_ago field")
                    
        return success

    def test_save_functionality(self):
        """Test save/unsave topic functionality"""
        if not self.test_topic_id:
            self.log("❌ No topic ID available for save test")
            return False
            
        # Test saving
        success1, response1 = self.run_test(
            "Save Topic",
            "POST",
            f"save/{self.test_topic_id}",
            200
        )
        
        save_success = False
        if success1:
            if response1.get('saved') is True:
                self.log("   ✓ Topic saved successfully")
                save_success = True
            else:
                self.log(f"   ⚠️ Unexpected save response: {response1}")
        
        # Test unsaving (calling save again should toggle)
        success2, response2 = self.run_test(
            "Unsave Topic", 
            "POST",
            f"save/{self.test_topic_id}",
            200
        )
        
        unsave_success = False
        if success2:
            if response2.get('saved') is False:
                self.log("   ✓ Topic unsaved successfully")
                unsave_success = True
            else:
                self.log(f"   ⚠️ Unexpected unsave response: {response2}")
                
        return save_success and unsave_success

    def test_saved_endpoint(self):
        """Test retrieving saved topics"""
        success, response = self.run_test(
            "Get Saved Topics",
            "GET",
            "saved", 
            200
        )
        
        if success:
            saved = response.get('saved', [])
            self.log(f"   Retrieved {len(saved)} saved topics")
            
            # Check structure of saved topics
            if saved:
                first_saved = saved[0]
                if 'topic' in first_saved and 'saved_at' in first_saved:
                    self.log("   ✓ Saved topics have correct structure")
                else:
                    self.log("   ⚠️ Saved topics missing required fields")
                    
        return success

    def test_explain_functionality(self):
        """Test AI explanation generation"""
        test_input = "Why did Tesla stock drop today?"
        
        success, response = self.run_test(
            "AI Explain Generation",
            "POST",
            "explain",
            200,
            data={'input': test_input}
        )
        
        if success:
            if 'topic' in response and 'explanation' in response:
                topic = response['topic']
                explanation = response['explanation']
                
                self.log(f"   ✓ Generated explanation for: {topic.get('title')}")
                self.log(f"   Card 1: {explanation.get('card_1', '')[:50]}...")
                
                # Check if explanation has all required cards
                cards_present = all(explanation.get(f'card_{i}') for i in range(1, 4))
                if cards_present:
                    self.log("   ✓ All explanation cards generated")
                else:
                    self.log("   ⚠️ Some explanation cards missing")
                    
                return cards_present
            else:
                self.log("   ⚠️ Response missing topic or explanation")
                
        return success

    def test_render_card_endpoint(self):
        """Test social card rendering"""
        if not self.test_topic_id:
            self.log("❌ No topic ID available for render card test")
            return False
            
        success, response = self.run_test(
            "Render Social Card",
            "GET",
            f"render-card/{self.test_topic_id}",
            200,
            params={'template_type': 'standard'}
        )
        
        if success:
            card_data = response.get('card_data', {})
            required_fields = ['title', 'card_1', 'card_2', 'card_3', 'caption']
            
            missing_fields = [field for field in required_fields if not card_data.get(field)]
            if not missing_fields:
                self.log("   ✓ Social card has all required fields")
                self.log(f"   Caption: {card_data.get('caption')}")
            else:
                self.log(f"   ⚠️ Social card missing fields: {missing_fields}")
                
        return success

    def run_all_tests(self):
        """Run comprehensive API test suite"""
        self.log("🚀 Starting WTFHappened API Test Suite")
        self.log(f"Testing against: {self.base_url}")
        self.log("-" * 60)
        
        # Core API tests
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Feed Endpoint", self.test_feed_endpoint), 
            ("Category Filtering", self.test_feed_with_category),
            ("Explanation Retrieval", self.test_explanation_endpoint),
            ("Trending Endpoint", self.test_trending_endpoint),
            ("Save Functionality", self.test_save_functionality),
            ("Saved Topics", self.test_saved_endpoint),
            ("AI Explain", self.test_explain_functionality),
            ("Social Card Rendering", self.test_render_card_endpoint),
        ]
        
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                self.log(f"\n📋 {test_name}")
                result = test_func()
                if not result:
                    failed_tests.append(test_name)
            except Exception as e:
                self.log(f"❌ {test_name} - Exception: {str(e)}")
                failed_tests.append(test_name)
        
        # Results summary
        self.log("\n" + "=" * 60)
        self.log("📊 TEST RESULTS")
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if failed_tests:
            self.log(f"\n❌ Failed Tests: {', '.join(failed_tests)}")
            return False
        else:
            self.log("\n✅ All tests passed!")
            return True

def main():
    """Main test execution"""
    tester = WTFHappenedAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
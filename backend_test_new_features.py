#!/usr/bin/env python3
"""
Backend API Testing for WTFHappened App - New Features
Tests all new backend endpoints added for 5 major features.
"""

import requests
import sys
import json
import time
from datetime import datetime

class WTFHappenedNewFeaturesAPITester:
    def __init__(self):
        self.base_url = "https://web-pulse-4.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.admin_token = None
        self.test_user_id = None
        self.reset_token = None
        self.created_topic_id = None
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, auth_required=False, admin_auth=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}
        
        # Add auth header if required and available
        if admin_auth and self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'
        elif auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        self.tests_run += 1
        self.log(f"🔍 Testing {name} - {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
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

    def setup_user_auth(self):
        """Login with existing user for testing"""
        test_data = {
            "identifier": "test@example.com",
            "password": "password123"
        }
        
        success, response = self.run_test(
            "Setup - Login User",
            "POST", 
            "auth/login",
            200,
            data=test_data
        )
        
        if success:
            if 'token' in response:
                self.auth_token = response['token']
                self.test_user_id = response['user'].get('id')
                self.log(f"   ✓ User authenticated: {response['user'].get('email')}")
                return True
        return False

    # FEATURE 1: FORGOT/RESET PASSWORD FLOW
    def test_forgot_password(self):
        """Test forgot password endpoint"""
        success, response = self.run_test(
            "Forgot Password Request",
            "POST",
            "auth/forgot-password", 
            200,
            data={"identifier": "test@example.com"}
        )
        
        if success:
            if response.get('message'):
                self.log("   ✓ Forgot password message returned")
                # Store reset token if returned (for demo)
                if response.get('reset_token'):
                    self.reset_token = response['reset_token']
                    self.log(f"   ✓ Reset token received: {self.reset_token[:20]}...")
                return True
            else:
                self.log("   ⚠️ No message in response")
        return success

    def test_reset_password(self):
        """Test reset password endpoint"""
        if not self.reset_token:
            self.log("❌ No reset token available for password reset test")
            return False
            
        success, response = self.run_test(
            "Reset Password",
            "POST", 
            "auth/reset-password",
            200,
            data={"token": self.reset_token, "new_password": "newpassword123"}
        )
        
        if success:
            if response.get('message') == 'Password reset successfully':
                self.log("   ✓ Password reset successful")
                return True
            else:
                self.log(f"   ⚠️ Unexpected response: {response}")
        return success

    def test_reset_password_invalid_token(self):
        """Test reset password with invalid token"""
        success, response = self.run_test(
            "Reset Password Invalid Token",
            "POST",
            "auth/reset-password", 
            400,
            data={"token": "invalid_token_123", "new_password": "newpassword123"}
        )
        
        if success:
            self.log("   ✓ Invalid token correctly rejected with 400")
        return success

    # FEATURE 2: PROFILE/SETTINGS MANAGEMENT
    def test_update_profile(self):
        """Test profile update endpoint"""
        if not self.auth_token:
            self.log("❌ No auth token available")
            return False
            
        success, response = self.run_test(
            "Update Profile",
            "PUT",
            "auth/profile",
            200, 
            data={"name": "Updated Test User", "email": "test@example.com"},
            auth_required=True
        )
        
        if success:
            user = response.get('user', {})
            if user.get('name') == "Updated Test User":
                self.log("   ✓ Profile updated successfully")
                return True
            else:
                self.log("   ⚠️ Profile not updated as expected")
        return success

    def test_change_password(self):
        """Test change password endpoint"""
        if not self.auth_token:
            self.log("❌ No auth token available")
            return False
            
        success, response = self.run_test(
            "Change Password", 
            "PUT",
            "auth/change-password",
            200,
            data={"current_password": "password123", "new_password": "newpassword123"},
            auth_required=True
        )
        
        if success:
            if response.get('message') == 'Password changed successfully':
                self.log("   ✓ Password changed successfully")
                return True
            else:
                self.log(f"   ⚠️ Unexpected response: {response}")
        return success

    def test_auto_renew_toggle(self):
        """Test auto-renew toggle endpoint"""
        if not self.auth_token:
            self.log("❌ No auth token available")
            return False
            
        success, response = self.run_test(
            "Toggle Auto Renew",
            "PUT", 
            "auth/auto-renew",
            200,
            auth_required=True
        )
        
        if success:
            if 'auto_renew' in response:
                self.log(f"   ✓ Auto-renew toggled to: {response['auto_renew']}")
                return True
            else:
                self.log("   ⚠️ No auto_renew field in response")
        return success

    def test_suspend_account(self):
        """Test suspend account endpoint"""
        # Create new test user for suspension
        timestamp = int(time.time())
        register_data = {
            "name": "Suspend Test User",
            "email": f"suspend{timestamp}@example.com",
            "password": "testpass123"
        }
        
        reg_success, reg_response = self.run_test(
            "Setup - Register Suspend User",
            "POST",
            "auth/register", 
            200,
            data=register_data
        )
        
        if not reg_success:
            return False
            
        # Use new user token
        temp_token = reg_response.get('token')
        old_token = self.auth_token
        self.auth_token = temp_token
        
        success, response = self.run_test(
            "Suspend Account",
            "POST",
            "auth/suspend",
            200,
            auth_required=True
        )
        
        # Restore original token
        self.auth_token = old_token
        
        if success:
            if response.get('message') == 'Account suspended':
                self.log("   ✓ Account suspended successfully")
                return True
            else:
                self.log(f"   ⚠️ Unexpected response: {response}")
        return success

    # FEATURE 3: SUBSCRIPTION MANAGEMENT
    def test_subscription_info(self):
        """Test subscription info endpoint"""
        if not self.auth_token:
            self.log("❌ No auth token available")
            return False
            
        success, response = self.run_test(
            "Subscription Info",
            "GET",
            "subscription/info", 
            200,
            auth_required=True
        )
        
        if success:
            sub_data = response
            expected_fields = ['subscription_status', 'trial_end', 'auto_renew']
            missing_fields = [f for f in expected_fields if f not in sub_data]
            
            if not missing_fields:
                self.log(f"   ✓ Subscription status: {sub_data.get('subscription_status')}")
                self.log(f"   ✓ Auto-renew: {sub_data.get('auto_renew')}")
                return True
            else:
                self.log(f"   ⚠️ Missing fields: {missing_fields}")
        return success

    def test_subscription_checkout(self):
        """Test subscription checkout endpoint"""
        if not self.auth_token:
            self.log("❌ No auth token available")
            return False
            
        success, response = self.run_test(
            "Subscription Checkout",
            "POST",
            "subscription/checkout",
            200,
            data={"origin_url": self.base_url},
            auth_required=True
        )
        
        if success:
            if response.get('url') and response.get('session_id'):
                self.log("   ✓ Checkout session created")
                self.log(f"   Session ID: {response.get('session_id')[:20]}...")
                return True
            else:
                self.log("   ⚠️ Missing checkout URL or session ID")
        return success

    # FEATURE 4 & 5: ADMIN FUNCTIONALITY
    def setup_admin_auth(self):
        """Login as admin for testing"""
        success, response = self.run_test(
            "Setup - Admin Login",
            "POST", 
            "admin/login",
            200,
            data={"email": "admin@wtfhappened.app", "password": "WTFadmin2026!"}
        )
        
        if success:
            if 'token' in response:
                self.admin_token = response['token']
                self.log(f"   ✓ Admin authenticated")
                return True
        return False

    def test_admin_login_invalid(self):
        """Test admin login with invalid credentials"""
        success, response = self.run_test(
            "Admin Login Invalid",
            "POST",
            "admin/login",
            401,
            data={"email": "admin@wtfhappened.app", "password": "wrongpassword"}
        )
        
        if success:
            self.log("   ✓ Invalid admin credentials correctly rejected")
        return success

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        if not self.admin_token:
            self.log("❌ No admin token available")
            return False
            
        success, response = self.run_test(
            "Admin Stats",
            "GET",
            "admin/stats",
            200,
            admin_auth=True
        )
        
        if success:
            stats = response
            expected_fields = ['total_users', 'active_users', 'trial_users', 'paid_users', 'total_topics', 'total_explanations']
            missing_fields = [f for f in expected_fields if f not in stats]
            
            if not missing_fields:
                self.log(f"   ✓ Total users: {stats.get('total_users')}")
                self.log(f"   ✓ Active users: {stats.get('active_users')}")
                self.log(f"   ✓ Total topics: {stats.get('total_topics')}")
                return True
            else:
                self.log(f"   ⚠️ Missing stats fields: {missing_fields}")
        return success

    def test_admin_users(self):
        """Test admin users endpoint"""
        if not self.admin_token:
            self.log("❌ No admin token available")
            return False
            
        success, response = self.run_test(
            "Admin Get Users",
            "GET",
            "admin/users", 
            200,
            admin_auth=True
        )
        
        if success:
            users = response.get('users', [])
            self.log(f"   ✓ Retrieved {len(users)} users")
            
            if users:
                # Test user status update
                user_id = users[0].get('id')
                if user_id:
                    return self.test_admin_update_user_status(user_id)
                    
        return success

    def test_admin_update_user_status(self, user_id):
        """Test admin update user status endpoint"""
        success, response = self.run_test(
            "Admin Update User Status",
            "PUT",
            f"admin/users/{user_id}/status?status=active",
            200,
            admin_auth=True
        )
        
        if success:
            if 'status updated' in response.get('message', '').lower():
                self.log("   ✓ User status updated successfully")
                return True
            else:
                self.log(f"   ⚠️ Unexpected response: {response}")
        return success

    def test_admin_prompts(self):
        """Test admin prompts endpoints"""
        if not self.admin_token:
            self.log("❌ No admin token available")
            return False
            
        success, response = self.run_test(
            "Admin Get Prompts",
            "GET", 
            "admin/prompts",
            200,
            admin_auth=True
        )
        
        if success:
            prompts = response.get('prompts', [])
            self.log(f"   ✓ Retrieved {len(prompts)} prompts")
            
            if prompts:
                # Test updating first prompt
                prompt_id = prompts[0].get('id')
                if prompt_id:
                    return self.test_admin_update_prompt(prompt_id, prompts[0].get('prompt_key'))
                    
        return success

    def test_admin_update_prompt(self, prompt_id, prompt_key):
        """Test admin update prompt endpoint"""
        updated_text = f"Updated prompt text at {datetime.now()}"
        
        success, response = self.run_test(
            "Admin Update Prompt", 
            "PUT",
            f"admin/prompts/{prompt_id}",
            200,
            data={"prompt_key": prompt_key, "prompt_text": updated_text},
            admin_auth=True
        )
        
        if success:
            if 'updated' in response.get('message', '').lower():
                self.log("   ✓ Prompt updated successfully")
                return True
            else:
                self.log(f"   ⚠️ Unexpected response: {response}")
        return success

    def test_admin_topics(self):
        """Test admin topics endpoints"""
        if not self.admin_token:
            self.log("❌ No admin token available")  
            return False
            
        # First get existing topics
        success, response = self.run_test(
            "Admin Get Topics",
            "GET",
            "admin/topics",
            200, 
            admin_auth=True
        )
        
        if not success:
            return False
            
        topics = response.get('topics', [])
        self.log(f"   ✓ Retrieved {len(topics)} topics")
        
        # Test creating new topic
        return self.test_admin_create_topic()

    def test_admin_create_topic(self):
        """Test admin create topic endpoint"""
        timestamp = int(time.time())
        topic_data = {
            "title": f"Test Admin Topic {timestamp}",
            "category": "technology",
            "trend_score": 75
        }
        
        success, response = self.run_test(
            "Admin Create Topic",
            "POST",
            "admin/topics", 
            200,
            data=topic_data,
            admin_auth=True
        )
        
        if success:
            topic = response.get('topic', {})
            if topic.get('title') == topic_data['title']:
                self.created_topic_id = topic.get('id')
                self.log(f"   ✓ Topic created: {topic.get('title')}")
                
                # Test deleting the topic we just created
                if self.created_topic_id:
                    return self.test_admin_delete_topic()
                return True
            else:
                self.log("   ⚠️ Topic not created as expected")
        return success

    def test_admin_delete_topic(self):
        """Test admin delete topic endpoint"""
        if not self.created_topic_id:
            self.log("❌ No topic ID available for deletion")
            return False
            
        success, response = self.run_test(
            "Admin Delete Topic",
            "DELETE",
            f"admin/topics/{self.created_topic_id}",
            200,
            admin_auth=True
        )
        
        if success:
            if 'deleted' in response.get('message', '').lower():
                self.log("   ✓ Topic deleted successfully")
                return True
            else:
                self.log(f"   ⚠️ Unexpected response: {response}")
        return success

    def run_all_new_feature_tests(self):
        """Run comprehensive test suite for new features"""
        self.log("🚀 Starting WTFHappened New Features API Test Suite")
        self.log(f"Testing against: {self.base_url}")
        self.log("-" * 60)
        
        # Setup authentication first
        if not self.setup_user_auth():
            self.log("❌ Failed to setup user authentication")
            return False
            
        # Feature tests
        tests = [
            # FEATURE 1: Forgot/Reset Password Flow
            ("Forgot Password Request", self.test_forgot_password),
            ("Reset Password", self.test_reset_password),
            ("Reset Password Invalid Token", self.test_reset_password_invalid_token),
            
            # FEATURE 2: Profile/Settings Management  
            ("Update Profile", self.test_update_profile),
            ("Change Password", self.test_change_password),
            ("Toggle Auto Renew", self.test_auto_renew_toggle),
            ("Suspend Account", self.test_suspend_account),
            
            # FEATURE 3: Subscription Management
            ("Subscription Info", self.test_subscription_info),
            ("Subscription Checkout", self.test_subscription_checkout),
        ]
        
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                self.log(f"\n📋 {test_name}")
                result = test_func()
                if not result:
                    failed_tests.append(test_name)
                time.sleep(0.5)  # Brief pause between tests
            except Exception as e:
                self.log(f"❌ {test_name} - Exception: {str(e)}")
                failed_tests.append(test_name)
        
        # Admin tests - setup admin auth separately
        if self.setup_admin_auth():
            admin_tests = [
                ("Admin Login Invalid", self.test_admin_login_invalid),
                ("Admin Stats", self.test_admin_stats),
                ("Admin Users Management", self.test_admin_users),
                ("Admin Prompts Management", self.test_admin_prompts),
                ("Admin Topics Management", self.test_admin_topics),
            ]
            
            for test_name, test_func in admin_tests:
                try:
                    self.log(f"\n📋 {test_name}")
                    result = test_func()
                    if not result:
                        failed_tests.append(test_name)
                    time.sleep(0.5)
                except Exception as e:
                    self.log(f"❌ {test_name} - Exception: {str(e)}")
                    failed_tests.append(test_name)
        else:
            self.log("❌ Failed to setup admin authentication - skipping admin tests")
            failed_tests.extend(["Admin Stats", "Admin Users Management", "Admin Prompts Management", "Admin Topics Management"])
        
        # Results summary
        self.log("\n" + "=" * 60)
        self.log("📊 NEW FEATURES TEST RESULTS")
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if failed_tests:
            self.log(f"\n❌ Failed Tests: {', '.join(failed_tests)}")
            return False
        else:
            self.log("\n✅ All new features tests passed!")
            return True

def main():
    """Main test execution"""
    tester = WTFHappenedNewFeaturesAPITester()
    
    try:
        success = tester.run_all_new_feature_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
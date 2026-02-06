import requests
import sys
import time
import json
from datetime import datetime

class QuizPlatformTester:
    def __init__(self, base_url="https://focus-learn-10.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.user_data = None
        self.admin_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.quiz_id = None
        self.result_id = None
        self.created_grade_id = None
        self.created_subject_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, auth_required=True):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            print(f"\n🔍 Testing {name}...")
            print(f"   URL: {url}")
            if data:
                print(f"   Data: {json.dumps(data, indent=2)}")

            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    self.log_test(name, True, f"Status: {response.status_code}")
                    return True, response_data
                except:
                    self.log_test(name, True, f"Status: {response.status_code} (No JSON)")
                    return True, {}
            else:
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    self.log_test(name, False, f"Expected {expected_status}, got {response.status_code} - {error_detail}")
                except:
                    self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, {}

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout after 30 seconds")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error - service may be down")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_server_health(self):
        """Test if server is responding"""
        success, response = self.run_test("Server Health Check", "GET", "", 200, auth_required=False)
        return success

    def test_signup(self):
        """Test user registration"""
        test_user = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "name": "Test User"
        }
        
        success, response = self.run_test("User Signup", "POST", "auth/signup", 200, test_user, auth_required=False)
        
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user_data = response['user']
            print(f"   ✓ Token received and user created: {self.user_data['name']}")
            return True
        return False

    def test_login(self):
        """Test user login with existing credentials"""
        if not self.user_data:
            print("   ⚠️ Cannot test login - no user data from signup")
            return False
            
        login_data = {
            "email": self.user_data['email'],
            "password": "TestPass123!"
        }
        
        success, response = self.run_test("User Login", "POST", "auth/login", 200, login_data, auth_required=False)
        
        if success and 'token' in response:
            self.token = response['token']  # Update token
            print(f"   ✓ Login successful, token updated")
            return True
        return False

    def test_admin_login(self):
        """Test admin user login"""
        admin_credentials = {
            "email": "test@example.com",
            "password": "admin123"
        }
        
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, admin_credentials, auth_required=False)
        
        if success and 'token' in response and 'user' in response:
            self.admin_token = response['token']
            self.admin_data = response['user']
            print(f"   ✓ Admin login successful: {self.admin_data.get('name', 'N/A')}")
            print(f"   ✓ Admin role: {self.admin_data.get('role', 'N/A')}")
            return True
        return False

    def test_get_me(self):
        """Test getting current user info"""
        success, response = self.run_test("Get Current User", "GET", "auth/me", 200)
        
        if success and 'email' in response:
            print(f"   ✓ User info retrieved: {response.get('name', 'N/A')}")
            return True
        return False

    def test_quiz_generation(self):
        """Test AI quiz generation"""
        quiz_request = {
            "subject": "Mathematics",
            "topic": "Basic Algebra",
            "subtopic": "Linear Equations",
            "difficulty": "medium",
            "num_questions": 3
        }
        
        print("   🤖 Testing AI integration - this may take a few seconds...")
        success, response = self.run_test("Quiz Generation (AI)", "POST", "quiz/generate", 200, quiz_request)
        
        if success and 'id' in response and 'questions' in response:
            self.quiz_id = response['id']
            questions = response['questions']
            print(f"   ✓ Quiz generated with {len(questions)} questions")
            print(f"   ✓ Quiz ID: {self.quiz_id}")
            
            # Validate question structure
            for i, q in enumerate(questions):
                if 'id' in q and 'question' in q and 'type' in q:
                    print(f"   ✓ Question {i+1}: {q['type']} - {q['question'][:50]}...")
                else:
                    print(f"   ❌ Question {i+1}: Invalid structure")
                    return False
            return True
        return False

    def test_quiz_submission(self):
        """Test quiz submission"""
        if not self.quiz_id:
            print("   ⚠️ Cannot test submission - no quiz ID")
            return False
        
        # Create sample answers for the quiz
        answers = [
            {
                "question_id": f"q1_{int(time.time())}",
                "user_answer": "A",
                "time_taken": 15.5,
                "is_correct": True
            },
            {
                "question_id": f"q2_{int(time.time())}",  
                "user_answer": "42",
                "time_taken": 12.3,
                "is_correct": True
            },
            {
                "question_id": f"q3_{int(time.time())}",
                "user_answer": "B", 
                "time_taken": 18.2,
                "is_correct": False
            }
        ]
        
        submission_data = {
            "quiz_id": self.quiz_id,
            "answers": answers
        }
        
        success, response = self.run_test("Quiz Submission", "POST", "quiz/submit", 200, submission_data)
        
        if success and 'id' in response:
            self.result_id = response['id']
            print(f"   ✓ Quiz submitted successfully")
            print(f"   ✓ Score: {response.get('score', 'N/A')}%")
            print(f"   ✓ Focus Score: {response.get('focus_score', 'N/A')}")
            print(f"   ✓ Points Earned: {response.get('points_earned', 'N/A')}")
            return True
        return False

    def test_dashboard_analytics(self):
        """Test dashboard analytics"""
        success, response = self.run_test("Dashboard Analytics", "GET", "analytics/dashboard", 200)
        
        if success:
            print(f"   ✓ Total Quizzes: {response.get('total_quizzes', 'N/A')}")
            print(f"   ✓ Avg Score: {response.get('avg_score', 'N/A')}%")
            print(f"   ✓ Avg Focus: {response.get('avg_focus', 'N/A')}")
            print(f"   ✓ Points: {response.get('points', 'N/A')}")
            return True
        return False

    def test_leaderboard(self):
        """Test global leaderboard"""
        success, response = self.run_test("Global Leaderboard", "GET", "leaderboard", 200)
        
        if success and isinstance(response, list):
            print(f"   ✓ Leaderboard loaded with {len(response)} users")
            if response:
                top_user = response[0]
                print(f"   ✓ Top user: {top_user.get('name', 'N/A')} with {top_user.get('points', 'N/A')} points")
            return True
        return False

    def test_topic_leaderboard(self):
        """Test topic-specific leaderboard"""
        success, response = self.run_test("Topic Leaderboard", "GET", "leaderboard/topic/Mathematics/Basic%20Algebra", 200)
        
        if success and isinstance(response, list):
            print(f"   ✓ Topic leaderboard loaded with {len(response)} entries")
            return True
        return False

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Backend API Testing")
        print("=" * 60)
        
        # Test sequence
        test_results = {
            "server_health": self.test_server_health(),
            "signup": self.test_signup(),
            "login": self.test_login(), 
            "get_me": self.test_get_me(),
            "quiz_generation": self.test_quiz_generation(),
            "quiz_submission": self.test_quiz_submission(),
            "dashboard_analytics": self.test_dashboard_analytics(),
            "leaderboard": self.test_leaderboard(),
            "topic_leaderboard": self.test_topic_leaderboard()
        }
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        failed_tests = []
        for test_name, passed in test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            if not passed:
                failed_tests.append(test_name)
        
        print(f"\nOverall: {self.tests_passed}/{self.tests_run} tests passed")
        
        if failed_tests:
            print(f"\n⚠️  Failed tests: {', '.join(failed_tests)}")
            return False
        else:
            print(f"\n🎉 All tests passed! Backend API is fully functional.")
            return True

def main():
    print("Focus Learn Platform - Backend API Testing")
    print("Testing against: https://focus-learn-10.preview.emergentagent.com/api")
    print()
    
    tester = QuizPlatformTester()
    success = tester.run_comprehensive_test()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
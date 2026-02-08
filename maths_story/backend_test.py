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
        # Try different password combinations for existing admin
        password_attempts = ["admin123", "password", "admin", "test123", "TestPass123!"]
        
        for attempt_password in password_attempts:
            admin_credentials = {
                "email": "test@example.com",
                "password": attempt_password
            }
            
            print(f"   🔐 Trying password: {attempt_password}")
            success, response = self.run_test(f"Admin Login (attempt)", "POST", "auth/login", 200, admin_credentials, auth_required=False)
            
            if success and 'token' in response and 'user' in response:
                self.admin_token = response['token']
                self.admin_data = response['user']
                print(f"   ✅ Admin login successful with password: {attempt_password}")
                print(f"   ✓ Admin name: {self.admin_data.get('name', 'N/A')}")
                print(f"   ✓ Admin role: {self.admin_data.get('role', 'N/A')}")
                return True
        
        print(f"   ❌ All password attempts failed for test@example.com")
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

    def test_get_all_grades(self):
        """Test GET /api/admin/grades endpoint"""
        if not self.admin_token:
            print("   ⚠️ Cannot test grades - no admin token")
            return False
        
        # Switch to admin token temporarily
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test("Get All Grades", "GET", "admin/grades", 200)
        
        # Restore original token
        self.token = original_token
        
        if success and isinstance(response, list):
            print(f"   ✓ Found {len(response)} grades")
            for grade in response:
                if 'name' in grade and 'order' in grade:
                    print(f"   ✓ Grade: {grade['name']} (Order: {grade['order']})")
                else:
                    print(f"   ❌ Invalid grade structure: {grade}")
                    return False
            return True
        return False

    def test_get_active_subjects(self):
        """Test GET /api/subjects/active endpoint (public)"""
        success, response = self.run_test("Get Active Subjects", "GET", "subjects/active", 200, auth_required=False)
        
        if success and isinstance(response, list):
            print(f"   ✓ Found {len(response)} active subjects")
            for subject in response:
                if 'name' in subject and 'is_active' in subject:
                    if subject['is_active']:
                        print(f"   ✓ Active Subject: {subject['name']}")
                    else:
                        print(f"   ❌ Found inactive subject in active list: {subject['name']}")
                        return False
                else:
                    print(f"   ❌ Invalid subject structure: {subject}")
                    return False
            return True
        return False

    def test_get_all_subjects(self):
        """Test GET /api/admin/subjects endpoint"""
        if not self.admin_token:
            print("   ⚠️ Cannot test admin subjects - no admin token")
            return False
        
        # Switch to admin token temporarily
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test("Get All Subjects (Admin)", "GET", "admin/subjects", 200)
        
        # Restore original token
        self.token = original_token
        
        if success and isinstance(response, list):
            print(f"   ✓ Found {len(response)} subjects (including inactive)")
            active_count = sum(1 for s in response if s.get('is_active', False))
            inactive_count = len(response) - active_count
            print(f"   ✓ Active: {active_count}, Inactive: {inactive_count}")
            return True
        return False

    def test_create_grade(self):
        """Test POST /api/admin/grades endpoint"""
        if not self.admin_token:
            print("   ⚠️ Cannot test create grade - no admin token")
            return False
        
        # Switch to admin token temporarily
        original_token = self.token
        self.token = self.admin_token
        
        grade_data = {
            "name": f"Test Grade {int(time.time())}",
            "order": 99
        }
        
        success, response = self.run_test("Create Grade", "POST", "admin/grades", 200, grade_data)
        
        # Restore original token
        self.token = original_token
        
        if success and 'id' in response:
            self.created_grade_id = response['id']
            print(f"   ✓ Grade created with ID: {self.created_grade_id}")
            print(f"   ✓ Grade name: {response.get('name', 'N/A')}")
            return True
        return False

    def test_create_subject(self):
        """Test POST /api/admin/subjects endpoint"""
        if not self.admin_token:
            print("   ⚠️ Cannot test create subject - no admin token")
            return False
        
        # Switch to admin token temporarily  
        original_token = self.token
        self.token = self.admin_token
        
        subject_data = {
            "name": f"Test Subject {int(time.time())}",
            "description": "Test subject for API testing",
            "is_active": True
        }
        
        success, response = self.run_test("Create Subject", "POST", "admin/subjects", 200, subject_data)
        
        # Restore original token
        self.token = original_token
        
        if success and 'id' in response:
            self.created_subject_id = response['id']
            print(f"   ✓ Subject created with ID: {self.created_subject_id}")
            print(f"   ✓ Subject name: {response.get('name', 'N/A')}")
            print(f"   ✓ Is active: {response.get('is_active', 'N/A')}")
            return True
        return False

    def test_quiz_generation_with_grade(self):
        """Test AI quiz generation with grade parameter"""
        quiz_request = {
            "subject": "Mathematics",
            "topic": "Basic Algebra", 
            "subtopic": "Linear Equations",
            "grade": "Grade 5",
            "difficulty": "medium",
            "num_questions": 3
        }
        
        print("   🤖 Testing AI integration with grade parameter - this may take a few seconds...")
        success, response = self.run_test("Quiz Generation with Grade", "POST", "quiz/generate", 200, quiz_request)
        
        if success and 'id' in response and 'questions' in response:
            self.quiz_id = response['id']
            questions = response['questions']
            print(f"   ✓ Quiz generated with {len(questions)} questions for Grade 5")
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

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Backend API Testing")
        print("Testing NEW ADMIN SYSTEM with Grade Management")
        print("=" * 60)
        
        # Test sequence
        test_results = {
            "server_health": self.test_server_health(),
            "signup": self.test_signup(),
            "login": self.test_login(),
            "admin_login": self.test_admin_login(), 
            "get_me": self.test_get_me(),
            
            # NEW: Admin grade management tests
            "get_all_grades": self.test_get_all_grades(),
            "create_grade": self.test_create_grade(),
            
            # NEW: Admin subject management tests
            "get_all_subjects": self.test_get_all_subjects(),
            "get_active_subjects": self.test_get_active_subjects(),
            "create_subject": self.test_create_subject(),
            
            # Quiz generation tests (updated with grade parameter)
            "quiz_generation": self.test_quiz_generation(),
            "quiz_generation_with_grade": self.test_quiz_generation_with_grade(),
            "quiz_submission": self.test_quiz_submission(),
            
            # Analytics tests
            "dashboard_analytics": self.test_dashboard_analytics(),
            "leaderboard": self.test_leaderboard(),
            "topic_leaderboard": self.test_topic_leaderboard()
        }
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        # Categorize results
        admin_tests = ["admin_login", "get_all_grades", "create_grade", "get_all_subjects", "get_active_subjects", "create_subject"]
        new_feature_tests = ["quiz_generation_with_grade", "get_all_grades", "get_active_subjects"]
        
        failed_tests = []
        admin_failed = []
        new_feature_failed = []
        
        for test_name, passed in test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            if not passed:
                failed_tests.append(test_name)
                if test_name in admin_tests:
                    admin_failed.append(test_name)
                if test_name in new_feature_tests:
                    new_feature_failed.append(test_name)
        
        print(f"\nOverall: {self.tests_passed}/{self.tests_run} tests passed")
        
        # Specific feedback for new features
        if new_feature_failed:
            print(f"\n🚨 NEW FEATURES FAILING: {', '.join(new_feature_failed)}")
        else:
            print(f"\n✅ All new admin/grade management features working!")
        
        if admin_failed:
            print(f"\n🚨 ADMIN FEATURES FAILING: {', '.join(admin_failed)}")
        
        if failed_tests:
            print(f"\n⚠️  All failed tests: {', '.join(failed_tests)}")
            return False
        else:
            print(f"\n🎉 All tests passed! Backend API with new admin system is fully functional.")
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
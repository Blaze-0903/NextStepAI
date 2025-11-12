import requests
import sys
import json
import os
from datetime import datetime
from pathlib import Path

class NextStepAITester:
    def __init__(self, base_url="https://ontology-webapp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_password = "nextstep2025"

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers)
            elif method == 'POST':
                if files:
                    # For file uploads, don't set Content-Type header
                    response = requests.post(url, data=data, files=files)
                else:
                    response = requests.post(url, json=data, headers=default_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

            return success, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )

    def test_ontology_endpoint(self):
        """Test ontology retrieval"""
        return self.run_test(
            "Get Ontology",
            "GET",
            "ontology",
            200
        )

    def test_admin_login_valid(self):
        """Test admin login with valid password"""
        return self.run_test(
            "Admin Login (Valid)",
            "POST",
            "admin/login",
            200,
            data={"password": self.admin_password}
        )

    def test_admin_login_invalid(self):
        """Test admin login with invalid password"""
        return self.run_test(
            "Admin Login (Invalid)",
            "POST",
            "admin/login",
            401,
            data={"password": "wrongpassword"}
        )

    def test_pending_updates(self):
        """Test getting pending updates"""
        return self.run_test(
            "Get Pending Updates",
            "GET",
            "admin/pending-updates",
            200
        )

    def test_trigger_ontology_update(self):
        """Test triggering ontology update"""
        return self.run_test(
            "Trigger Ontology Update",
            "POST",
            "trigger-ontology-update",
            200
        )

    def test_resume_upload_no_file(self):
        """Test resume upload without file"""
        return self.run_test(
            "Resume Upload (No File)",
            "POST",
            "upload-resume",
            422  # FastAPI validation error
        )

    def create_sample_resume_file(self):
        """Create a sample resume file for testing"""
        sample_resume_content = """
        John Doe
        Software Engineer
        
        Skills:
        - Python programming with 5 years experience
        - JavaScript and React development
        - Machine Learning and Data Analysis
        - SQL database management
        - Git version control
        - Docker containerization
        - AWS cloud services
        - REST API development
        - Problem solving and communication skills
        
        Experience:
        Senior Software Engineer at Tech Corp (2020-2024)
        - Developed web applications using React and Node.js
        - Implemented machine learning models using Python and TensorFlow
        - Managed databases with SQL and MongoDB
        - Deployed applications on AWS using Docker
        
        Education:
        Bachelor of Computer Science
        """
        
        # Create a temporary text file (we'll test with .txt first, then proper formats)
        temp_file_path = "/tmp/sample_resume.txt"
        with open(temp_file_path, 'w') as f:
            f.write(sample_resume_content)
        
        return temp_file_path

    def test_resume_upload_invalid_format(self):
        """Test resume upload with invalid file format"""
        # Create sample file
        file_path = self.create_sample_resume_file()
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': ('sample_resume.txt', f, 'text/plain')}
                success, response = self.run_test(
                    "Resume Upload (Invalid Format)",
                    "POST",
                    "upload-resume",
                    400,  # Should reject non-PDF/DOCX files
                    files=files
                )
            return success, response
        finally:
            # Clean up
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_admin_review_nonexistent(self):
        """Test reviewing non-existent update"""
        return self.run_test(
            "Admin Review (Non-existent)",
            "POST",
            "admin/review",
            404,
            data={
                "update_id": "nonexistent-id",
                "decision": "approve",
                "reviewer_name": "Admin"
            }
        )

def main():
    print("="*60)
    print("NEXTSTEAI BACKEND API TESTING")
    print(f"Timestamp: {datetime.now()}")
    print("="*60)

    # Setup
    tester = NextStepAITester()

    # Run basic API tests
    print("\n📋 BASIC API TESTS")
    tester.test_root_endpoint()
    tester.test_ontology_endpoint()

    # Test admin functionality
    print("\n🔐 ADMIN AUTHENTICATION TESTS")
    tester.test_admin_login_valid()
    tester.test_admin_login_invalid()
    tester.test_pending_updates()

    # Test ontology update
    print("\n🔄 ONTOLOGY UPDATE TESTS")
    tester.test_trigger_ontology_update()

    # Test resume upload
    print("\n📄 RESUME UPLOAD TESTS")
    tester.test_resume_upload_no_file()
    tester.test_resume_upload_invalid_format()

    # Test admin review
    print("\n👨‍💼 ADMIN REVIEW TESTS")
    tester.test_admin_review_nonexistent()

    # Print results
    print("\n" + "="*60)
    print(f"📊 BACKEND TEST RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    print("="*60)

    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
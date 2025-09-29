#!/usr/bin/env python3
"""
Smart Face Analytics Backend API Testing
Tests all API endpoints for the face analysis application
"""

import requests
import sys
import json
import base64
import io
from datetime import datetime
from PIL import Image, ImageDraw
import numpy as np

class FaceAnalyticsAPITester:
    def __init__(self, base_url="https://facerecognize-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def create_test_image(self):
        """Create a simple test image with a face-like shape"""
        # Create a 300x300 RGB image
        img = Image.new('RGB', (300, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple face-like shape
        # Head (circle)
        draw.ellipse([75, 50, 225, 200], fill='peachpuff', outline='black', width=2)
        
        # Eyes
        draw.ellipse([100, 100, 120, 120], fill='black')
        draw.ellipse([180, 100, 200, 120], fill='black')
        
        # Nose
        draw.polygon([(150, 130), (140, 150), (160, 150)], fill='pink')
        
        # Mouth
        draw.arc([125, 160, 175, 180], 0, 180, fill='red', width=3)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return img_base64, img_bytes

    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {data.get('status', 'unknown')}"
            else:
                details = f"Status code: {response.status_code}"
                
            self.log_test("Health Check", success, details, response.json() if success else None)
            return success
            
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_root_endpoint(self):
        """Test root API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Message: {data.get('message', 'No message')}"
            else:
                details = f"Status code: {response.status_code}"
                
            self.log_test("Root Endpoint", success, details, response.json() if success else None)
            return success
            
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_model_info(self):
        """Test model info endpoint"""
        try:
            response = requests.get(f"{self.api_url}/models/info", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Models loaded: {data.get('status', 'unknown')}"
            else:
                details = f"Status code: {response.status_code}"
                
            self.log_test("Model Info", success, details, response.json() if success else None)
            return success
            
        except Exception as e:
            self.log_test("Model Info", False, f"Exception: {str(e)}")
            return False

    def test_analyze_image(self):
        """Test image analysis endpoint"""
        try:
            img_base64, _ = self.create_test_image()
            
            payload = {
                "image_data": img_base64,
                "session_id": self.session_id
            }
            
            response = requests.post(
                f"{self.api_url}/analyze-image", 
                json=payload, 
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                faces_detected = data.get('faces_detected', 0)
                processing_time = data.get('processing_time_ms', 0)
                details = f"Faces detected: {faces_detected}, Processing time: {processing_time:.2f}ms"
            else:
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("Analyze Image", success, details, response.json() if success else None)
            return success, response.json() if success else None
            
        except Exception as e:
            self.log_test("Analyze Image", False, f"Exception: {str(e)}")
            return False, None

    def test_analyze_upload(self):
        """Test file upload analysis endpoint"""
        try:
            _, img_bytes = self.create_test_image()
            
            files = {
                'file': ('test_face.jpg', img_bytes, 'image/jpeg')
            }
            data = {
                'session_id': self.session_id
            }
            
            response = requests.post(
                f"{self.api_url}/analyze-upload", 
                files=files,
                data=data,
                timeout=30
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                faces_detected = data.get('faces_detected', 0)
                processing_time = data.get('processing_time_ms', 0)
                details = f"Faces detected: {faces_detected}, Processing time: {processing_time:.2f}ms"
            else:
                try:
                    error_data = response.json()
                    details = f"Status: {response.status_code}, Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("Analyze Upload", success, details, response.json() if success else None)
            return success
            
        except Exception as e:
            self.log_test("Analyze Upload", False, f"Exception: {str(e)}")
            return False

    def test_analysis_history(self):
        """Test analysis history endpoint"""
        try:
            response = requests.get(
                f"{self.api_url}/analysis-history?session_id={self.session_id}", 
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                history_count = len(data) if isinstance(data, list) else 0
                details = f"History entries: {history_count}"
            else:
                details = f"Status code: {response.status_code}"
                
            self.log_test("Analysis History", success, details, response.json() if success else None)
            return success
            
        except Exception as e:
            self.log_test("Analysis History", False, f"Exception: {str(e)}")
            return False

    def test_analytics_summary(self):
        """Test analytics summary endpoint"""
        try:
            response = requests.get(
                f"{self.api_url}/analytics/summary?session_id={self.session_id}", 
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                total_analyses = data.get('total_analyses', 0)
                total_faces = data.get('total_faces', 0)
                details = f"Total analyses: {total_analyses}, Total faces: {total_faces}"
            else:
                details = f"Status code: {response.status_code}"
                
            self.log_test("Analytics Summary", success, details, response.json() if success else None)
            return success
            
        except Exception as e:
            self.log_test("Analytics Summary", False, f"Exception: {str(e)}")
            return False

    def test_clear_history(self):
        """Test clear history endpoint"""
        try:
            response = requests.delete(
                f"{self.api_url}/analysis-history?session_id={self.session_id}", 
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                deleted_count = data.get('deleted_count', 0)
                details = f"Deleted entries: {deleted_count}"
            else:
                details = f"Status code: {response.status_code}"
                
            self.log_test("Clear History", success, details, response.json() if success else None)
            return success
            
        except Exception as e:
            self.log_test("Clear History", False, f"Exception: {str(e)}")
            return False

    def test_status_endpoints(self):
        """Test status check endpoints"""
        try:
            # Test POST status
            payload = {"client_name": "test_client"}
            response = requests.post(
                f"{self.api_url}/status", 
                json=payload, 
                timeout=10
            )
            
            post_success = response.status_code == 200
            
            # Test GET status
            response = requests.get(f"{self.api_url}/status", timeout=10)
            get_success = response.status_code == 200
            
            success = post_success and get_success
            details = f"POST: {post_success}, GET: {get_success}"
            
            self.log_test("Status Endpoints", success, details)
            return success
            
        except Exception as e:
            self.log_test("Status Endpoints", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting Smart Face Analytics API Tests")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🔑 Session ID: {self.session_id}")
        print("=" * 60)
        
        # Basic connectivity tests
        print("\n📡 Testing Basic Connectivity...")
        self.test_health_check()
        self.test_root_endpoint()
        self.test_model_info()
        
        # Core functionality tests
        print("\n🧠 Testing Core Face Analysis...")
        analyze_success, analyze_data = self.test_analyze_image()
        self.test_analyze_upload()
        
        # Data management tests
        print("\n📊 Testing Data Management...")
        self.test_analysis_history()
        self.test_analytics_summary()
        
        # Additional endpoints
        print("\n🔧 Testing Additional Endpoints...")
        self.test_status_endpoints()
        self.test_clear_history()
        
        # Final results
        print("\n" + "=" * 60)
        print(f"📊 Test Results Summary:")
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Detailed failure analysis
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests Details:")
            for test in failed_tests:
                print(f"  • {test['test_name']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = FaceAnalyticsAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
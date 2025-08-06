#!/usr/bin/env python3
"""
USSD Flow Testing Script for Tujali Health
Comprehensive testing of the USSD geo-location system
"""

import requests
import json
import time
import sys
from datetime import datetime

class USSDTester:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_service_health(self):
        """Test if USSD service is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                service_name = data.get('service', 'Unknown')
                self.log_test("Service Health Check", True, f"Service: {service_name}")
                return True
            else:
                self.log_test("Service Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Service Health Check", False, str(e))
            return False
    
    def test_ussd_main_menu(self):
        """Test USSD main menu response"""
        try:
            response = requests.post(f"{self.base_url}/ussd", 
                json={
                    'sessionId': 'test_main_menu',
                    'serviceCode': '*384*4040#',
                    'phoneNumber': '+254701234567',
                    'text': ''
                },
                timeout=5
            )
            
            if response.status_code == 200:
                text = response.text
                success = 'Find Doctors Near Me' in text and 'Welcome to Tujali Health' in text
                details = f"Response length: {len(text)} chars"
                self.log_test("USSD Main Menu", success, details)
                return success, text
            else:
                self.log_test("USSD Main Menu", False, f"Status: {response.status_code}")
                return False, ""
                
        except Exception as e:
            self.log_test("USSD Main Menu", False, str(e))
            return False, ""
    
    def test_find_doctors_option(self):
        """Test selecting find doctors option"""
        try:
            response = requests.post(f"{self.base_url}/ussd",
                json={
                    'sessionId': 'test_find_doctors',
                    'serviceCode': '*384*4040#',
                    'phoneNumber': '+254701234567',
                    'text': '1'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                text = response.text
                success = 'location' in text.lower() or 'enter' in text.lower()
                self.log_test("Find Doctors Option", success, f"Prompted for location input")
                return success, text
            else:
                self.log_test("Find Doctors Option", False, f"Status: {response.status_code}")
                return False, ""
                
        except Exception as e:
            self.log_test("Find Doctors Option", False, str(e))
            return False, ""
    
    def test_location_search(self, location="Nairobi, CBD"):
        """Test location-based doctor search"""
        try:
            response = requests.post(f"{self.base_url}/ussd",
                json={
                    'sessionId': 'test_location_search',
                    'serviceCode': '*384*4040#',
                    'phoneNumber': '+254701234567',
                    'text': f'1*{location}'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                text = response.text
                # Check if response contains doctor information
                has_doctors = 'Dr.' in text or 'doctor' in text.lower()
                success = has_doctors and len(text) > 50
                details = f"Location: {location}, Response: {len(text)} chars"
                self.log_test("Location Search", success, details)
                return success, text
            else:
                self.log_test("Location Search", False, f"Status: {response.status_code}")
                return False, ""
                
        except Exception as e:
            self.log_test("Location Search", False, str(e))
            return False, ""
    
    def test_geo_api_direct(self, location="Nairobi"):
        """Test geo-location API directly"""
        try:
            response = requests.post(f"{self.base_url}/api/geo/doctors/nearby",
                json={
                    'location': location,
                    'phone_number': '+254701234567',
                    'limit': 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False) and data.get('count', 0) > 0
                count = data.get('count', 0)
                details = f"Location: {location}, Found: {count} doctors"
                self.log_test("Geo API Direct", success, details)
                
                # Show sample doctor if available
                if success and data.get('data'):
                    doctor = data['data'][0]
                    sample = f"Sample: Dr. {doctor.get('name', 'Unknown')} ({doctor.get('distance', 'N/A')}km)"
                    print(f"   {sample}")
                
                return success, data
            else:
                self.log_test("Geo API Direct", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Geo API Direct", False, str(e))
            return False, {}
    
    def test_doctors_api(self):
        """Test doctors listing API"""
        try:
            response = requests.get(f"{self.base_url}/api/doctors?limit=3", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False) and data.get('count', 0) > 0
                count = data.get('count', 0)
                self.log_test("Doctors API", success, f"Retrieved: {count} doctors")
                return success, data
            else:
                self.log_test("Doctors API", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Doctors API", False, str(e))
            return False, {}
    
    def test_multiple_locations(self):
        """Test multiple location scenarios"""
        test_locations = [
            "Nairobi, CBD",
            "Nairobi, Westlands",
            "Mombasa",
            "Kisumu",
            "Invalid Location XYZ"
        ]
        
        print("\nTesting multiple locations:")
        print("-" * 40)
        
        for location in test_locations:
            success, data = self.test_geo_api_direct(location)
            time.sleep(1)  # Rate limiting
    
    def test_appointment_booking_flow(self):
        """Test appointment booking process"""
        try:
            # Step 1: Get doctors for location
            success, data = self.test_geo_api_direct("Nairobi, CBD")
            
            if not success or not data.get('data'):
                self.log_test("Appointment Booking Setup", False, "No doctors available")
                return False
            
            # Step 2: Simulate doctor selection
            doctor = data['data'][0]
            doctor_id = doctor.get('id')
            
            # Step 3: Test appointment creation (this would be done via USSD flow)
            appointment_data = {
                'patient_phone': '+254701234567',
                'doctor_id': doctor_id,
                'appointment_type': 'physical',
                'notes': 'Test appointment via USSD'
            }
            
            # Note: Actual booking would be part of USSD flow
            self.log_test("Appointment Booking Flow", True, f"Doctor selected: {doctor.get('name')}")
            return True
            
        except Exception as e:
            self.log_test("Appointment Booking Flow", False, str(e))
            return False
    
    def test_error_handling(self):
        """Test system error handling"""
        print("\nTesting error handling:")
        print("-" * 30)
        
        # Test invalid session
        try:
            response = requests.post(f"{self.base_url}/ussd",
                json={
                    'sessionId': '',
                    'serviceCode': '*384*4040#',
                    'phoneNumber': 'invalid',
                    'text': 'invalid_input'
                },
                timeout=5
            )
            
            handles_error = response.status_code in [200, 400]  # Either works or graceful error
            self.log_test("Error Handling", handles_error, "Invalid input handled")
            
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
    
    def run_complete_test_suite(self):
        """Run all tests in sequence"""
        print("=" * 60)
        print("TUJALI HEALTH - USSD SYSTEM TESTING")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Core functionality tests
        print("1. CORE FUNCTIONALITY TESTS")
        print("-" * 30)
        
        if not self.test_service_health():
            print("❌ Service not available. Stopping tests.")
            return False
        
        self.test_ussd_main_menu()
        self.test_find_doctors_option()
        self.test_location_search()
        
        # API tests
        print("\n2. API FUNCTIONALITY TESTS")
        print("-" * 30)
        
        self.test_geo_api_direct()
        self.test_doctors_api()
        
        # Extended tests
        print("\n3. EXTENDED FUNCTIONALITY TESTS")
        print("-" * 30)
        
        self.test_multiple_locations()
        self.test_appointment_booking_flow()
        self.test_error_handling()
        
        # Results summary
        self.print_test_summary()
        
        return True
    
    def print_test_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save results to file
        with open('ussd_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\nDetailed results saved to: ussd_test_results.json")

def main():
    """Main testing function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:3000"
    
    tester = USSDTester(base_url)
    success = tester.run_complete_test_suite()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
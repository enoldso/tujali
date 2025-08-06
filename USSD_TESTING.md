# USSD Testing Guidelines - Tujali Health System

## Overview
This guide provides comprehensive testing procedures for the Tujali Health USSD geo-location system that allows patients to find nearby doctors and book appointments using the access code `*384*4040#`.

## System Architecture
- **Flask Dashboard**: http://localhost:5000 (Healthcare provider interface)
- **Node.js USSD Service**: http://localhost:3000 (Patient USSD interface)
- **USSD Access Code**: `*384*4040#`
- **Database**: PostgreSQL with shared schema

## Prerequisites
1. Both Flask and Node.js services must be running
2. Database connection established
3. Sample doctor data populated

## Testing Methods

### 1. Manual API Testing

#### A. Health Check
```bash
# Test if USSD service is running
curl -X GET http://localhost:3000/health

# Expected response:
{
  "status": "OK",
  "service": "Tujali USSD Geo Service",
  "version": "1.0.0",
  "timestamp": "2025-06-25T14:59:00.000Z"
}
```

#### B. USSD Flow Testing
```bash
# Step 1: Main Menu
curl -X POST http://localhost:3000/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_001",
    "serviceCode": "*384*4040#",
    "phoneNumber": "+254701234567",
    "text": ""
  }'

# Expected: Main menu with options 1-4

# Step 2: Select Find Doctors
curl -X POST http://localhost:3000/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_002",
    "serviceCode": "*384*4040#",
    "phoneNumber": "+254701234567",
    "text": "1"
  }'

# Expected: Location input prompt

# Step 3: Enter Location
curl -X POST http://localhost:3000/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_003",
    "serviceCode": "*384*4040#",
    "phoneNumber": "+254701234567",
    "text": "1*Nairobi, CBD"
  }'

# Expected: List of nearby doctors with details
```

#### C. Geo-Location API Testing
```bash
# Test nearby doctors search
curl -X POST http://localhost:3000/api/geo/doctors/nearby \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Nairobi, Westlands",
    "phone_number": "+254701234567",
    "limit": 5
  }'

# Expected response:
{
  "success": true,
  "count": 3,
  "data": [
    {
      "id": 1,
      "name": "Sarah Wanjiku",
      "specialization": "General Practitioner",
      "distance": "2.3",
      "location": "Nairobi, Westlands",
      "consultation_fee": 1500,
      "phone_number": "+254712345678"
    }
  ]
}
```

### 2. Python Test Scripts

#### A. Complete System Test
```python
# Run the comprehensive test
python test-complete-system.py

# This tests:
# - Flask dashboard accessibility
# - USSD service health
# - USSD flow functionality
# - Geo-location API
# - Doctors API
```

#### B. USSD Flow Simulation
```python
import requests

def test_ussd_flow():
    base_url = "http://localhost:3000"
    
    # Test data
    test_cases = [
        {
            "step": "Main Menu",
            "data": {
                "sessionId": "test_main",
                "serviceCode": "*384*4040#",
                "phoneNumber": "+254701234567",
                "text": ""
            }
        },
        {
            "step": "Find Doctors",
            "data": {
                "sessionId": "test_doctors",
                "serviceCode": "*384*4040#",
                "phoneNumber": "+254701234567",
                "text": "1"
            }
        },
        {
            "step": "Location Search",
            "data": {
                "sessionId": "test_location",
                "serviceCode": "*384*4040#",
                "phoneNumber": "+254701234567",
                "text": "1*Nairobi"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"Testing: {test_case['step']}")
        response = requests.post(f"{base_url}/ussd", json=test_case['data'])
        print(f"Response: {response.text[:100]}...")
```

### 3. Location Testing Scenarios

Test various location inputs to verify geo-location accuracy:

#### Valid Location Formats
- City names: "Nairobi", "Mombasa", "Kisumu"
- City with area: "Nairobi, CBD", "Nairobi, Westlands"
- Landmarks: "Uhuru Park", "KICC", "Westgate Mall"
- GPS coordinates: "-1.2921,36.8219"

#### Test Locations
```bash
# Test different locations
locations=(
  "Nairobi, CBD"
  "Nairobi, Westlands"
  "Nairobi, Karen"
  "Mombasa, Nyali"
  "Kisumu, Kondele"
  "Nakuru, Stadium"
  "Eldoret, Langas"
)

for location in "${locations[@]}"; do
  echo "Testing location: $location"
  curl -X POST http://localhost:3000/api/geo/doctors/nearby \
    -H "Content-Type: application/json" \
    -d "{\"location\": \"$location\", \"phone_number\": \"+254701234567\", \"limit\": 3}"
done
```

### 4. Error Handling Tests

#### A. Invalid Inputs
```bash
# Test empty location
curl -X POST http://localhost:3000/api/geo/doctors/nearby \
  -H "Content-Type: application/json" \
  -d '{"location": "", "phone_number": "+254701234567"}'

# Test invalid phone number
curl -X POST http://localhost:3000/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_invalid",
    "serviceCode": "*384*4040#",
    "phoneNumber": "invalid_number",
    "text": ""
  }'
```

#### B. Database Connection Issues
```bash
# Test service behavior when database is unavailable
# (Stop database temporarily and test)
curl -X GET http://localhost:3000/health
```

### 5. Performance Testing

#### A. Load Testing
```python
import threading
import requests
import time

def stress_test_ussd():
    def make_request(session_id):
        try:
            response = requests.post('http://localhost:3000/ussd', 
                json={
                    'sessionId': f'stress_{session_id}',
                    'serviceCode': '*384*4040#',
                    'phoneNumber': f'+25470123{session_id:04d}',
                    'text': '1*Nairobi'
                },
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    # Create 50 concurrent requests
    threads = []
    results = []
    
    for i in range(50):
        thread = threading.Thread(target=lambda i=i: results.append(make_request(i)))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    success_rate = sum(results) / len(results) * 100
    print(f"Success rate: {success_rate}%")

stress_test_ussd()
```

### 6. User Experience Testing

#### A. USSD Flow Validation
Test the complete user journey:

1. **Menu Navigation**
   - Main menu displays correctly
   - Options are numbered and clear
   - Navigation works with numeric inputs

2. **Location Input**
   - Accepts various location formats
   - Provides helpful error messages
   - Handles typos gracefully

3. **Doctor Results**
   - Shows relevant doctors sorted by distance
   - Displays complete information (name, specialty, distance, fee)
   - Provides booking options

4. **Appointment Booking**
   - Allows selection of doctor
   - Offers appointment types (physical/teleconsultation)
   - Confirms booking details

#### B. Multi-language Testing
```bash
# Test Swahili responses (when implemented)
curl -X POST http://localhost:3000/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test_swahili",
    "serviceCode": "*384*4040#",
    "phoneNumber": "+254701234567",
    "text": "",
    "language": "sw"
  }'
```

### 7. Integration Testing

#### A. Flask Dashboard Integration
1. Create appointment via USSD
2. Verify it appears in Flask dashboard
3. Update appointment status in dashboard
4. Check if changes reflect in USSD system

#### B. Database Consistency
```sql
-- Check USSD sessions are logged
SELECT * FROM ussd_sessions ORDER BY created_at DESC LIMIT 10;

-- Verify appointment creation
SELECT * FROM appointments WHERE source = 'ussd' ORDER BY created_at DESC LIMIT 5;

-- Check patient records
SELECT * FROM patients WHERE phone_number LIKE '+2547%' ORDER BY created_at DESC LIMIT 5;
```

### 8. Production Readiness Tests

#### A. Security Testing
- Test SQL injection attempts
- Verify input sanitization
- Check session management
- Test rate limiting

#### B. Monitoring
- Check log files for errors
- Monitor response times
- Verify error reporting
- Test graceful degradation

### 9. Expected Results

#### Successful USSD Flow Response Examples:

**Main Menu:**
```
CON Welcome to Tujali Health 🏥
Find doctors near you and book appointments

1. Find Doctors Near Me
2. My Appointments
3. Emergency Services
4. Health Information
0. Exit
```

**Doctor Results:**
```
CON 📍 Doctors near Nairobi, CBD:

1. Dr. Sarah Wanjiku (2.3km)
   General Practitioner
   Westlands Medical Center
   Fee: KSh 1,500
   📞 +254712345678

2. Dr. James Kipchoge (5.1km)
   Pediatrician
   Karen Hospital
   Fee: KSh 2,000
   📞 +254723456789

Reply with doctor number to book
0. Back to main menu
```

### 10. Troubleshooting Common Issues

#### Issue: "Service unavailable" error
- Check if Node.js service is running on port 3000
- Verify database connection
- Check service logs

#### Issue: No doctors found
- Verify sample doctor data exists in database
- Check if doctors have latitude/longitude coordinates
- Test geo-location service

#### Issue: USSD flow breaks
- Check session management
- Verify input parsing
- Review error handling logic

### 11. Automated Testing Setup

Create automated test suite:
```bash
# Install testing dependencies
npm install --save-dev jest supertest

# Run automated tests
npm test
```

## Quick Test Commands

```bash
# 1. Check services
curl http://localhost:5000/health  # Flask
curl http://localhost:3000/health  # USSD

# 2. Test USSD main menu
curl -X POST http://localhost:3000/ussd -H "Content-Type: application/json" -d '{"sessionId":"test","serviceCode":"*384*4040#","phoneNumber":"+254701234567","text":""}'

# 3. Test doctor search
curl -X POST http://localhost:3000/api/geo/doctors/nearby -H "Content-Type: application/json" -d '{"location":"Nairobi","phone_number":"+254701234567","limit":3}'

# 4. Run complete system test
python test-complete-system.py
```

This comprehensive testing approach ensures the USSD geo-location system works reliably for patients seeking healthcare services in Kenya.
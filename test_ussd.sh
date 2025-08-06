#!/bin/bash
# USSD Testing Script for Tujali Health System
# Quick testing commands for the USSD geo-location service

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
USSD_URL="http://localhost:3000"
FLASK_URL="http://localhost:5000"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}    TUJALI HEALTH - USSD TESTING SCRIPT${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Function to test service health
test_service_health() {
    echo -e "${YELLOW}Testing Service Health...${NC}"
    
    # Test Flask service
    if curl -s -f "${FLASK_URL}/health" > /dev/null 2>&1 || curl -s -f "${FLASK_URL}/" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Flask Dashboard: Running${NC}"
    else
        echo -e "${RED}✗ Flask Dashboard: Not accessible${NC}"
    fi
    
    # Test USSD service
    if curl -s -f "${USSD_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ USSD Service: Running${NC}"
        return 0
    else
        echo -e "${RED}✗ USSD Service: Not running${NC}"
        return 1
    fi
    echo
}

# Function to test USSD main menu
test_main_menu() {
    echo -e "${YELLOW}Testing USSD Main Menu...${NC}"
    
    response=$(curl -s -X POST "${USSD_URL}/ussd" \
        -H "Content-Type: application/json" \
        -d '{
            "sessionId": "test_main",
            "serviceCode": "*384*4040#",
            "phoneNumber": "+254701234567",
            "text": ""
        }' 2>/dev/null)
    
    if echo "$response" | grep -q "Find Doctors Near Me"; then
        echo -e "${GREEN}✓ Main menu working${NC}"
        echo "Response preview: $(echo "$response" | head -c 100)..."
    else
        echo -e "${RED}✗ Main menu failed${NC}"
        echo "Response: $response"
    fi
    echo
}

# Function to test doctor search
test_doctor_search() {
    echo -e "${YELLOW}Testing Doctor Search...${NC}"
    
    response=$(curl -s -X POST "${USSD_URL}/ussd" \
        -H "Content-Type: application/json" \
        -d '{
            "sessionId": "test_search",
            "serviceCode": "*384*4040#",
            "phoneNumber": "+254701234567",
            "text": "1*Nairobi, CBD"
        }' 2>/dev/null)
    
    if [ ${#response} -gt 50 ]; then
        echo -e "${GREEN}✓ Doctor search returning results${NC}"
        echo "Response length: ${#response} characters"
    else
        echo -e "${RED}✗ Doctor search failed or no results${NC}"
        echo "Response: $response"
    fi
    echo
}

# Function to test geo API
test_geo_api() {
    echo -e "${YELLOW}Testing Geo-Location API...${NC}"
    
    response=$(curl -s -X POST "${USSD_URL}/api/geo/doctors/nearby" \
        -H "Content-Type: application/json" \
        -d '{
            "location": "Nairobi, Westlands",
            "phone_number": "+254701234567",
            "limit": 3
        }' 2>/dev/null)
    
    if echo "$response" | grep -q '"success":true'; then
        count=$(echo "$response" | grep -o '"count":[0-9]*' | cut -d':' -f2)
        echo -e "${GREEN}✓ Geo API working - Found $count doctors${NC}"
        
        # Extract first doctor name if available
        doctor_name=$(echo "$response" | grep -o '"name":"[^"]*' | head -1 | cut -d'"' -f4)
        if [ ! -z "$doctor_name" ]; then
            echo "Sample doctor: Dr. $doctor_name"
        fi
    else
        echo -e "${RED}✗ Geo API failed${NC}"
        echo "Response: $response"
    fi
    echo
}

# Function to test doctors API
test_doctors_api() {
    echo -e "${YELLOW}Testing Doctors API...${NC}"
    
    response=$(curl -s "${USSD_URL}/api/doctors?limit=3" 2>/dev/null)
    
    if echo "$response" | grep -q '"success":true'; then
        count=$(echo "$response" | grep -o '"count":[0-9]*' | cut -d':' -f2)
        echo -e "${GREEN}✓ Doctors API working - Retrieved $count doctors${NC}"
    else
        echo -e "${RED}✗ Doctors API failed${NC}"
        echo "Response: $response"
    fi
    echo
}

# Function to test multiple locations
test_multiple_locations() {
    echo -e "${YELLOW}Testing Multiple Locations...${NC}"
    
    locations=("Nairobi" "Mombasa" "Kisumu" "Nakuru")
    
    for location in "${locations[@]}"; do
        echo -n "Testing $location: "
        
        response=$(curl -s -X POST "${USSD_URL}/api/geo/doctors/nearby" \
            -H "Content-Type: application/json" \
            -d "{\"location\": \"$location\", \"phone_number\": \"+254701234567\", \"limit\": 2}" 2>/dev/null)
        
        if echo "$response" | grep -q '"success":true'; then
            count=$(echo "$response" | grep -o '"count":[0-9]*' | cut -d':' -f2)
            echo -e "${GREEN}✓ ($count doctors)${NC}"
        else
            echo -e "${RED}✗ Failed${NC}"
        fi
        
        sleep 0.5  # Rate limiting
    done
    echo
}

# Function to run performance test
test_performance() {
    echo -e "${YELLOW}Testing Performance (10 concurrent requests)...${NC}"
    
    start_time=$(date +%s.%N)
    
    for i in {1..10}; do
        (curl -s -X POST "${USSD_URL}/ussd" \
            -H "Content-Type: application/json" \
            -d "{\"sessionId\": \"perf_test_$i\", \"serviceCode\": \"*384*4040#\", \"phoneNumber\": \"+25470123456$i\", \"text\": \"\"}" \
            > /dev/null 2>&1) &
    done
    
    wait
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l)
    
    echo -e "${GREEN}✓ Performance test completed in ${duration%.*} seconds${NC}"
    echo
}

# Function to show demo flow
show_demo_flow() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}           USSD DEMO FLOW${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo
    
    echo -e "${YELLOW}Step 1: Patient dials *384*4040#${NC}"
    main_menu=$(curl -s -X POST "${USSD_URL}/ussd" \
        -H "Content-Type: application/json" \
        -d '{
            "sessionId": "demo_main",
            "serviceCode": "*384*4040#",
            "phoneNumber": "+254701234567",
            "text": ""
        }' 2>/dev/null)
    echo "$main_menu"
    echo
    
    echo -e "${YELLOW}Step 2: Patient selects '1' - Find Doctors${NC}"
    location_prompt=$(curl -s -X POST "${USSD_URL}/ussd" \
        -H "Content-Type: application/json" \
        -d '{
            "sessionId": "demo_location",
            "serviceCode": "*384*4040#",
            "phoneNumber": "+254701234567",
            "text": "1"
        }' 2>/dev/null)
    echo "$location_prompt"
    echo
    
    echo -e "${YELLOW}Step 3: Patient enters 'Nairobi, Westlands'${NC}"
    doctor_results=$(curl -s -X POST "${USSD_URL}/ussd" \
        -H "Content-Type: application/json" \
        -d '{
            "sessionId": "demo_results",
            "serviceCode": "*384*4040#",
            "phoneNumber": "+254701234567",
            "text": "1*Nairobi, Westlands"
        }' 2>/dev/null)
    echo "$doctor_results"
    echo
}

# Function to run all tests
run_all_tests() {
    echo -e "${BLUE}Running Complete Test Suite...${NC}"
    echo
    
    # Check if services are running
    if ! test_service_health; then
        echo -e "${RED}Services not available. Exiting.${NC}"
        exit 1
    fi
    
    # Run individual tests
    test_main_menu
    test_doctor_search
    test_geo_api
    test_doctors_api
    test_multiple_locations
    test_performance
    
    echo -e "${GREEN}✓ All tests completed!${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [option]"
    echo
    echo "Options:"
    echo "  health      - Test service health"
    echo "  menu        - Test USSD main menu"
    echo "  search      - Test doctor search"
    echo "  geo         - Test geo-location API"
    echo "  doctors     - Test doctors API"
    echo "  locations   - Test multiple locations"
    echo "  performance - Run performance test"
    echo "  demo        - Show complete demo flow"
    echo "  all         - Run all tests (default)"
    echo
}

# Main script logic
case "${1:-all}" in
    "health")
        test_service_health
        ;;
    "menu")
        test_main_menu
        ;;
    "search")
        test_doctor_search
        ;;
    "geo")
        test_geo_api
        ;;
    "doctors")
        test_doctors_api
        ;;
    "locations")
        test_multiple_locations
        ;;
    "performance")
        test_performance
        ;;
    "demo")
        show_demo_flow
        ;;
    "all")
        run_all_tests
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        show_usage
        exit 1
        ;;
esac

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Testing completed. USSD Access Code: *384*4040#${NC}"
echo -e "${BLUE}Services: Flask (${FLASK_URL}) | USSD (${USSD_URL})${NC}"
echo -e "${BLUE}================================================${NC}"
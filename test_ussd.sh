#!/bin/bash
# Tujali Telehealth USSD Testing Script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}  Tujali Telehealth USSD Tester  ${NC}"
echo -e "${BLUE}=================================${NC}"
echo

# Check if main application is running
if ! curl -s http://localhost:5000 > /dev/null; then
    echo -e "${YELLOW}Warning: The main application doesn't seem to be running at http://localhost:5000${NC}"
    echo -e "${YELLOW}Start the application first with:${NC} gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"
    echo
fi

# Function to display menu
show_menu() {
    echo "Choose a testing option:"
    echo "1) Run interactive USSD tester"
    echo "2) Run automated registration flow test"
    echo "3) Run automated symptom reporting flow test"
    echo "4) Run automated health information flow test"
    echo "5) Start USSD simulator web interface"
    echo "6) Exit"
    echo
    echo -n "Enter your choice [1-6]: "
}

# Main loop
while true; do
    show_menu
    read -r choice
    
    case $choice in
        1)
            echo -e "\n${GREEN}Starting interactive USSD tester...${NC}"
            python ussd_tester.py
            ;;
        2)
            echo -e "\n${GREEN}Running automated registration flow test...${NC}"
            python run_test_ussd_flow.py
            ;;
        3)
            echo -e "\n${GREEN}Running automated symptom reporting flow test...${NC}"
            python run_test_ussd_flow.py symptom
            ;;
        4)
            echo -e "\n${GREEN}Running automated health information flow test...${NC}"
            python run_test_ussd_flow.py info
            ;;
        5)
            echo -e "\n${GREEN}Starting USSD simulator web interface...${NC}"
            echo -e "${YELLOW}Press Ctrl+C to stop the server when done${NC}"
            python serve_simulator.py --port 8080
            ;;
        6)
            echo -e "\n${BLUE}Thank you for testing Tujali Telehealth!${NC}"
            exit 0
            ;;
        *)
            echo -e "\n${YELLOW}Invalid choice. Please select a number between 1 and 6.${NC}\n"
            ;;
    esac
    
    echo
    echo -e "${BLUE}Press Enter to return to the menu...${NC}"
    read -r
    clear
done
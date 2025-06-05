#!/usr/bin/env python3
"""
USSD Flow Example Tester for Tujali Telehealth

This script demonstrates the key USSD flows in Tujali Telehealth by
running through common user journeys automatically.
"""

import requests
import uuid
import time
import sys

# Base URL for the USSD endpoint
BASE_URL = "http://localhost:5000/ussd"

class USSDSession:
    def __init__(self, phone_number):
        self.session_id = str(uuid.uuid4())
        self.service_code = "*384*4255#"  # Example service code
        self.phone_number = phone_number
        self.text = ""
        
    def send(self, input_text=None):
        """Send a USSD request and return the response"""
        # If input is provided, append it to the text chain
        if input_text is not None:
            if self.text:
                self.text += f"*{input_text}"
            else:
                self.text = input_text
        
        # Prepare the USSD payload
        payload = {
            "sessionId": self.session_id,
            "serviceCode": self.service_code,
            "phoneNumber": self.phone_number,
            "text": self.text
        }
        
        try:
            # Send POST request to the USSD endpoint
            response = requests.post(BASE_URL, data=payload)
            return response.text
        except requests.RequestException as e:
            return f"Error: {str(e)}"
    
    def reset(self):
        """Reset the session (start over)"""
        self.text = ""
        return self.send()


def run_registration_flow():
    """Run through the patient registration flow"""
    print("\n=== Testing Patient Registration Flow ===\n")
    
    # Use a unique phone number for the test
    phone = f"+2547{uuid.uuid4().hex[:8]}"
    session = USSDSession(phone)
    
    # Step 1: Start the session
    print("Step 1: Starting USSD session")
    response = session.send()
    print_response(response)
    time.sleep(1)
    
    # Step 2: Select language (English)
    print("\nStep 2: Selecting English as language")
    response = session.send("1")
    print_response(response)
    time.sleep(1)
    
    # Step 3: Select Registration
    print("\nStep 3: Selecting Registration")
    response = session.send("1")
    print_response(response)
    time.sleep(1)
    
    # Step 4: Enter name
    print("\nStep 4: Entering name 'John Doe'")
    response = session.send("John Doe")
    print_response(response)
    time.sleep(1)
    
    # Step 5: Enter age
    print("\nStep 5: Entering age '35'")
    response = session.send("35")
    print_response(response)
    time.sleep(1)
    
    # Step 6: Select gender
    print("\nStep 6: Selecting gender 'Male'")
    response = session.send("1")
    print_response(response)
    time.sleep(1)
    
    # Step 7: Enter location
    print("\nStep 7: Entering location 'Nairobi'")
    response = session.send("Nairobi")
    print_response(response)
    time.sleep(1)
    
    # Step 8: Return to main menu
    print("\nStep 8: Continuing to main menu")
    response = session.send("0")
    print_response(response)
    
    print("\n=== Registration Flow Complete ===\n")
    return session


def run_symptom_reporting_flow(session):
    """Run through the symptom reporting flow"""
    print("\n=== Testing Symptom Reporting Flow ===\n")
    
    # Step 1: Select Report Symptoms
    print("Step 1: Selecting Report Symptoms")
    response = session.send("1")
    print_response(response)
    time.sleep(1)
    
    # Step 2: Enter symptoms
    print("\nStep 2: Entering symptoms 'Fever and headache'")
    response = session.send("Fever and headache")
    print_response(response)
    time.sleep(1)
    
    # Step 3: Select duration
    print("\nStep 3: Selecting duration 'Few days'")
    response = session.send("2")
    print_response(response)
    time.sleep(1)
    
    # Step 4: Select severity
    print("\nStep 4: Selecting severity 'Moderate'")
    response = session.send("2")
    print_response(response)
    time.sleep(1)
    
    # Step 5: Return to main menu
    print("\nStep 5: Return to main menu")
    response = session.send("0")
    print_response(response)
    
    print("\n=== Symptom Reporting Flow Complete ===\n")


def run_health_info_flow(session):
    """Run through the health information flow"""
    print("\n=== Testing Health Information Flow ===\n")
    
    # Step 1: Select Health Information
    print("Step 1: Selecting Health Information")
    response = session.send("4")
    print_response(response)
    time.sleep(1)
    
    # Step 2: Select COVID-19 Information
    print("\nStep 2: Selecting COVID-19 Information")
    response = session.send("1")
    print_response(response)
    time.sleep(1)
    
    # Step 3: Return to health info menu
    print("\nStep 3: Return to health info menu")
    response = session.send("0")
    print_response(response)
    time.sleep(1)
    
    # Step 4: Return to main menu
    print("\nStep 4: Return to main menu")
    response = session.send("0")
    print_response(response)
    
    print("\n=== Health Information Flow Complete ===\n")


def print_response(response):
    """Print USSD response with formatting"""
    print("USSD Response:")
    print("-" * 40)
    print(response)
    print("-" * 40)


if __name__ == "__main__":
    print("=== Tujali Telehealth USSD Flow Tester ===")
    
    # Reduce the delay between steps to make the test run faster
    time.sleep = lambda x: None
    
    try:
        # Run the registration flow only as a quick test
        session = run_registration_flow()
        
        print("\nRegistration test flow completed successfully!")
        print("To run additional flows, use the following commands:")
        print("- python run_test_ussd_flow.py symptom   # Test symptom reporting")
        print("- python run_test_ussd_flow.py info      # Test health information")
        
        # Check if additional flow was requested via command line
        if len(sys.argv) > 1:
            if sys.argv[1].lower() == 'symptom':
                run_symptom_reporting_flow(session)
                print("\nSymptom reporting flow completed successfully!")
            elif sys.argv[1].lower() == 'info':
                run_health_info_flow(session)
                print("\nHealth information flow completed successfully!")
        
    except requests.RequestException as e:
        print(f"\nError connecting to the server: {e}")
        print("Make sure the Tujali Telehealth server is running.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
#!/usr/bin/env python3
"""
USSD Tester - A simple interface to test the Tujali Telehealth USSD flow

This script simulates USSD sessions to test the Tujali Telehealth system
without needing an actual USSD gateway or mobile device.
"""

import requests
import uuid
import os
import sys

# Base URL for the USSD endpoint
BASE_URL = "http://localhost:5000/ussd"

# Default test phone number
DEFAULT_PHONE = "+254712345678"

class USSDSession:
    def __init__(self, phone_number=DEFAULT_PHONE):
        self.session_id = str(uuid.uuid4())
        self.service_code = "*384*4255#"  # Example service code
        self.phone_number = phone_number
        self.text = ""
        self.history = []
        
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
            response_text = response.text
            
            # Store the request and response in history
            self.history.append({
                "request": payload,
                "response": response_text
            })
            
            return response_text
        except requests.RequestException as e:
            return f"Error: {str(e)}"
    
    def reset(self):
        """Reset the session (start over)"""
        self.text = ""
        return self.send()
    
    def show_history(self):
        """Display the session history"""
        print("\n=== USSD Session History ===")
        for i, entry in enumerate(self.history, 1):
            print(f"\nStep {i}:")
            print(f"Request: {entry['request']['text']}")
            print(f"Response:\n{entry['response']}")
        print("\n============================")


def interactive_session():
    """Run an interactive USSD testing session"""
    print("=== Tujali Telehealth USSD Tester ===")
    phone = input(f"Enter phone number (or press Enter for default {DEFAULT_PHONE}): ")
    if not phone:
        phone = DEFAULT_PHONE
    
    # Initialize the session
    session = USSDSession(phone)
    
    # Start the session
    response = session.send()
    print("\nUSSD Response:")
    print(response)
    
    while True:
        print("\nOptions:")
        print("1-9: Send selection")
        print("t: Enter text input")
        print("r: Reset session")
        print("h: Show history")
        print("q: Quit")
        
        choice = input("\nEnter your choice: ").strip().lower()
        
        if choice == 'q':
            print("Exiting USSD tester.")
            break
        elif choice == 'r':
            response = session.reset()
            print("\nSession reset. USSD Response:")
            print(response)
        elif choice == 'h':
            session.show_history()
        elif choice == 't':
            text_input = input("Enter text: ")
            response = session.send(text_input)
            print("\nUSSD Response:")
            print(response)
        elif choice.isdigit() and 1 <= int(choice) <= 9:
            response = session.send(choice)
            print("\nUSSD Response:")
            print(response)
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    interactive_session()
# Tujali Telehealth USSD Testing Tools

This document describes the USSD testing tools available for the Tujali Telehealth system.

## Overview

Tujali Telehealth provides a USSD-based interface that allows patients in rural areas to access healthcare services using basic mobile phones without requiring internet connectivity or smartphones. The testing tools in this directory help you simulate and test the USSD flows.

## Available Testing Tools

### 1. Interactive USSD Tester (`ussd_tester.py`)

This tool provides an interactive command-line interface to simulate USSD sessions with the Tujali Telehealth system.

**Usage:**
```bash
python ussd_tester.py
```

**Features:**
- Enter custom phone numbers for testing
- Navigate USSD menus interactively
- Reset sessions
- View session history

### 2. Automated USSD Flow Tester (`run_test_ussd_flow.py`)

This tool automatically runs through predefined USSD flows to demonstrate key user journeys in the Tujali Telehealth system.

**Usage:**
```bash
# Run registration flow only
python run_test_ussd_flow.py

# Run registration and symptom reporting flows
python run_test_ussd_flow.py symptom

# Run registration and health information flows
python run_test_ussd_flow.py info
```

**Key Flows:**
- Patient registration
- Symptom reporting
- Health information access

### 3. USSD Simulator Web Interface (`serve_simulator.py` and `ussd_simulator.html`)

This tool provides a visual web-based interface that simulates how USSD looks on a basic mobile phone, allowing for a more realistic testing experience.

**Usage:**
```bash
python serve_simulator.py --port 8080
```

Then open your browser to http://localhost:8080/ussd_simulator.html

**Features:**
- Visual representation of a basic mobile phone display
- Simulated keypad input
- Session history tracking
- Custom phone number input

## Testing Tips

1. **Testing Registration:**
   The first step for most testing is registering a patient. Use different phone numbers to create multiple patient profiles.

2. **Testing Multilingual Support:**
   Select different languages at the start of a session to verify multilingual support.

3. **Testing Error Handling:**
   Intentionally provide invalid inputs (like letters when numbers are expected) to test error handling.

4. **Testing Session Persistence:**
   Use the same session ID across multiple requests to verify that session state is maintained correctly.

## USSD Protocol Details

The USSD protocol used by Tujali Telehealth follows the Africa's Talking USSD API format:

- Each request contains: `sessionId`, `serviceCode`, `phoneNumber`, and `text`
- Responses are prefixed with either `CON` (continues the session) or `END` (ends the session)
- Menu navigation uses the `*` character as a delimiter between inputs

Example USSD code to dial: `*384*4255#`
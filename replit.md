# Tujali Telehealth System

## Overview
Tujali is a comprehensive healthcare solution using USSD technology to provide medical consultations to populations across Africa, initially focused on rural Kenya. The system addresses connectivity challenges where over 60% of Africans lack reliable internet access and nearly 40% don't own smartphones.

## Architecture
- **Flask Web Dashboard**: Healthcare provider interface with role-based access control
- **Python USSD System**: Existing patient consultation interface via Africa's Talking
- **Node.js USSD System** (NEW): Enhanced geo-location services for doctor discovery and appointment booking
- **PostgreSQL Database**: Centralized data storage with shared schema

## Recent Changes
- 2025-06-25: Enhanced department system with specialized healthcare roles (finance, lab, clinical, pharmacy, nursing)
- 2025-06-25: Integrated USSD-specific metrics across all department dashboards
- 2025-06-25: Created comprehensive pharmacy dashboard with drug inventory management
- 2025-06-25: **COMPLETED** Node.js USSD system with geo-location services for doctor discovery
- 2025-06-25: Implemented doctor booking system for physical visits and teleconsultations
- 2025-06-25: Added geo-location API with distance-based doctor sorting
- 2025-06-25: Created complete USSD flow with multi-language support

## User Preferences
- Focus on practical healthcare workflows for African rural settings
- Prioritize USSD accessibility over web interfaces for patient interactions
- Implement real-world medical department operations and metrics
- Use professional healthcare terminology and practices

## Department Credentials
- **Super Admin**: admin/admin123
- **Finance Manager**: finance_manager/finance123
- **Lab Supervisor**: lab_supervisor/lab123
- **Chief Medical Officer**: chief_medical/clinical123
- **Charge Nurse**: charge_nurse/nurse123
- **Pharmacy Manager**: pharmacy_head/pharmacy123

## Node.js USSD System (COMPLETED)
- **Geo-location Services**: Find doctors within specified radius using city names, landmarks, or GPS coordinates
- **Doctor Discovery**: Display doctor information including location, contact, specialty, fees, and distance
- **Appointment Booking**: Complete booking system for both physical visits and teleconsultations
- **USSD Flow**: *384*4040# access code with intuitive menu navigation
- **Multi-language Support**: English, Swahili, and other local languages
- **Emergency Services**: Quick access to emergency contact information
- **Integration**: Seamlessly works with existing Flask dashboard and shared database
- **API Endpoints**: RESTful APIs for geo-location, doctor search, and appointment management
- **Session Management**: Robust USSD session handling with fallback mechanisms
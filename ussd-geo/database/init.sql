-- Database initialization for USSD Geo Service
-- This extends the existing database schema with additional tables for USSD sessions and enhanced functionality

-- USSD Session Tracking
CREATE TABLE IF NOT EXISTS ussd_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    service_code VARCHAR(50),
    input_text TEXT,
    response_text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_phone_number (phone_number),
    INDEX idx_timestamp (timestamp)
);

-- Patient Symptoms Tracking
CREATE TABLE IF NOT EXISTS patient_symptoms (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    symptoms TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'mild',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patient_id (patient_id),
    INDEX idx_reported_at (reported_at)
);

-- Notifications Log
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    recipient_id INTEGER NOT NULL,
    recipient_type VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    INDEX idx_recipient (recipient_id, recipient_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Enhanced Provider table columns (add if not exists)
ALTER TABLE providers ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8);
ALTER TABLE providers ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8);
ALTER TABLE providers ADD COLUMN IF NOT EXISTS hospital VARCHAR(255);
ALTER TABLE providers ADD COLUMN IF NOT EXISTS languages VARCHAR(255) DEFAULT 'English, Swahili';
ALTER TABLE providers ADD COLUMN IF NOT EXISTS rating DECIMAL(3, 2) DEFAULT 4.5;
ALTER TABLE providers ADD COLUMN IF NOT EXISTS available_days VARCHAR(255) DEFAULT 'Monday,Tuesday,Wednesday,Thursday,Friday';
ALTER TABLE providers ADD COLUMN IF NOT EXISTS available_hours VARCHAR(50) DEFAULT '09:00-17:00';
ALTER TABLE providers ADD COLUMN IF NOT EXISTS consultation_fee INTEGER DEFAULT 1500;
ALTER TABLE providers ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true;

-- Enhanced Appointments table columns
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'web';
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS appointment_type VARCHAR(20) DEFAULT 'physical';
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS diagnosis TEXT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS treatment TEXT;

-- Enhanced Patients table columns
ALTER TABLE patients ADD COLUMN IF NOT EXISTS emergency_contact VARCHAR(255);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS medical_history TEXT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS allergies TEXT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';

-- Geo Search Log
CREATE TABLE IF NOT EXISTS geo_searches (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    location_input VARCHAR(255) NOT NULL,
    parsed_coordinates JSON,
    results_count INTEGER DEFAULT 0,
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone_number (phone_number),
    INDEX idx_search_timestamp (search_timestamp)
);

-- Doctor Availability Slots (optional - for more detailed scheduling)
CREATE TABLE IF NOT EXISTS doctor_availability (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES providers(id),
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_available BOOLEAN DEFAULT true,
    slot_type VARCHAR(20) DEFAULT 'consultation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_slot (provider_id, date, start_time),
    INDEX idx_provider_date (provider_id, date),
    INDEX idx_availability (is_available)
);

-- Sample data for testing (only insert if tables are empty)
INSERT INTO providers (
    username, full_name, email, password_hash, role, specialization, 
    phone_number, location, years_experience, consultation_fee,
    latitude, longitude, hospital, languages, rating,
    available_days, available_hours, active, created_at
) VALUES 
(
    'dr_wanjiku', 'Dr. Sarah Wanjiku', 'sarah.wanjiku@tujali.health', 
    'hashed_password_123', 'provider', 'General Practitioner',
    '+254712345678', 'Nairobi, Westlands', 8, 1500,
    -1.2630, 36.8063, 'Westlands Medical Center', 'English, Swahili, Kikuyu', 4.8,
    'Monday,Tuesday,Wednesday,Thursday,Friday', '09:00-17:00', true, NOW()
),
(
    'dr_kipchoge', 'Dr. James Kipchoge', 'james.kipchoge@tujali.health',
    'hashed_password_124', 'provider', 'Pediatrician',
    '+254723456789', 'Nairobi, Karen', 12, 2000,
    -1.3197, 36.6859, 'Karen Hospital', 'English, Swahili, Kalenjin', 4.9,
    'Monday,Tuesday,Wednesday,Thursday,Friday', '08:00-16:00', true, NOW()
),
(
    'dr_akinyi', 'Dr. Grace Akinyi', 'grace.akinyi@tujali.health',
    'hashed_password_125', 'provider', 'Gynecologist',
    '+254734567890', 'Nairobi, Kilimani', 15, 2500,
    -1.2884, 36.7780, 'Aga Khan Hospital', 'English, Swahili, Luo', 4.7,
    'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday', '09:00-18:00', true, NOW()
),
(
    'dr_mutua', 'Dr. David Mutua', 'david.mutua@tujali.health',
    'hashed_password_126', 'provider', 'Cardiologist',
    '+254745678901', 'Nairobi, Upper Hill', 20, 3000,
    -1.2841, 36.8155, 'Nairobi Hospital', 'English, Swahili, Kamba', 4.9,
    'Monday,Tuesday,Wednesday,Thursday,Friday', '10:00-16:00', true, NOW()
),
(
    'dr_chebet', 'Dr. Mary Chebet', 'mary.chebet@tujali.health',
    'hashed_password_127', 'provider', 'Dermatologist',
    '+254756789012', 'Nairobi, Parklands', 10, 1800,
    -1.2637, 36.8084, 'MP Shah Hospital', 'English, Swahili, Kalenjin', 4.6,
    'Tuesday,Wednesday,Thursday,Friday,Saturday', '09:00-17:00', true, NOW()
)
ON CONFLICT (username) DO NOTHING;

-- Add sample patients for testing
INSERT INTO patients (
    name, phone_number, age, gender, location, language, created_at
) VALUES 
('John Kamau', '+254701234567', 35, 'Male', 'Nairobi, Kasarani', 'en', NOW()),
('Mary Wanjiru', '+254712345678', 28, 'Female', 'Nairobi, Embakasi', 'sw', NOW()),
('Peter Ochieng', '+254723456789', 42, 'Male', 'Kisumu, Kondele', 'en', NOW()),
('Jane Muthoni', '+254734567890', 31, 'Female', 'Nakuru, Pipeline', 'en', NOW()),
('Samuel Kiplagat', '+254745678901', 25, 'Male', 'Eldoret, Langas', 'en', NOW())
ON CONFLICT (phone_number) DO NOTHING;
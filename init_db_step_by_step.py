import os
from app import app, db_ext
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from sqlalchemy import text

def create_tables():
    with app.app_context():
        try:
            # Drop all tables if they exist (in reverse order due to foreign key constraints)
            db_ext.session.execute(text("""
                DROP TABLE IF EXISTS payment_refunds;
                DROP TABLE IF EXISTS payments;
                DROP TABLE IF EXISTS prescriptions;
                DROP TABLE IF EXISTS lab_results;
                DROP TABLE IF EXISTS user_interactions;
                DROP TABLE IF EXISTS messages;
                DROP TABLE IF EXISTS appointments;
                DROP TABLE IF EXISTS providers;
                DROP TABLE IF EXISTS patients;
                DROP TABLE IF EXISTS health_info_articles;
                DROP TABLE IF EXISTS pharmacies;
                DROP TABLE IF EXISTS users;
            
                -- Users table
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(256),
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Providers table
                CREATE TABLE providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    specialization VARCHAR(100),
                    license_number VARCHAR(50),
                    languages TEXT,
                    location VARCHAR(200),
                    coordinates TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                
                -- Patients table
                CREATE TABLE patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    age INTEGER,
                    gender VARCHAR(20),
                    location VARCHAR(200),
                    coordinates TEXT,
                    language VARCHAR(10) DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Health Info Articles table
                CREATE TABLE health_info_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    category VARCHAR(50),
                    language VARCHAR(20) DEFAULT 'en',
                    is_published BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Pharmacies table
                CREATE TABLE pharmacies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    address VARCHAR(200),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    phone VARCHAR(20),
                    email VARCHAR(120),
                    coordinates TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Appointments table
                CREATE TABLE appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    provider_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    price FLOAT,
                    payment_status VARCHAR(20) DEFAULT 'pending',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reminder_sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY (patient_id) REFERENCES patients (id),
                    FOREIGN KEY (provider_id) REFERENCES providers (id)
                );
                
                -- Prescriptions table
                CREATE TABLE prescriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_id INTEGER NOT NULL,
                    patient_id INTEGER NOT NULL,
                    medication_details TEXT,
                    instructions TEXT,
                    collection_method VARCHAR(20) DEFAULT 'pharmacy_pickup',
                    pharmacy_id INTEGER,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (provider_id) REFERENCES providers (id),
                    FOREIGN KEY (patient_id) REFERENCES patients (id),
                    FOREIGN KEY (pharmacy_id) REFERENCES pharmacies (id)
                );
                
                -- Payments table
                CREATE TABLE payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL,
                    amount FLOAT NOT NULL,
                    phone_number VARCHAR(20),
                    mpesa_reference VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'pending',
                    payment_method VARCHAR(20) DEFAULT 'mpesa',
                    currency VARCHAR(3) DEFAULT 'KES',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    receipt_sent BOOLEAN DEFAULT 0,
                    receipt_sent_at TIMESTAMP,
                    notes TEXT,
                    metadata TEXT,
                    FOREIGN KEY (appointment_id) REFERENCES appointments (id)
                );
                
                -- Payment Refunds table
                CREATE TABLE payment_refunds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id INTEGER NOT NULL,
                    amount FLOAT NOT NULL,
                    reason TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    processed_by INTEGER,
                    reference VARCHAR(50),
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (payment_id) REFERENCES payments (id),
                    FOREIGN KEY (processed_by) REFERENCES users (id)
                );
                
                -- Messages table
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_id INTEGER NOT NULL,
                    patient_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    sender_type VARCHAR(10) NOT NULL,
                    is_read BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (provider_id) REFERENCES providers (id),
                    FOREIGN KEY (patient_id) REFERENCES patients (id)
                );
                
                -- Lab Results table
                CREATE TABLE lab_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    provider_id INTEGER NOT NULL,
                    test_name VARCHAR(200) NOT NULL,
                    test_type VARCHAR(100),
                    fee DECIMAL(10,2) DEFAULT 0.00,
                    fee_paid DECIMAL(10,2) DEFAULT 0.00,
                    is_billed BOOLEAN DEFAULT 0,
                    billing_notes TEXT,
                    test_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    result_date TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'pending',
                    notes TEXT,
                    results TEXT,
                    reference_range TEXT,
                    is_abnormal BOOLEAN DEFAULT 0,
                    is_urgent BOOLEAN DEFAULT 0,
                    urgency VARCHAR(20) DEFAULT 'routine',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id),
                    FOREIGN KEY (provider_id) REFERENCES providers (id)
                );
                
                -- User Interactions table
                CREATE TABLE user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    interaction_type VARCHAR(50) NOT NULL,
                    description VARCHAR(255),
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id)
                );
                
                -- Create indexes
                CREATE INDEX idx_appointments_patient_id ON appointments (patient_id);
                CREATE INDEX idx_appointments_provider_id ON appointments (provider_id);
                CREATE INDEX idx_messages_patient_id ON messages (patient_id);
                CREATE INDEX idx_messages_provider_id ON messages (provider_id);
                CREATE INDEX idx_prescriptions_patient_id ON prescriptions (patient_id);
                CREATE INDEX idx_prescriptions_provider_id ON prescriptions (provider_id);
                CREATE INDEX idx_lab_results_patient_id ON lab_results (patient_id);
                CREATE INDEX idx_lab_results_provider_id ON lab_results (provider_id);
                CREATE INDEX idx_user_interactions_patient_id ON user_interactions (patient_id);
            """))
            
            db_ext.session.commit()
            print("Tables created successfully!")
            return True
            
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            db_ext.session.rollback()
            return False

def create_admin_user():
    with app.app_context():
        try:
            # Create admin user
            db_ext.session.execute(
                text("""
                INSERT INTO users (username, email, password_hash, is_admin, created_at)
                VALUES (:username, :email, :password_hash, :is_admin, :created_at)
                """),
                {
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'password_hash': generate_password_hash('admin123'),
                    'is_admin': 1,
                    'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                }
            )
            
            # Get the admin user ID
            result = db_ext.session.execute(
                text("SELECT last_insert_rowid()")
            ).fetchone()
            user_id = result[0] if result else None
            
            if not user_id:
                raise Exception("Failed to get the ID of the newly created admin user")
            
            # Create provider entry for admin
            db_ext.session.execute(
                text("""
                INSERT INTO providers (user_id, name, specialization, license_number, languages, location, created_at)
                VALUES (:user_id, :name, :specialization, :license_number, :languages, :location, :created_at)
                """),
                {
                    'user_id': user_id,
                    'name': 'System Administrator',
                    'specialization': 'System Admin',
                    'license_number': 'ADMIN-001',
                    'languages': 'en',
                    'location': 'Nairobi',
                    'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                }
            )
            
            db_ext.session.commit()
            print("\nAdmin user created successfully!")
            print("  Username: admin")
            print("  Password: admin123")
            return True
            
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")
            db_ext.session.rollback()
            return False

def init_database():
    # Delete the existing database file if it exists
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except Exception as e:
            print(f"Warning: Could not remove existing database: {str(e)}")
    
    # Create tables
    if not create_tables():
        print("Failed to create tables. Aborting.")
        return False
    
    # Create admin user
    if not create_admin_user():
        print("Failed to create admin user.")
        return False
    
    print("\nDatabase initialization completed successfully!")
    return True

if __name__ == '__main__':
    init_database()

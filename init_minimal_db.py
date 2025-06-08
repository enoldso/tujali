import os
from app import app, db_ext
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from sqlalchemy import text

def init_minimal_db():
    with app.app_context():
        try:
            # Drop all tables if they exist
            db_ext.session.execute(text("""
                DROP TABLE IF EXISTS users;
                DROP TABLE IF EXISTS providers;
            
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
            
                -- Create admin user
                INSERT INTO users (username, email, password_hash, is_admin, created_at)
                VALUES (
                    'admin',
                    'admin@example.com',
                    :password_hash,
                    1,
                    :created_at
                );
            
                -- Get the admin user ID and create provider entry
                INSERT INTO providers (user_id, name, specialization, license_number, languages, location, created_at)
                VALUES (
                    last_insert_rowid(),
                    'System Administrator',
                    'System Admin',
                    'ADMIN-001',
                    'en',
                    'Nairobi',
                    :created_at
                );
            """), {
                'password_hash': generate_password_hash('admin123'),
                'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            })
            
            db_ext.session.commit()
            print("\nMinimal database initialized successfully!")
            print("Admin user created:")
            print("  Username: admin")
            print("  Password: admin123")
            return True
            
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            db_ext.session.rollback()
            return False

if __name__ == '__main__':
    # Delete the existing database file if it exists
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except Exception as e:
            print(f"Warning: Could not remove existing database: {str(e)}")
    
    # Initialize the minimal database
    if init_minimal_db():
        print("\nYou can now start the application with the admin user.")
    else:
        print("\nFailed to initialize the database. Please check the error messages above.")

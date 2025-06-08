import os
from app import app, db_ext
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from sqlalchemy import text

def execute_sql(statements):
    """Execute a list of SQL statements"""
    with app.app_context():
        try:
            for stmt in statements:
                db_ext.session.execute(text(stmt))
            db_ext.session.commit()
            return True
        except Exception as e:
            print(f"Error executing SQL: {str(e)}")
            print(f"Statement: {stmt}")
            db_ext.session.rollback()
            return False

def init_db():
    # Drop existing tables if they exist
    drop_statements = [
        "DROP TABLE IF EXISTS providers;",
        "DROP TABLE IF EXISTS users;"
    ]
    
    # Create tables
    create_statements = [
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(256),
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
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
        """
    ]
    
    # Create admin user
    admin_password_hash = generate_password_hash('admin123')
    create_admin = f"""
    INSERT INTO users (username, email, password_hash, is_admin, created_at)
    VALUES (
        'admin',
        'admin@example.com',
        '{admin_password_hash}',
        1,
        '{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}'
    );
    """
    
    # Create provider for admin
    create_admin_provider = f"""
    INSERT INTO providers (user_id, name, specialization, license_number, languages, location, created_at)
    VALUES (
        (SELECT id FROM users WHERE username = 'admin'),
        'System Administrator',
        'System Admin',
        'ADMIN-001',
        'en',
        'Nairobi',
        '{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}'
    );
    """
    
    # Delete the existing database file if it exists
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except Exception as e:
            print(f"Warning: Could not remove existing database: {str(e)}")
    
    # Execute all statements
    print("Initializing database...")
    
    # Drop tables
    print("Dropping existing tables...")
    if not execute_sql(drop_statements):
        return False
    
    # Create tables
    print("Creating tables...")
    if not execute_sql(create_statements):
        return False
    
    # Create admin user
    print("Creating admin user...")
    if not execute_sql([create_admin]):
        return False
    
    # Create admin provider
    print("Creating admin provider...")
    if not execute_sql([create_admin_provider]):
        return False
    
    print("\nDatabase initialized successfully!")
    print("Admin user created:")
    print("  Username: admin")
    print("  Password: admin123")
    return True

if __name__ == '__main__':
    if init_db():
        print("\nYou can now start the application with the admin user.")
    else:
        print("\nFailed to initialize the database. Please check the error messages above.")

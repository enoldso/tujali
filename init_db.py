from app import app, db_ext
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from sqlalchemy import text
import os

def init_database():
    with app.app_context():
        try:
            # Drop all tables if they exist
            db_ext.drop_all()
            print("Dropped all tables")
            
            # Create all tables
            db_ext.create_all()
            print("Created all tables")
            
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
            print("Username: admin")
            print("Password: admin123")
            
            # Verify the admin user was created
            admin = db_ext.session.execute(
                text("SELECT id, username, email, is_admin FROM users WHERE username = :username"),
                {'username': 'admin'}
            ).fetchone()
            
            if admin:
                print("\nVerification:")
                print(f"ID: {admin[0]}")
                print(f"Username: {admin[1]}")
                print(f"Email: {admin[2]}")
                print(f"Is Admin: {bool(admin[3])}")
            
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            db_ext.session.rollback()
            raise

if __name__ == '__main__':
    # Delete the existing database file if it exists
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except Exception as e:
            print(f"Warning: Could not remove existing database: {str(e)}")
    
    # Initialize the database
    init_database()

from app import app, db_ext
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from sqlalchemy import text

def add_admin_user():
    with app.app_context():
        try:
            # Check if admin user already exists
            result = db_ext.session.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {'username': 'admin'}
            ).fetchone()
            
            if result:
                print("Admin user already exists!")
                return
            
            # Insert admin user
            db_ext.session.execute(
                text("""
                INSERT INTO users (username, email, password_hash, is_admin, created_at)
                VALUES (:username, :email, :password_hash, :is_admin, :created_at)
                """),
                {
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'password_hash': generate_password_hash('admin123'),
                    'is_admin': 1,  # SQLite uses 1 for true
                    'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                }
            )
            
            # Get the user ID of the newly created admin
            result = db_ext.session.execute(
                text("SELECT last_insert_rowid()")
            ).fetchone()
            user_id = result[0] if result else None
            
            if not user_id:
                raise Exception("Failed to get the ID of the newly created user")
            
            # Insert provider entry for the admin
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
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
            
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")
            db_ext.session.rollback()
            raise

if __name__ == '__main__':
    add_admin_user()

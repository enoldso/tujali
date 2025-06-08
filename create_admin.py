from app import app, db_ext
from models_sqlalchemy import User, Provider
from werkzeug.security import generate_password_hash

def create_admin():
    # Create an application context
    with app.app_context():
        try:
            # Check if admin user already exists
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print("Admin user already exists!")
                return
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123')  # Set the password directly
            )
            
            # Add to session and commit
            db_ext.session.add(admin)
            db_ext.session.commit()
            
            # Create a provider entry for the admin
            provider = Provider(
                user_id=admin.id,
                name='System Administrator',
                specialization='System Admin',
                license_number='ADMIN-001',
                languages=['en'],
                location='Nairobi'
            )
            db_ext.session.add(provider)
            db_ext.session.commit()
            
            print("Admin user created successfully!")
            print(f"Username: admin")
            print(f"Password: admin123")
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")
            db_ext.session.rollback()
            raise

if __name__ == '__main__':
    create_admin()

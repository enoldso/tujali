from app import app, db_ext
from models_sqlalchemy import User
from werkzeug.security import generate_password_hash

def reset_admin_password():
    with app.app_context():
        try:
            # Find the admin user
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("Admin user not found!")
                return
            
            # Set a new password
            new_password = 'admin123'  # You can change this to your preferred password
            admin.password_hash = generate_password_hash(new_password)
            
            # Save changes
            db_ext.session.commit()
            
            print("Admin password has been reset successfully!")
            print(f"Username: admin")
            print(f"New password: {new_password}")
            
        except Exception as e:
            print(f"Error resetting admin password: {str(e)}")
            db_ext.session.rollback()
            raise

if __name__ == '__main__':
    reset_admin_password()

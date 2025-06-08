from app import app, db_ext
from sqlalchemy import text

def check_admin_user():
    with app.app_context():
        try:
            # Check if admin user exists
            result = db_ext.session.execute(
                text("SELECT id, username, email, is_admin FROM users WHERE username = :username"),
                {'username': 'admin'}
            ).fetchone()
            
            if result:
                print("Admin user found!")
                print(f"ID: {result[0]}")
                print(f"Username: {result[1]}")
                print(f"Email: {result[2]}")
                print(f"Is Admin: {bool(result[3])}")
            else:
                print("Admin user not found!")
                
            # List all users
            print("\nAll users in the database:")
            users = db_ext.session.execute(
                text("SELECT id, username, email, is_admin FROM users")
            ).fetchall()
            
            for user in users:
                print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Is Admin: {bool(user[3])}")
                
        except Exception as e:
            print(f"Error checking admin user: {str(e)}")

if __name__ == '__main__':
    check_admin_user()

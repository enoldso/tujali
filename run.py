from app import app, db_ext
from models_sqlalchemy import *
from extensions import migrate

def init_db():
    with app.app_context():
        # Create all database tables
        print("Creating database tables...")
        db_ext.create_all()
        print("Database tables created.")
        
        # Create admin user if it doesn't exist
        if User.query.count() == 0:
            print("Creating initial admin user...")
            admin_user = User(
                username='admin',
                email='admin@example.com'
            )
            admin_user.set_password('admin123')
            db_ext.session.add(admin_user)
            
            # Create a sample provider
            provider = Provider(
                user=admin_user,
                name='Dr. Admin User',
                specialization='General Practitioner',
                license_number='MD12345',
                languages=['en', 'sw'],
                location='Nairobi, Kenya'
            )
            db_ext.session.add(provider)
            db_ext.session.commit()
            print("Created initial admin user and provider")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    # Run the Flask app
    print("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=True)

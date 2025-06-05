"""
Script to reset the database by dropping and recreating all tables.
Run this script to apply schema changes.
"""
from sqlalchemy import text
from app import app, db_ext
from models_sqlalchemy import *

def reset_database():
    with app.app_context():
        print("Dropping all database tables...")
        # First, drop all tables with CASCADE to handle foreign key constraints
        tables = [
            'health_info', 'health_info_articles', 'messages', 'payments',
            'prescriptions', 'appointments', 'pharmacies', 'providers',
            'patients', 'users'
        ]
        for table in tables:
            db_ext.session.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
        db_ext.session.commit()
        print("All tables dropped.")
        
        print("Creating all database tables...")
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
    reset_database()

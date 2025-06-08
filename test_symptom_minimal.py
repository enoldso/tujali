import unittest
from flask import Flask, url_for
from flask_testing import TestCase
from flask_login import LoginManager, current_user, login_user, logout_user
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import the app and db from app.py
from app import app, db
from models_sqlalchemy import User, Provider, Patient, HealthInfo, UserInteraction

class TestSymptomDashboardMinimal(TestCase):
    """Minimal test case for the symptom dashboard"""
    
    def create_app(self):
        """Create and configure the app for testing"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['LOGIN_DISABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['DEBUG'] = True
        app.config['PROPAGATE_EXCEPTIONS'] = True
        
        return app
    
    def setUp(self):
        """Set up test data"""
        # Create all tables
        db.create_all()
        
        # Create a test user
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            is_active=True
        )
        self.test_user.set_password('testpass')
        db.session.add(self.test_user)
        
        # Commit the user first to get an ID
        db.session.commit()
        
        # Create a test provider linked to the user
        self.test_provider = Provider(
            user_id=self.test_user.id,
            name='Test Provider',
            specialization='General Practitioner',
            license_number='TEST123',
            languages='English,Swahili',
            location='Test Location'
        )
        db.session.add(self.test_provider)
        
        # Set the user's provider_id
        self.test_user.provider_id = self.test_provider.id
        
        # Create a test patient
        self.test_patient = Patient(
            phone_number='+254700000000',
            name='Test Patient',
            age=30,
            gender='Male',
            location='Test Location'
        )
        db.session.add(self.test_patient)
        
        # Create a test health info record with symptom data
        self.test_symptom = HealthInfo(
            title='Symptom Report - Headache',
            content='Headache\nSeverity: High\nLocation: Head\nDuration: 2 days',
            category='symptom',
            is_published=True
        )
        db.session.add(self.test_symptom)
        
        # Create a UserInteraction to track the symptom report
        self.test_interaction = UserInteraction(
            patient_id=self.test_patient.id,
            interaction_type='symptom_report',
            description='Patient reported symptoms',
            interaction_metadata={
                'symptoms': [
                    {
                        'name': 'Headache',
                        'severity': 'High',
                        'category': 'neurological',
                        'description': 'Severe headache lasting 2 days',
                        'started': '2023-01-01',
                        'notes': 'Patient reports sensitivity to light'
                    }
                ]
            }
        )
        db.session.add(self.test_interaction)
        
        # Commit all changes
        db.session.commit()
    
    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
    
    def login(self, username='testuser', password='testpass'):
        """Helper method to log in a test user"""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def test_symptom_dashboard_loads(self):
        """Test that the symptom dashboard loads for authenticated users"""
        # Log in
        self.login()
        
        # Access the dashboard
        response = self.client.get('/symptom-dashboard')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Symptom Visualization Dashboard', response.data)

if __name__ == '__main__':
    unittest.main()

import unittest
import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# SQLAlchemy imports
from sqlalchemy import event, types, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

# Flask imports
from flask import url_for, template_rendered, session, get_flashed_messages
from flask_login import current_user, login_user, logout_user
from contextlib import contextmanager

# Test client
from flask_testing import TestCase

# Import the Flask app and database
from app import app, db
from models_sqlalchemy import User, Provider, Patient, UserInteraction, HealthInfo

# Test configuration
TEST_CONFIG = {
    'TESTING': True,
    'WTF_CSRF_ENABLED': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SECRET_KEY': 'dev-key-for-testing',
    'LOGIN_DISABLED': False,
    'DEBUG': True,
    'PROPAGATE_EXCEPTIONS': True
}

# Patch database types for SQLite
@compiles(types.ARRAY, 'sqlite')
def compile_array(element, compiler, **kw):
    return "TEXT"

@compiles(types.JSON, 'sqlite')
def compile_json(element, compiler, **kw):
    return "TEXT"

@compiles(JSONB, 'sqlite')
def compile_jsonb(element, compiler, **kw):
    return "TEXT"

class TestSymptomDashboard(TestCase):
    """Test suite for the Symptom Dashboard functionality."""
    
    def create_app(self):
        """Create and configure the test app."""
        app.config.update(TEST_CONFIG)
        return app
    
    def setUp(self):
        """Set up test data before each test."""
        with app.app_context():
            try:
                # Create all tables
                db.create_all()
                
                # Create test user and provider
                self.test_user = User(
                    username='testuser',
                    email='test@example.com',
                    role='provider'
                )
                self.test_user.set_password('testpass')
                db.session.add(self.test_user)
                
                self.test_provider = Provider(
                    user_id=self.test_user.id,
                    name='Test Provider',
                    specialization='General Practitioner',
                    license_number='TEST123'
                )
                db.session.add(self.test_provider)
                
                # Create test patient
                self.test_patient = Patient(
                    phone_number='+254700000000',
                    name='Test Patient',
                    age=30,
                    gender='Male',
                    location='Nairobi, Kenya',
                    coordinates=json.dumps({'lat': -1.286389, 'lng': 36.817223})
                )
                db.session.add(self.test_patient)
                
                # Create test symptom interaction
                self.test_symptom = UserInteraction(
                    patient_id=self.test_patient.id,
                    interaction_type='symptom_report',
                    description='Patient reported symptoms',
                    interaction_metadata={
                        'symptoms': [{
                            'name': 'Headache',
                            'severity': 'moderate',
                            'duration': '2 days',
                            'notes': 'Persistent headache',
                            'category': 'neurological'
                        }],
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                db.session.add(self.test_symptom)
                
                db.session.commit()
                logger.info("Test data created successfully")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error setting up test data: {str(e)}")
                raise
    
    def tearDown(self):
        """Clean up after each test."""
        with app.app_context():
            try:
                db.session.remove()
                db.drop_all()
                logger.info("Test database cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up test database: {str(e)}")
    
    def login(self, username='testuser', password='testpass'):
        """Helper method to log in a test user."""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def test_requires_login(self):
        """Test that the symptom dashboard requires login."""
        response = self.client.get('/symptom-dashboard', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)
    
    def test_dashboard_loads(self):
        """Test that the symptom dashboard loads for authenticated users."""
        self.login()
        response = self.client.get('/symptom-dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Symptom Dashboard', response.data)
    
    def test_shows_symptom_data(self):
        """Test that the dashboard displays symptom data."""
        self.login()
        response = self.client.get('/symptom-dashboard')
        self.assertIn(b'Headache', response.data)
        self.assertIn(b'moderate', response.data)
    
    def test_filter_by_severity(self):
        """Test filtering symptoms by severity."""
        self.login()
        response = self.client.get('/symptom-dashboard?severity=moderate')
        self.assertIn(b'Headache', response.data)
        
        response = self.client.get('/symptom-dashboard?severity=severe')
        self.assertNotIn(b'Headache', response.data)
    
    def test_search_functionality(self):
        """Test searching for symptoms."""
        self.login()
        response = self.client.get('/symptom-dashboard?search=head')
        self.assertIn(b'Headache', response.data)
        
        response = self.client.get('/symptom-dashboard?search=nonexistent')
        self.assertNotIn(b'Headache', response.data)

if __name__ == '__main__':
    unittest.main()

import unittest
import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Configure logging before any other imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# SQLAlchemy imports
from sqlalchemy import event, types, String, inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

# Flask imports
from flask import url_for, template_rendered, session
from flask_login import current_user, login_user, logout_user
from contextlib import contextmanager

# Test client
from flask_testing import TestCase

# Import the Flask app and database
from app import app, db
from models_sqlalchemy import User, Provider, Patient, UserInteraction, HealthInfo

# Set up test configuration
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

# Patch ARRAY type for SQLite
@compiles(types.ARRAY, 'sqlite')
def compile_array(element, compiler, **kw):
    """Convert ARRAY type to TEXT for SQLite"""
    return "TEXT"

# Patch JSON type for SQLite
@compiles(types.JSON, 'sqlite')
def compile_json(element, compiler, **kw):
    """Convert JSON type to TEXT for SQLite"""
    return "TEXT"

# Patch JSONB type for SQLite
@compiles(JSONB, 'sqlite')
def compile_jsonb(element, compiler, **kw):
    """Convert JSONB type to TEXT for SQLite"""
    return "TEXT"

class TestSymptomDashboard(TestCase):
    """Test the symptom dashboard functionality"""
    
    def create_app(self):
        """Create and configure the test app"""
        # Configure the existing app for testing
        app.config.update(TEST_CONFIG)
        
        # Enable SQLAlchemy logging
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        
        return app
    
    @contextmanager
    def captured_templates(self, app):
        """Capture templates used during a request"""
        recorded = []
        
        def record(sender, template, context, **extra):
            recorded.append((template, context))
            
        template_rendered.connect(record, app)
        try:
            yield recorded
        finally:
            template_rendered.disconnect(record, app)
    
    def setUp(self):
        """Set up test data"""
        logger.info("Setting up test environment...")
        
        try:
            # Create app and client
            self.app = self.create_app()
            self.client = self.app.test_client()
            
            # Create application context
            self.app_context = self.app.app_context()
            self.app_context.push()
            
            # Initialize database
            logger.info("Initializing database...")
            
            # Drop all tables first to ensure clean state
            logger.info("Dropping all tables...")
            db.drop_all()
            
            # Create database tables
            logger.info("Creating all database tables...")
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Created tables: {tables}")
            
            # Create test data
            logger.info("Creating test data...")
            self.create_test_data()
            
            # Verify data was created
            patient_count = Patient.query.count()
            user_count = User.query.count()
            interaction_count = UserInteraction.query.count()
            
            logger.info(f"Test data created - Patients: {patient_count}, Users: {user_count}, Interactions: {interaction_count}")
            logger.info("Test setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during test setup: {str(e)}", exc_info=True)
            raise
    
    def create_test_data(self):
        """Create test data in the database"""
        try:
            with self.app.app_context():
                # Create test user with properly hashed password
                logger.info("Creating test user...")
                self.test_user = User(
                    username='testuser',
                    email='test@example.com'
                )
                self.test_user.set_password('testpass')  # This will hash the password
                db.session.add(self.test_user)
                
                # The User model inherits from UserMixin which provides is_active as a property
                # that returns True by default, so we don't need to set it
                
                try:
                    db.session.flush()  # Ensure user ID is generated
                    logger.info(f"Created test user with ID: {self.test_user.id}")
                except Exception as e:
                    logger.error(f"Error creating test user: {str(e)}")
                    raise
                
                # Create test provider
                logger.info("Creating test provider...")
                self.test_provider = Provider(
                    user_id=self.test_user.id,  # Use user_id instead of user
                    name='Test Provider',
                    specialization='General Practitioner',
                    license_number='TEST123'
                )
                db.session.add(self.test_provider)
                
                try:
                    db.session.flush()
                    logger.info(f"Created test provider with ID: {self.test_provider.id}")
                except Exception as e:
                    logger.error(f"Error creating test provider: {str(e)}")
                    raise
                
                # Create test patient
                logger.info("Creating test patient...")
                self.test_patient = Patient(
                    phone_number='+254700000000',
                    name='Test Patient',
                    age=30,
                    gender='Male',
                    location='Nairobi, Kenya',
                    coordinates=json.dumps({'lat': -1.286389, 'lng': 36.817223})
                )
                db.session.add(self.test_patient)
                
                try:
                    db.session.flush()  # Ensure patient ID is generated
                    logger.info(f"Created test patient with ID: {self.test_patient.id}")
                except Exception as e:
                    logger.error(f"Error creating test patient: {str(e)}")
                    raise
                
                # Create test health info records with symptom data
                logger.info("Creating test health info records with symptom data...")
                
                # Create test symptoms in the format expected by the dashboard
                test_symptoms = [
                    {
                        'content': 'Headache\nSeverity: High\nLocation: Head\nDuration: 2 days',
                        'category': 'symptom',
                        'patient_id': self.test_patient.id,
                        'created_at': datetime.utcnow()
                    },
                    {
                        'content': 'Fever\nSeverity: Moderate\nTemperature: 38°C',
                        'category': 'symptom',
                        'patient_id': self.test_patient.id,
                        'created_at': datetime.utcnow() - timedelta(hours=12)
                    }
                ]
                
                # Add symptoms to the database
                for symptom in test_symptoms:
                    health_info = HealthInfo(
                        title=f"Symptom Report - {symptom['content'].split('\n')[0]}",
                        content=symptom['content'],
                        category=symptom['category'],
                        patient_id=symptom['patient_id']
                    )
                    health_info.created_at = symptom['created_at']
                    db.session.add(health_info)
                
                # Also create a UserInteraction for tracking
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
                            },
                            {
                                'name': 'Fever',
                                'severity': 'Moderate',
                                'category': 'fever',
                                'description': 'Mild fever around 38°C',
                                'started': '2023-01-02',
                                'notes': 'Responding to paracetamol'
                            }
                        ]
                    }
                )
                db.session.add(self.test_interaction)
                
                # Commit all changes
                try:
                    db.session.commit()
                    logger.info("Test data created successfully")
                except Exception as e:
                    logger.error(f"Error committing test data: {str(e)}")
                    db.session.rollback()
                    raise
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating test data: {str(e)}", exc_info=True)
            raise
    
    def tearDown(self):
        """Clean up after each test"""
        logger.info("Tearing down test environment...")
        try:
            # Clear database
            db.session.remove()
            db.drop_all()
            
            # Pop application context
            self.app_context.pop()
            
            logger.info("Test teardown completed")
        except Exception as e:
            logger.error(f"Error during teardown: {str(e)}", exc_info=True)
            raise
    
    def login(self, username='testuser', password='testpass'):
        """Helper method to log in a test user"""
        logger.info(f"Attempting to log in user: {username}")
        
        # First, verify the user exists in the database
        with self.app.app_context():
            user = User.query.filter_by(username=username).first()
            if not user:
                logger.error(f"User {username} not found in database")
                return None
            
            logger.info(f"Found user in database: {user.username}, ID: {user.id}, Active: {user.is_active}")
        
        # Use the login route
        logger.info("Sending login request...")
        response = self.client.post('/login', 
            data={
                'username': username,
                'password': password,
                'remember_me': False
            },
            follow_redirects=True,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        logger.info(f"Login response status: {response.status_code}")
        logger.debug(f"Login response data: {response.data.decode('utf-8')}")
        
        # Check if login was successful by looking for a session cookie
        session_cookie = response.headers.get('Set-Cookie', '')
        logger.info(f"Session cookie: {'found' if 'session=' in session_cookie else 'not found'}")
        
        return response
    
    def test_symptom_dashboard_requires_login(self):
        """Test that the symptom dashboard requires login"""
        logger.info("=== Starting test_symptom_dashboard_requires_login ===")
        
        try:
            # Log out any existing user
            logger.info("Logging out any existing user...")
            logout_user()
            
            # Clear any existing session
            with self.client.session_transaction() as sess:
                sess.clear()
            
            # Try to access dashboard without logging in
            logger.info("Attempting to access dashboard without login...")
            response = self.client.get('/symptom-dashboard', follow_redirects=True)
            
            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            logger.debug(f"Response data (first 500 chars): {response.data.decode('utf-8')[:500]}")
            
            # Should redirect to login page
            self.assertEqual(response.status_code, 200, 
                          f"Expected status 200, got {response.status_code}")
            
            # Check if we were redirected to login page
            response_data = response.data.lower()
            self.assertIn(b'login', response_data, 
                         "Should redirect to login page")
            
        except Exception as e:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
            raise
        finally:
            logger.info("=== Completed test_symptom_dashboard_requires_login ===\n")
    
    def test_symptom_dashboard_loads(self):
        """Test that the symptom dashboard loads for authenticated users"""
        logger.info("=== Starting test_symptom_dashboard_loads ===")
        
        try:
            # Log in
            logger.info("Attempting to log in...")
            response = self.login()
            logger.info(f"Login response status: {response.status_code}")
            logger.debug(f"Login response data: {response.data.decode('utf-8')}")
            
            # Verify login was successful
            self.assertEqual(response.status_code, 200, f"Login failed with status {response.status_code}")
            
            # Verify session
            with self.client.session_transaction() as sess:
                logger.info(f"Session data: {dict(sess)}")
                self.assertIn('_user_id', sess, "User ID not in session after login")
            
            # Access the dashboard
            logger.info("Accessing symptom dashboard...")
            with self.captured_templates(self.app) as templates:
                response = self.client.get('/symptom-dashboard')
                logger.info(f"Dashboard response status: {response.status_code}")
                logger.debug(f"Dashboard response data: {response.data.decode('utf-8')}")
                
                # Check response
                self.assertEqual(response.status_code, 200, 
                             f"Failed to load dashboard. Status: {response.status_code}")
                
                # Check template used
                self.assertGreater(len(templates), 0, "No templates were rendered")
                template_names = [t[0].name for t in templates if t[0] is not None]
                logger.info(f"Rendered templates: {template_names}")
                
                # Check if we got redirected to login (which would indicate auth failure)
                if any('login' in name.lower() for name in template_names if name):
                    logger.error("Unexpected redirect to login page. Check authentication.")
                    
                self.assertIn('symptom_dashboard.html', template_names,
                            "symptom_dashboard.html template was not rendered")
                
                # Log the context data if we have templates
                if templates and templates[0][0] is not None:
                    template, context = templates[0]
                    if template is not None:
                        logger.info(f"Template context keys: {list(context.keys())}")
                    else:
                        logger.warning("First template is None in templates list")
                else:
                    logger.warning("No valid templates found in response")
        except Exception as e:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
            raise
        finally:
            logger.info("=== Completed test_symptom_dashboard_loads ===\n")
    
    def test_symptom_dashboard_shows_data(self):
        """Test that the symptom dashboard shows symptom data"""
        logger.info("=== Starting test_symptom_dashboard_shows_data ===")
        
        try:
            # Log in
            logger.info("Logging in...")
            response = self.login()
            self.assertEqual(response.status_code, 200, 
                          f"Login failed with status {response.status_code}")
            
            # Verify session
            with self.client.session_transaction() as sess:
                logger.info(f"Session after login: {dict(sess)}")
                self.assertIn('_user_id', sess, "User ID not in session after login")
            
            # Access the dashboard
            logger.info("Accessing symptom dashboard...")
            with self.captured_templates(self.app) as templates:
                response = self.client.get('/symptom-dashboard')
                logger.info(f"Dashboard response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                # Check response
                self.assertEqual(response.status_code, 200, 
                             f"Failed to load dashboard. Status: {response.status_code}")
                
                # Verify templates were rendered
                self.assertGreater(len(templates), 0, "No templates were rendered")
                
                # Get the first valid template
                valid_templates = [t for t in templates if t[0] is not None]
                if not valid_templates:
                    logger.error("No valid templates found in response")
                    self.fail("No valid templates were rendered")
                
                template, context = valid_templates[0]
                logger.info(f"Using template: {template.name}")
                logger.info(f"Template context keys: {list(context.keys())}")
                
                # Check if symptom data is in the context
                self.assertIn('symptoms', context, "'symptoms' not in template context")
                self.assertIn('categories', context, "'categories' not in template context")
                
                # Check if our test symptom is in the data
                symptoms = context['symptoms']
                logger.info(f"Found {len(symptoms)} symptoms in context")
                
                # Log all symptoms for debugging
                logger.info("All symptoms in context:")
                for i, symptom in enumerate(symptoms):
                    logger.info(f"  {i+1}. {symptom.get('name')} - Severity: {symptom.get('severity')}, "
                               f"Category: {symptom.get('category')}")
                
                # Verify the test symptom is present
                symptom_found = any(
                    s.get('name') == 'Headache' and 
                    s.get('severity') == 'High' and
                    'neurological' in s.get('category', '')
                    for s in symptoms
                )
                
                if not symptom_found:
                    logger.warning("Test symptom not found in context. Available symptoms:")
                    for i, s in enumerate(symptoms):
                        logger.warning(f"  {i+1}. {s.get('name')} - Severity: {s.get('severity')}, "
                                     f"Category: {s.get('category')}")
                
                self.assertTrue(symptom_found, "Test symptom not found in context")
                
        except Exception as e:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
            raise
        finally:
            logger.info("=== Completed test_symptom_dashboard_shows_data ===\n")

if __name__ == '__main__':
    unittest.main()

import unittest
import os
import json
import logging
from datetime import datetime, timedelta

# SQLAlchemy imports
from sqlalchemy import event, types, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

# Flask imports
from flask import url_for
from flask_login import current_user

# Test client
from flask_testing import TestCase

# Import the Flask app and database
from app import app, db
from models_sqlalchemy import User, Provider, Patient, HealthInfo, UserInteraction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY='test-secret-key'
        )
        return app
    
    def setUp(self):
        """Set up test data"""
        with app.app_context():
            try:
                # Create all tables
                db.create_all()
                
                # Create test user
                self.test_user = User(
                    username='testuser',
                    email='test@example.com'
                )
                self.test_user.set_password('testpass')
                db.session.add(self.test_user)
                
                # Create test provider
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
                            'severity': 'High',
                            'duration': '1 day',
                            'notes': 'Severe headache with dizziness'
                        }],
                        'category': 'neurological'
                    },
                    created_at=datetime.utcnow()
                )
                db.session.add(self.test_symptom)
                
                db.session.commit()
                logger.info("Test data created successfully")
                
            except Exception as e:
                logger.error(f"Error setting up test data: {str(e)}")
                db.session.rollback()
                raise
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
            logger.info("Test database cleaned up")
    
    def login(self, username='testuser', password='testpass'):
        """Helper method to log in a test user"""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def test_symptom_dashboard_requires_login(self):
        """Test that the symptom dashboard requires login"""
        response = self.client.get('/symptom-dashboard', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)
    
    def test_symptom_dashboard_loads(self):
        """Test that the symptom dashboard loads for authenticated users"""
        # Log in
        self.login()
        
        # Access the dashboard
        response = self.client.get('/symptom-dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Symptom Dashboard', response.data)
    
    def test_symptom_dashboard_shows_data(self):
        """Test that the symptom dashboard shows symptom data"""
        # Log in
        self.login()
        
        # Access the dashboard
        response = self.client.get('/symptom-dashboard')
        
        # Check if test patient's symptom is shown
        self.assertIn(b'Test Patient', response.data)
        self.assertIn(b'Headache', response.data)


if __name__ == '__main__':
    unittest.main()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            try:
                db.session.remove()
                db.drop_all()
                logger.info("Test database cleaned up")
            except Exception as e:
                logger.error(f"Error during teardown: {str(e)}")
                raise
    
    def login(self, username='testuser', password='testpass'):
        """Helper method to log in a test user"""
        with app.test_client() as client:
            return client.post('/login', data=dict(
                username=username,
                password=password
            ), follow_redirects=True)
    
    def test_symptom_dashboard_requires_login(self):
        """Test that the symptom dashboard requires login"""
        with app.test_client() as client:
            response = client.get('/symptom-dashboard', follow_redirects=True)
            self.assertIn(b'Please log in to access this page', response.data)
    
    def test_symptom_dashboard_loads(self):
        """Test that the symptom dashboard loads for authenticated users"""
        with app.test_client() as client:
            # Log in
            self.login()
            
            # Access the dashboard
            response = client.get('/symptom-dashboard')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Symptom Dashboard', response.data)
    
    def test_symptom_dashboard_shows_data(self):
        """Test that the symptom dashboard shows symptom data"""
        with app.test_client() as client:
            # Log in
            self.login()
            
            # Access the dashboard
            response = client.get('/symptom-dashboard')
            
            # Check if test patient's symptoms are shown
            self.assertIn(b'Test Patient', response.data)
            self.assertIn(b'Fever', response.data)
            self.assertIn(b'Cough', response.data)
            self.assertIn(b'Headache', response.data)
    
    def test_filter_by_severity(self):
        """Test filtering symptoms by severity"""
        with app.test_client() as client:
            # Log in
            self.login()
            
            # Filter by high severity
            response = client.get('/symptom-dashboard?severity=High')
            self.assertIn(b'Headache', response.data)  # Should be shown
            self.assertNotIn(b'Fever', response.data)   # Should be filtered out
    
    def test_search_functionality(self):
        """Test searching for symptoms"""
        with app.test_client() as client:
            # Log in
            self.login()
            
            # Search for 'cough'
            response = client.get('/symptom-dashboard?search=cough')
            self.assertIn(b'Cough', response.data)       # Should be shown
            self.assertNotIn(b'Headache', response.data)  # Should be filtered out
    
    def test_export_functionality(self):
        """Test exporting symptom data"""
        with app.test_client() as client:
            # Log in
            self.login()
            
            # Export as CSV
            response = client.get('/symptom-dashboard/export?format=csv')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'text/csv')
            self.assertIn(b'Test Patient', response.data)
    
    def test_sorting_functionality(self):
        """Test sorting symptom data"""
        with app.test_client() as client:
            # Log in
            self.login()
            
            # Sort by date (newest first)
            response = client.get('/symptom-dashboard?sort=date&order=desc')
            self.assertEqual(response.status_code, 200)
            
            # The newest symptom (Headache) should appear first
            content = response.data.decode('utf-8')
            headache_pos = content.find('Headache')
            fever_pos = content.find('Fever')
            self.assertTrue(0 < headache_pos < fever_pos)
    
    def test_pagination(self):
        """Test that pagination works correctly"""
        with app.test_client() as client:
            # Log in
            self.login()
            
            # Request first page with 2 items per page
            response = client.get('/symptom-dashboard?page=1&per_page=2')
            self.assertEqual(response.status_code, 200)
            
            # Should show only 2 symptoms
            content = response.data.decode('utf-8')
            self.assertEqual(content.count('symptom-row'), 2)
            
            # Request second page
            response = client.get('/symptom-dashboard?page=2&per_page=2')
            content = response.data.decode('utf-8')
            self.assertEqual(content.count('symptom-row'), 1)
    
    def test_invalid_filters(self):
        """Test that invalid filters don't break the dashboard"""
        with app.test_client() as client:
            # Log in
            self.login()
            
            # Test with invalid severity
            response = client.get('/symptom-dashboard?severity=InvalidSeverity')
            self.assertEqual(response.status_code, 200)
            
            # Test with invalid date range
            response = client.get('/symptom-dashboard?start_date=invalid&end_date=dates')
            self.assertEqual(response.status_code, 200)
    
    def test_empty_state(self):
        """Test that the dashboard handles empty results gracefully"""
        with app.test_client() as client:
            # Log in
            self.login()
            
            # Delete all symptoms
            HealthInfo.query.filter_by(category='symptom').delete()
            db.session.commit()
            
            # Access the dashboard
            response = client.get('/symptom-dashboard')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'No symptoms found', response.data)
    
    def test_unauthorized_access(self):
        """Test that non-provider users can't access the dashboard"""
        # Create a non-provider user
        with app.app_context():
            regular_user = User(username='regular', email='regular@example.com')
            regular_user.set_password('testpass')
            db.session.add(regular_user)
            db.session.commit()
        
        with app.test_client() as client:
            # Log in as regular user
            client.post('/login', data=dict(
                username='regular',
                password='testpass'
            ), follow_redirects=True)
            
            # Try to access the dashboard
            response = client.get('/symptom-dashboard', follow_redirects=True)
            self.assertEqual(response.status_code, 403)  # Should be forbidden


if __name__ == '__main__':
    # Run the tests
    unittest.main(failfast=True)
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        logger.info("\n" + "="*80)
        logger.info(f"Setting up test: {self._testMethodName}")
        logger.info("="*80)
        
        # Create all database tables
        with app.app_context():
            logger.info("Creating database tables")
            db.create_all()
            
            try:
                # Create a test user and provider
                logger.info("Creating test user and provider")
                self.test_user = User(
                    username='testuser',
                    email='test@example.com',
                )
                self.test_user.set_password('testpass')
                
                self.test_provider = Provider(
                    user=self.test_user,
                    name='Test Provider',
                    specialization='General Practitioner',
                    license_number='TEST123',
                    user_id=1  # Ensure this matches the test user's ID
                )
                
                # Add and commit the test user and provider
                db.session.add(self.test_user)
                db.session.add(self.test_provider)
                db.session.commit()
                
                logger.info(f"Created test user: {self.test_user.username} (ID: {self.test_user.id})")
                logger.info(f"Created test provider: {self.test_provider.name} (ID: {self.test_provider.id})")
                
                # Create a test patient
                logger.info("Creating test patient")
                self.test_patient = Patient(
                    id=1,  # Explicit ID for easier reference
                    phone_number='+254700000000',
                    name='Test Patient',
                    age=30,
                    gender='Male',
                    location='Nairobi, Kenya',
                    coordinates=json.dumps({'lat': -1.286389, 'lng': 36.817223})  # JSON string for SQLite
                )
                
                # Add the test patient
                db.session.add(self.test_patient)
                db.session.commit()
                
                logger.info(f"Created test patient: {self.test_patient.name} (ID: {self.test_patient.id})")
                
                # Create health info records for symptoms
                logger.info("Creating test health info records")
                self.symptom1 = HealthInfo(
                    patient_id=self.test_patient.id,
                    title='Fever',
                    content='''Chief Complaint: Fever
    Severity: Moderate
    Duration: 2 days
    Associated Symptoms: Headache, Chills
    Notes: Patient reports feeling warm to touch''',
                    category='symptom',
                    created_at=datetime.utcnow() - timedelta(days=1)
                )
                
                self.symptom2 = HealthInfo(
                    patient_id=self.test_patient.id,
                    title='Cough',
                    content='''Chief Complaint: Dry cough
    Severity: Mild
    Duration: 3 days
    Associated Symptoms: Sore throat
    Notes: Worse at night''',
                    category='symptom',
                    created_at=datetime.utcnow() - timedelta(days=2)
                )
                
                # Add the test symptoms
                db.session.add(self.symptom1)
                db.session.add(self.symptom2)
                db.session.commit()
                
                logger.info(f"Created symptom 1: {self.symptom1.title} (ID: {self.symptom1.id})")
                logger.info(f"Created symptom 2: {self.symptom2.title} (ID: {self.symptom2.id})")
                
                # Create a test interaction
                logger.info("Creating test user interaction")
                interaction = UserInteraction(
                    patient_id=self.test_patient.id,
                    interaction_type='symptom_report',
                    description='Reported fever and cough',
                    interaction_metadata=json.dumps({
                        'symptoms': ['fever', 'cough'],
                        'severity': 'moderate',
                        'source': 'web'
                    })
                )
                db.session.add(interaction)
                db.session.commit()
                
                logger.info(f"Created user interaction (ID: {interaction.id})")
                
                # Log the current state of the database
                self._log_database_state()
                
            except Exception as e:
                logger.error(f"Error during test setup: {str(e)}", exc_info=True)
                db.session.rollback()
                raise
    
    def _log_database_state(self):
        """Log the current state of the database for debugging"""
        try:
            logger.info("\nDatabase State:")
            logger.info("-" * 50)
            
            # Log users
            users = User.query.all()
            logger.info(f"Users ({len(users)}):")
            for user in users:
                logger.info(f"  - {user.id}: {user.username} ({user.email})")
            
            # Log providers
            providers = Provider.query.all()
            logger.info(f"Providers ({len(providers)}):")
            for provider in providers:
                logger.info(f"  - {provider.id}: {provider.name} (User ID: {provider.user_id})")
            
            # Log patients
            patients = Patient.query.all()
            logger.info(f"Patients ({len(patients)}):")
            for patient in patients:
                logger.info(f"  - {patient.id}: {patient.name} ({patient.phone_number})")
            
            # Log health info
            health_infos = HealthInfo.query.all()
            logger.info(f"Health Info Records ({len(health_infos)}):")
            for hi in health_infos:
                logger.info(f"  - {hi.id}: {hi.title} (Patient ID: {hi.patient_id}, Category: {hi.category})")
            
            # Log user interactions
            interactions = UserInteraction.query.all()
            logger.info(f"User Interactions ({len(interactions)}):")
            for interaction in interactions:
                logger.info(f"  - {interaction.id}: {interaction.interaction_type} (Patient ID: {interaction.patient_id})")
                
        except Exception as e:
            logger.error(f"Error logging database state: {str(e)}", exc_info=True)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def login(self, username='testuser', password='testpass'):
        """Helper method to log in a test user"""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
        
    def test_symptom_dashboard_route(self):
        """Test that the symptom dashboard route returns a 200 status code"""
        logger.info("Starting test_symptom_dashboard_route...")
        with app.test_client() as client:
            # Log in the test user
            logger.info("Logging in test user...")
            login_response = client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            logger.info(f"Login response status: {login_response.status_code}")
            logger.debug(f"Login response data: {login_response.data.decode('utf-8')[:200]}...")
            
            # Access the symptom dashboard
            logger.info("Accessing symptom dashboard...")
            response = client.get('/symptom-dashboard')
            logger.info(f"Dashboard response status: {response.status_code}")
            
            # Log response data for debugging
            response_text = response.data.decode('utf-8', 'ignore')
            logger.info(f"Response length: {len(response_text)} characters")
            logger.debug(f"Response preview: {response_text[:500]}...")
            
            # Check status code
            self.assertEqual(response.status_code, 200, 
                           f"Expected status code 200, got {response.status_code}")
            
            # Check for expected content
            self.assertIn(b'Symptom Dashboard', response.data,
                        "'Symptom Dashboard' text not found in response")
            
            # Check for test patient data
            patient_name = 'Test Patient'.encode()
            self.assertIn(patient_name, response.data,
                        f"Test patient name not found in response. Response: {response_text[:500]}...")
            
            logger.info("test_symptom_dashboard_route completed successfully")
    
    def test_symptom_dashboard_requires_login(self):
        """Test that the symptom dashboard requires login"""
        logger.info("Starting test_symptom_dashboard_requires_login...")
        with app.test_client() as client:
            # Try to access dashboard without logging in
            logger.info("Accessing dashboard without login...")
            response = client.get('/symptom-dashboard', follow_redirects=True)
            
            # Log response for debugging
            logger.info(f"Response status: {response.status_code}")
            response_text = response.data.decode('utf-8', 'ignore')
            logger.debug(f"Response preview: {response_text[:500]}...")
            
            # Check for login prompt
            self.assertIn(b'Please log in to access this page', response.data,
                        "Login prompt not found in response")
            logger.info("test_symptom_dashboard_requires_login completed successfully")
    
    def test_symptom_dashboard_shows_symptoms(self):
        """Test that the symptom dashboard shows the test patient's symptoms"""
        logger.info("Starting test_symptom_dashboard_shows_symptoms...")
        with app.test_client() as client:
            # Log in
            logger.info("Logging in test user...")
            login_response = client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            logger.info(f"Login response status: {login_response.status_code}")
            
            # Access the dashboard
            logger.info("Accessing symptom dashboard...")
            response = client.get('/symptom-dashboard')
            logger.info(f"Dashboard response status: {response.status_code}")
            
            # Log response for debugging
            response_text = response.data.decode('utf-8', 'ignore').lower()
            logger.debug(f"Response preview: {response_text[:500]}...")
            
            # Check that the test symptoms are shown
            logger.info("Checking for symptoms in response...")
            self.assertIn('fever', response_text, 
                        "'fever' not found in response")
            self.assertIn('cough', response_text, 
                        "'cough' not found in response")
                        
            logger.info("test_symptom_dashboard_shows_symptoms completed successfully")
    
    def test_symptom_dashboard_filtering(self):
        """Test that the symptom dashboard filters work correctly"""
        with app.test_client() as client:
            # Log in
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            # Test severity filter
            response = client.get('/symptom-dashboard?severity=mild')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'mild', response.data.lower())
            self.assertIn(b'Test Patient', response.data)  # Should show mild case
            self.assertNotIn(b'Another Patient', response.data)  # Should not show moderate case
            
            # Test category filter
            response = client.get('/symptom-dashboard?category=respiratory')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'respiratory', response.data.lower())
            self.assertIn(b'Test Patient', response.data)  # Should show respiratory case
            self.assertNotIn(b'Another Patient', response.data)  # Should not show neurological case
            
            # Test date range filter
            today = datetime.utcnow().strftime('%Y-%m-%d')
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
            response = client.get(f'/symptom-dashboard?start_date={yesterday}&end_date={yesterday}')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Another Patient', response.data)  # Should show yesterday's case
            self.assertNotIn(b'Test Patient', response.data)  # Should not show today's case
    
    def test_symptom_dashboard_search(self):
        """Test that the symptom dashboard search works correctly"""
        with app.test_client() as client:
            # Log in
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            # Test search for patient name
            response = client.get('/symptom-dashboard?search=Test+Patient')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test Patient', response.data)
            
            # Test search for symptom
            response = client.get('/symptom-dashboard?search=fever')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'fever', response.data.lower())
    
    def test_export_functionality(self):
        """Test that the export functionality works"""
        with app.test_client() as client:
            # Log in
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            # Test CSV export
            response = client.get('/export-symptoms?format=csv')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'text/csv')
            self.assertIn(b'Patient Name,Symptom,Severity,Category', response.data)
            self.assertIn(b'Test Patient', response.data)
            
            # Test Excel export
            response = client.get('/export-symptoms?format=excel')
            self.assertEqual(response.status_code, 200)
            self.assertIn('spreadsheetml', response.mimetype)
            
            # Test export with filters
            response = client.get('/export-symptoms?format=csv&severity=mild')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test Patient', response.data)
            self.assertNotIn(b'Another Patient', response.data)
    
    def test_sorting_functionality(self):
        """Test that sorting works correctly in the symptom dashboard"""
        with app.test_client() as client:
            # Log in
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            # Test sorting by patient name (ascending)
            response = client.get('/symptom-dashboard?sort=patient_name&order=asc')
            self.assertEqual(response.status_code, 200)
            
            # Test sorting by date (descending)
            response = client.get('/symptom-dashboard?sort=date&order=desc')
            self.assertEqual(response.status_code, 200)
            
            # Test sorting by severity (ascending)
            response = client.get('/symptom-dashboard?sort=severity&order=asc')
            self.assertEqual(response.status_code, 200)
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        with app.test_client() as client:
            # Log in
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            # Test with invalid date range
            response = client.get('/symptom-dashboard?start_date=invalid-date&end_date=invalid-date')
            self.assertEqual(response.status_code, 200)  # Should handle gracefully
            
            # Test with non-existent category
            response = client.get('/symptom-dashboard?category=nonexistent')
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'Test Patient', response.data)  # No results expected
            
            # Test with empty search term
            response = client.get('/symptom-dashboard?search=')
            self.assertEqual(response.status_code, 200)
    
    def create_test_data(self):
        """Create comprehensive test data in the database"""
        print("\n=== Creating test data ===")
        
        # Create test users
        users = [
            {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'testpass',
                'role': 'provider'
            },
            {
                'username': 'adminuser',
                'email': 'admin@example.com',
                'password': 'adminpass',
                'role': 'admin'
            }
        ]
        
        for user_data in users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()
            
            if user_data['role'] == 'provider':
                provider = Provider(
                    user_id=user.id,
                    name=f"{user_data['username'].title()}",
                    specialty='General Medicine',
                    phone_number='+1234567890',
                    languages=['en'],
                    created_at=datetime.utcnow()
                )
                db.session.add(provider)
                print(f"Created provider: {provider.name}")
        
        # Create test patients with health info
        patients = [
            {
                'phone_number': '+1234567891',
                'name': 'John Doe',
                'age': 30,
                'gender': 'Male',
                'symptoms': ['fever', 'cough', 'headache'],
                'diagnosis': 'Common cold',
                'treatment': 'Rest and hydration',
                'severity': 'mild'
            },
            {
                'phone_number': '+1234567892',
                'name': 'Jane Smith',
                'age': 25,
                'gender': 'Female',
                'symptoms': ['fever', 'sore throat', 'fatigue'],
                'diagnosis': 'Strep throat',
                'treatment': 'Antibiotics',
                'severity': 'moderate'
            },
            {
                'phone_number': '+1234567893',
                'name': 'Bob Johnson',
                'age': 45,
                'gender': 'Male',
                'symptoms': ['shortness of breath', 'chest pain'],
                'diagnosis': 'Asthma',
                'treatment': 'Inhaler and medication',
                'severity': 'severe'
            }
        ]
        
        for p_data in patients:
            patient = Patient(
                phone_number=p_data['phone_number'],
                name=p_data['name'],
                age=p_data['age'],
                gender=p_data['gender'],
                location='Test Location',
                coordinates={'lat': 0, 'lng': 0},
                language='en',
                created_at=datetime.utcnow()
            )
            db.session.add(patient)
            db.session.flush()
            
            health_info = HealthInfo(
                patient_id=patient.id,
                symptoms=p_data['symptoms'],
                diagnosis=p_data['diagnosis'],
                treatment=p_data['treatment'],
                severity=p_data['severity'],
                notes=f"Patient reported: {', '.join(p_data['symptoms'])}",
                created_at=datetime.utcnow()
            )
            db.session.add(health_info)
            print(f"Created patient: {p_data['name']} with {p_data['diagnosis']}")
        
        db.session.commit()
        print("Successfully committed test data")
        
    def setUp(self):
        """Set up test client and data"""
        self.client = app.test_client()
        
        with app.app_context():
            # Clear any existing data
            db.session.remove()
            db.drop_all()
            db.create_all()
            
            # Create test data
            self.create_test_data()
            
            # Get references to test data
            self.test_user = User.query.filter_by(username='testuser').first()
            self.test_provider = Provider.query.first()
            self.test_patient = Patient.query.first()
            self.test_health_info = HealthInfo.query.first()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
            db.session.commit()
        with app.app_context():
            db.session.remove()
            db.drop_all()
        
        # Create test client
        self.client = app.test_client()
        
        # Create database tables
        with app.app_context():
            # Drop all tables first to ensure clean state
            db.drop_all()
            # Create all tables
            db.create_all()
            
            # Create test user
            hashed_password = generate_password_hash('testpass')
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hashed_password,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()  # Flush to get the user ID
            
            # Create test provider associated with the user
            provider = Provider(
                user_id=user.id,
                name='Test Provider',
                specialty='General Practitioner',
                phone='+1234567890',
                address='123 Test St, Test City',
                created_at=datetime.utcnow()
            )
            db.session.add(provider)
            
            # Create test patient
            patient = Patient(
                phone_number='+1234567890',
                name='Test Patient',
                age=30,
                gender='Male',
                location='Test Location',
                coordinates=json.dumps({'lat': 0, 'lng': 0}),
                language='en',
                created_at=datetime.utcnow()
            )
            db.session.add(patient)
            db.session.flush()  # Flush to get the patient ID
            
            # Create test health info
            health_info = HealthInfo(
                patient_id=patient.id,
                symptoms=json.dumps({
                    'fever': True,
                    'cough': False,
                    'headache': True,
                    'sore_throat': False,
                    'fatigue': True
                }),
                severity='moderate',
                notes='Test notes',
                created_at=datetime.utcnow()
            )
            db.session.add(health_info)
            
            # Commit all changes
            db.session.commit()
            
            self.user = user
            self.provider = provider
            self.patient = patient
            self.health_info = health_info
            
            # Create test symptom data
            symptoms = [
                {
                    'patient_id': self.patient.id,
                    'content': 'cough\nSeverity: moderate\nLocation: chest',
                    'category': 'symptom',
                    'is_published': True,
                    'created_at': datetime.utcnow()
                },
                {
                    'patient_id': self.patient.id,
                    'content': 'fever\nSeverity: mild\nLocation: head',
                    'category': 'symptom',
                    'is_published': True,
                    'created_at': datetime.utcnow() - timedelta(days=1)
                },
                {
                    'patient_id': self.patient.id,
                    'content': 'headache\nSeverity: severe\nLocation: head',
                    'category': 'symptom',
                    'is_published': True,
                    'created_at': datetime.utcnow() - timedelta(days=2)
                }
            ]
            
            for symptom in symptoms:
                health_info = HealthInfo(**symptom)
                db_ext.session.add(health_info)
            
            db_ext.session.commit()
        
        # Patch the login_required decorator
        self.patcher = patch('app.login_required', lambda x: x)
        self.mock_login_required = self.patcher.start()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db_ext.session.remove()
            db_ext.drop_all()
        self.patcher.stop()
        self.app_context.pop()
    
    def login(self):
        """Helper method to log in as test user"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user.id
            sess['_fresh'] = True  # Mark the session as fresh
        return True
    
    def test_symptom_dashboard_loads(self):
        """Test that the symptom dashboard loads"""
        logger.info("Starting symptom dashboard load test...")
        
        # 1. Verify database state
        logger.info("Verifying database state...")
        with app.app_context():
            # Check if tables exist and have data
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Found {len(tables)} tables in database")
            
            # Verify essential tables exist
            required_tables = {'users', 'providers', 'patients', 'health_info'}
            missing_tables = required_tables - set(tables)
            if missing_tables:
                logger.error(f"Missing required tables: {missing_tables}")
            
            # Check record counts
            for table in required_tables:
                if table in tables:
                    try:
                        count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                        logger.info(f"Table {table}: {count} records")
                    except Exception as e:
                        logger.error(f"Error counting records in {table}: {str(e)}")
        
        # 2. Test login
        logger.info("Testing login...")
        with app.test_client() as client:
            # Log in
            response = client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            logger.info(f"Login response status: {response.status_code}")
            logger.info(f"Redirected to: {response.request.path}")
            
            # Check if login was successful
            self.assertEqual(response.status_code, 200, "Login failed")
            
            # Check if we're redirected to dashboard after login
            self.assertIn(b'Symptom Dashboard', response.data, 
                        "Not redirected to dashboard after login")
            
            # 3. Test dashboard access
            logger.info("Accessing symptom dashboard...")
            response = client.get('/symptom-dashboard')
            
            logger.info(f"Dashboard response status: {response.status_code}")
            logger.info(f"Response length: {len(response.data)} bytes")
            
            # Check response
            self.assertEqual(response.status_code, 200, 
                          f"Expected status 200, got {response.status_code}")
            self.assertIn(b'Symptom Dashboard', response.data,
                        "'Symptom Dashboard' not found in response")
            
            # Check for common error messages
            error_indicators = [b'error', b'exception', b'traceback', 
                             b'not found', b'forbidden', b'unauthorized']
            for indicator in error_indicators:
                self.assertNotIn(indicator, response.data.lower(),
                               f"Found error indicator in response: {indicator}")
            
            # Check for expected UI elements
            expected_elements = [
                b'Filter by Severity',
                b'Filter by Category',
                b'Export Data'
            ]
            for element in expected_elements:
                self.assertIn(element, response.data,
                            f"Expected element not found: {element.decode()}")
            
            logger.info("Symptom dashboard test completed successfully")
        
        # 4. Test login functionality
        print("\n[4/6] TESTING LOGIN")
        print("-"*40)
        with app.test_client() as client:
            print("\nAttempting to log in...")
            
            # Print login attempt details
            print(f"Login URL: /login")
            print(f"Username: testuser")
            print("Sending login request...")
            
            # Send login request
            response = client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)
            
            # Print login response details
            print(f"\nLogin response status: {response.status}")
            print(f"Redirected to: {response.request.path}")
            print(f"Response length: {len(response.data)} bytes")
            
            # Check if login was successful
            if response.status_code == 200 and b'Login' not in response.data:
                print("Login successful!")
                
                # Print session information
                with client.session_transaction() as sess:
                    print("\nSession data:")
                    for key, value in sess.items():
                        print(f"  {key}: {value}")
            else:
                print("Login failed!")
            
            # Check if the response contains expected content
            self.assertIn(b'Symptom Dashboard', response.data,
                        "'Symptom Dashboard' not found in response")
            
            # Print response headers
            print("\nResponse headers:")
            for key, value in response.headers.items():
                if key.lower() in ['content-type', 'content-length']:
                    print(f"  {key}: {value}")
            
            # Print a portion of the response for debugging
            response_text = response.data.decode('utf-8', 'ignore')
            print("\nResponse preview (first 500 chars):")
            print("-" * 50)
            print(response_text[:500])
            print("-" * 50)
            
            # Check for common error messages in the response
            error_indicators = [
                'error', 'exception', 'traceback', 'not found', 'forbidden', 'unauthorized'
            ]
            
            for indicator in error_indicators:
                if indicator.encode() in response.data.lower():
                    print(f"\nWARNING: Found potential error indicator in response: '{indicator}'")
        
        # 6. Test complete and clean up
        print("\n[6/6] TEST COMPLETION AND CLEANUP")
        print("-"*40)
        print("All assertions passed!")
        print("="*80 + "\n")
        
        # Print app configuration
        print("\nApp configuration:")
        for key, value in app.config.items():
            if 'SECRET' not in key and 'PASSWORD' not in key and 'TOKEN' not in key:
                print(f"  {key}: {value}")
        
        # Print database URL
        print(f"\nDatabase URL: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        
        # Print all registered routes
        print("\nRegistered routes:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule.rule} {list(rule.methods - {'OPTIONS', 'HEAD'})}")
            
        # Print database state before login
        with app.app_context():
            print("\nDatabase state before login:")
            print(f"  Users: {User.query.count()}")
            print(f"  Providers: {Provider.query.count()}")
            print(f"  Patients: {Patient.query.count()}")
            print(f"  HealthInfo: {HealthInfo.query.count()}")
            
            # Print first user and provider
            user = User.query.first()
            if user:
                print(f"  First user: {user.username} (ID: {user.id})")
                provider = Provider.query.filter_by(user_id=user.id).first()
                if provider:
                    print(f"  Provider: {provider.name} (ID: {provider.id})")
        
        # Log in
        print("\nAttempting to log in...")
        print("\n=== Testing symptom dashboard load ===")
        
        # Print initial database state
        with app.app_context():
            try:
                user_count = User.query.count()
                patient_count = Patient.query.count()
                provider_count = Provider.query.count()
                health_info_count = HealthInfo.query.count()
                print(f"Initial database state - Users: {user_count}, Providers: {provider_count}, Patients: {patient_count}, HealthInfo: {health_info_count}")
                
                # Print user and provider details
                user = User.query.first()
                if user:
                    print(f"User: id={user.id}, username={user.username}, email={user.email}")
                    provider = Provider.query.filter_by(user_id=user.id).first()
                    if provider:
                        print(f"Provider: id={provider.id}, name={provider.name}, user_id={provider.user_id}")
                
                # Print all tables in the database
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"\nDatabase tables: {tables}")
                
                # Print all routes in the app
                print("\nAvailable routes:")
                for rule in app.url_map.iter_rules():
                    print(f"{rule.endpoint}: {rule.rule} {list(rule.methods - {'OPTIONS', 'HEAD'})}")
                    
            except Exception as e:
                print(f"Error checking database state: {str(e)}")
        
        # Log in
        print("\nAttempting to log in...")
        login_result = self.login()
        print(f"Login result: {login_result}")
        
        # Make the request
        print("\nMaking request to /symptom-dashboard")
        try:
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = self.user.id
                    sess['_fresh'] = True
                
                response = client.get('/symptom-dashboard', follow_redirects=True)
                
                # Print response details
                print(f"\nResponse status code: {response.status_code}")
                print(f"Response content type: {response.content_type}")
                print(f"Response data length: {len(response.data) if response.data else 0}")
                
                # Print response headers
                print("\nResponse headers:")
                for key, value in response.headers.items():
                    print(f"{key}: {value}")
                
                # Print a portion of the response data for debugging
                if response.data:
                    try:
                        response_text = response.data.decode('utf-8')
                        print("\nResponse data preview (first 500 chars):")
                        print(response_text[:500])
                    except UnicodeDecodeError:
                        print("Could not decode response data as UTF-8")
                
                # Check response
                self.assertEqual(response.status_code, 200, "Expected status code 200")
                self.assertIn(b'Symptom Dashboard', response.data, "Response should contain 'Symptom Dashboard'")
                
        except Exception as e:
            print(f"Error making request: {str(e)}")
            raise
    
    def test_search_functionality(self):
        """Test the symptom search functionality"""
        self.login()
        response = self.client.get('/symptom-dashboard?search=cough')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'cough', response.data.lower())
    
    def test_filter_by_severity(self):
        """Test filtering symptoms by severity"""
        self.login()
        response = self.client.get('/symptom-dashboard?severity=moderate')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'moderate', response.data.lower())
    
    def test_toggle_details_button(self):
        """Test the toggle details button"""
        self.login()
        response = self.client.get('/symptom-dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-bs-toggle="collapse"', response.data)
    
    @patch('app.symptom_dashboard')
    def test_export_buttons(self, mock_symptom_dashboard):
        """Test export buttons (CSV, Excel, PDF)"""
        self.login()
        
        # Mock the response from the symptom_dashboard function
        mock_symptom_dashboard.return_value = ({
            'symptom_data': [],
            'category_counts': {},
            'severity_data': {},
            'location_data': {},
            'time_data': {},
            'top_symptoms': {},
            'outbreak_signals': [],
            'total_symptoms': 0,
            'unique_symptoms': [],
            'avg_severity': 0,
            'top_location': ('Nairobi', 1)
        }, 200)
        
        # Test CSV export
        response = self.client.get('/symptom-dashboard/export/csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response.content_type)
    
    def test_outbreak_alerts(self):
        """Test outbreak alerts functionality"""
        self.login()
        response = self.client.get('/symptom-dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Potential Outbreak Alerts', response.data)
    
    def test_time_period_filter(self):
        """Test filtering by time period"""
        self.login()
        response = self.client.get('/symptom-dashboard?period=7d')
        self.assertEqual(response.status_code, 200)
    
    def test_category_filter(self):
        """Test filtering by symptom category"""
        self.login()
        response = self.client.get('/symptom-dashboard?category=respiratory')
        self.assertEqual(response.status_code, 200)
    
    def test_location_filter(self):
        """Test filtering by location"""
        self.login()
        response = self.client.get('/symptom-dashboard?location=Nairobi')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()

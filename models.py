from flask_login import UserMixin
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt
import uuid

# In-memory database for prototype
db = {
    'users': [],
    'providers': [],
    'patients': [],
    'appointments': [],
    'messages': [],
    'health_info': [],
    'user_interactions': [],
    'payments': []
}

def init_db():
    """Initialize demo data for the in-memory database"""
    # Always reset users to have consistent state
    db['users'] = []
    db['providers'] = []
    
    # Create a default admin user with proper password hash
    password_hash = generate_password_hash('admin123')
    print(f"Creating admin user with password hash: {password_hash}")
    # Directly create admin user with the expected password hash format
    user = User(1, 'admin', 'admin@tujali.com', 'hashed_admin123')
    db['users'].append(user)
    print(f"User created: {user.username}, password hash stored: {user.password_hash}")
    
    # Create providers with locations and coordinates
    provider1 = Provider(
        1, 1, 'Dr. John Doe', 'johndoe@example.com',
        'General Medicine', 
        'English, Swahili',
        'Nairobi, Kenya',
        (-1.2921, 36.8219)  # Nairobi coordinates
    )
    provider2 = Provider(
        2, 1, 'Dr. Sarah Kimani', 'sarahk@example.com',
        'Pediatrics', 
        'English, Swahili',
        'Mombasa, Kenya',
        (-4.0435, 39.6682)  # Mombasa coordinates
    )
    provider3 = Provider(
        3, 1, 'Dr. Mohammed Ali', 'mohammeda@example.com',
        'Cardiology', 
        'English, Swahili, Arabic',
        'Kisumu, Kenya',
        (-0.1022, 34.7617)  # Kisumu coordinates
    )
    provider4 = Provider(
        4, 1, 'Dr. Elizabeth Ochieng', 'elizabeto@example.com',
        'Obstetrics & Gynecology', 
        'English, Swahili, Luo',
        'Nakuru, Kenya',
        (-0.3031, 36.0800)  # Nakuru coordinates
    )
    provider5 = Provider(
        5, 1, 'Dr. Thomas Mutua', 'thomasm@example.com',
        'General Medicine', 
        'English, Swahili, Kamba',
        'Eldoret, Kenya',
        (0.5143, 35.2698)  # Eldoret coordinates
    )
    db['providers'].append(provider1)
    db['providers'].append(provider2)
    db['providers'].append(provider3)
    db['providers'].append(provider4)
    db['providers'].append(provider5)
    
    # Clear and add health information
    db['health_info'] = []
    info1 = HealthInfo(1, 'COVID-19 Prevention', 
                     'Wash hands regularly, wear masks in public, maintain social distance.', 
                     'en')
    info2 = HealthInfo(2, 'Kuzuia COVID-19', 
                      'Osha mikono mara kwa mara, vaa mask kwa umma, dumisha umbali wa kijamii.', 
                      'sw')
    info3 = HealthInfo(3, 'Maternal Health Tips', 
                     'Regular check-ups, balanced diet, and adequate rest are essential during pregnancy.', 
                     'en')
    info4 = HealthInfo(4, 'Ushauri wa Afya ya Uzazi', 
                     'Uchunguzi wa mara kwa mara, lishe bora, na kupumzika kwa kutosha ni muhimu wakati wa ujauzito.', 
                     'sw')
    db['health_info'].append(info1)
    db['health_info'].append(info2)
    db['health_info'].append(info3)
    db['health_info'].append(info4)
    
    # Add sample patients with locations and coordinates
    db['patients'] = []
    patient1 = Patient(
        1, '+254711001122', 'Jane Wanjiku', 32, 'Female', 
        'Nairobi', 'en', 
        (-1.2864, 36.8172)  # Nairobi coordinates (slight variation)
    )
    patient2 = Patient(
        2, '+254722334455', 'John Otieno', 45, 'Male', 
        'Kisumu', 'sw', 
        (-0.1050, 34.7550)  # Kisumu coordinates (slight variation)
    )
    patient3 = Patient(
        3, '+254733667788', 'Mary Akinyi', 28, 'Female', 
        'Mombasa', 'en', 
        (-4.0500, 39.6700)  # Mombasa coordinates (slight variation)
    )
    patient4 = Patient(
        4, '+254744990011', 'James Maina', 52, 'Male', 
        'Nakuru', 'sw', 
        (-0.3100, 36.0750)  # Nakuru coordinates (slight variation)
    )
    patient5 = Patient(
        5, '+254755223344', 'Grace Njeri', 19, 'Female', 
        'Eldoret', 'en',
        (0.5200, 35.2650)  # Eldoret coordinates (slight variation)
    )
    db['patients'].append(patient1)
    db['patients'].append(patient2)
    db['patients'].append(patient3)
    db['patients'].append(patient4)
    db['patients'].append(patient5)
    
    # Add symptoms to patients with varied types
    patient1.add_symptom('Persistent headache and fever for 3 days')
    patient1.add_symptom('Severe cough and difficulty breathing')
    patient1.add_symptom('Pain in joints and muscles, mild fever')
    
    patient2.add_symptom('Kikohozi na maumivu ya kifua kwa wiki moja')
    patient2.add_symptom('Stomach pain and vomiting, moderate severity')
    patient2.add_symptom('High fever with chills and sweating')
    
    patient3.add_symptom('Skin rash and itching on arms')
    patient3.add_symptom('Mild digestive issues with nausea')
    patient3.add_symptom('Persistent headache, unbearable at times')
    
    patient4.add_symptom('Chronic cough with chest pain, moderate severity')
    patient4.add_symptom('Skin lesions with slight itching on legs')
    
    patient5.add_symptom('Severe abdominal pain with vomiting')
    patient5.add_symptom('Mild fever and body aches')
    patient5.add_symptom('Respiratory difficulty when exercising')
    
    # Add sample appointments
    db['appointments'] = []
    appt1 = Appointment(1, 1, 1, '25-03-2025', '10:00 AM', 'confirmed', 500.00, 'completed')
    appt2 = Appointment(2, 2, 1, '26-03-2025', '2:30 PM', 'pending', 500.00, 'pending')
    appt3 = Appointment(3, 3, 1, '24-03-2025', '11:15 AM', 'completed', 750.00, 'pending')
    appt4 = Appointment(4, 4, 1, '27-03-2025', '9:00 AM', 'pending', 350.00, 'completed')
    appt5 = Appointment(5, 5, 1, '23-03-2025', '3:45 PM', 'cancelled', 400.00, 'pending')
    db['appointments'].append(appt1)
    db['appointments'].append(appt2)
    db['appointments'].append(appt3)
    db['appointments'].append(appt4)
    db['appointments'].append(appt5)
    
    # Add sample messages
    db['messages'] = []
    msg1 = Message(1, 1, 1, 'Hello Dr. Doe, I have been experiencing severe headaches.', 'patient')
    msg2 = Message(2, 1, 1, 'Hi Jane, I recommend you come in for a check-up. When are you available?', 'provider')
    msg3 = Message(3, 1, 1, 'I can come tomorrow morning if that works.', 'patient')
    msg4 = Message(4, 1, 1, 'Perfect. I have scheduled you for 10 AM tomorrow.', 'provider')
    msg5 = Message(5, 1, 2, 'Habari daktari, nina maumivu ya kifua.', 'patient', is_read=False)
    msg6 = Message(6, 1, 3, 'Doctor, the rash on my arms is getting worse.', 'patient', is_read=False)
    db['messages'].append(msg1)
    db['messages'].append(msg2)
    db['messages'].append(msg3)
    db['messages'].append(msg4)
    db['messages'].append(msg5)
    db['messages'].append(msg6)
    
    # Add sample user interactions for journey tracking
    db['user_interactions'] = []
    
    # Sample interactions for Patient 1 (Jane Wanjiku)
    # USSD interactions
    interaction1 = UserInteraction(1, 1, 'ussd', 'Started USSD session', {'session_id': 'ATI123456789'}, datetime(2025, 2, 1, 9, 30))
    interaction2 = UserInteraction(2, 1, 'ussd', 'Checked available appointments', {'session_id': 'ATI123456789'}, datetime(2025, 2, 1, 9, 33))
    interaction3 = UserInteraction(3, 1, 'ussd', 'Requested health information', {'session_id': 'ATI123456790'}, datetime(2025, 2, 5, 14, 15))
    
    # Symptom reporting
    interaction4 = UserInteraction(4, 1, 'symptom', 'Reported persistent headache', {'severity': 'Moderate'}, datetime(2025, 2, 10, 8, 45))
    interaction5 = UserInteraction(5, 1, 'symptom', 'Reported fever', {'severity': 'Mild'}, datetime(2025, 2, 10, 8, 47))
    
    # Appointment interactions
    interaction6 = UserInteraction(6, 1, 'appointment', 'Scheduled appointment with Dr. John Doe', {'date': '25-03-2025', 'time': '10:00 AM'}, datetime(2025, 2, 12, 11, 20))
    
    # Message interactions
    interaction7 = UserInteraction(7, 1, 'message', 'Sent message about headaches', {'message_id': 1}, datetime(2025, 3, 1, 10, 5))
    interaction8 = UserInteraction(8, 1, 'message', 'Received response from Dr. Doe', {'message_id': 2}, datetime(2025, 3, 1, 10, 30))
    interaction9 = UserInteraction(9, 1, 'message', 'Confirmed appointment availability', {'message_id': 3}, datetime(2025, 3, 1, 10, 35))
    
    # Health tip interactions
    interaction10 = UserInteraction(10, 1, 'health_tip', 'Received tips for headache management', {'tip_type': 'symptom_specific'}, datetime(2025, 3, 5, 9, 0))
    
    # Sample interactions for Patient 2 (John Otieno)
    interaction11 = UserInteraction(11, 2, 'ussd', 'Started USSD session in Swahili', {'session_id': 'ATI987654321', 'language': 'sw'}, datetime(2025, 2, 3, 12, 15))
    interaction12 = UserInteraction(12, 2, 'symptom', 'Reported chest pain and cough', {'severity': 'Severe'}, datetime(2025, 2, 3, 12, 20))
    interaction13 = UserInteraction(13, 2, 'appointment', 'Requested urgent consultation', {'provider': 'Any available'}, datetime(2025, 2, 3, 12, 25))
    interaction14 = UserInteraction(14, 2, 'message', 'Sent message about chest pain', {'message_id': 5}, datetime(2025, 2, 4, 9, 10))
    
    # Sample interactions for Patient 3 (Mary Akinyi)
    interaction15 = UserInteraction(15, 3, 'ussd', 'Accessed health information', {'topic': 'skin care'}, datetime(2025, 2, 8, 16, 30))
    interaction16 = UserInteraction(16, 3, 'symptom', 'Reported skin rash', {'severity': 'Moderate', 'location': 'arms'}, datetime(2025, 2, 8, 16, 35))
    interaction17 = UserInteraction(17, 3, 'message', 'Sent message about worsening rash', {'message_id': 6}, datetime(2025, 3, 2, 15, 40))
    interaction18 = UserInteraction(18, 3, 'health_tip', 'Received skin care recommendations', {'tip_type': 'condition_specific'}, datetime(2025, 3, 3, 10, 0))
    
    # Add the interactions to the database
    for i in range(1, 19):
        db['user_interactions'].append(eval(f"interaction{i}"))
        
    # Initialize payments collection
    db['payments'] = []
    
    # Add some sample payments
    payment1 = Payment(
        1,
        1,  # appointment_id
        500.00,  # amount (in KES)
        '+254711001122',  # phone_number
        'MPESA123456',  # mpesa_reference
        'completed',  # status
        'mpesa',  # payment_method
        datetime.now() - timedelta(days=3),  # created_at
        datetime.now() - timedelta(days=3)  # paid_at
    )
    
    payment2 = Payment(
        2,
        3,  # appointment_id
        750.00,  # amount (in KES)
        '+254733667788',  # phone_number
        None,  # mpesa_reference
        'pending',  # status
        'mpesa',  # payment_method
        datetime.now() - timedelta(days=1)  # created_at
    )
    
    payment3 = Payment(
        3,
        4,  # appointment_id
        350.00,  # amount (in KES)
        '+254722334455',  # phone_number
        'MPESA789012',  # mpesa_reference
        'completed',  # status
        'mpesa',  # payment_method
        datetime.now() - timedelta(days=7),  # created_at
        datetime.now() - timedelta(days=7)  # paid_at
    )
    
    db['payments'].append(payment1)
    db['payments'].append(payment2)
    db['payments'].append(payment3)

def generate_password_hash(password):
    """Mock password hashing for prototype"""
    return f"hashed_{password}"

def check_password_hash(hashed_password, password):
    """Mock password verification for prototype"""
    # For debugging
    print(f"Checking password: comparing '{hashed_password}' with 'hashed_{password}'")
    expected = f"hashed_{password}"
    return hashed_password == expected

class User(UserMixin):
    """User model for authentication"""
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        for user in db['users']:
            if user.id == user_id:
                return user
        return None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        for user in db['users']:
            if user.username == username:
                return user
        return None
        
    @staticmethod
    def username_exists(username):
        """Check if a username already exists"""
        return any(user.username == username for user in db['users'])
        
    @staticmethod
    def email_exists(email):
        """Check if an email already exists"""
        return any(user.email.lower() == email.lower() for user in db['users'])

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # Radius of earth in kilometers
    return c * r

class Provider:
    """Healthcare provider model"""
    def __init__(self, id, user_id, name, email, specialization, languages, location=None, coordinates=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.email = email
        self.specialization = specialization
        self.languages = languages
        self.location = location  # Text description of location (e.g., "Nairobi, Kenya")
        self.coordinates = coordinates  # Tuple (latitude, longitude) for distance calculations
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get provider by user ID"""
        for provider in db['providers']:
            if provider.user_id == user_id:
                return provider
        return None
    
    @staticmethod
    def get_by_id(provider_id):
        """Get provider by ID"""
        for provider in db['providers']:
            if provider.id == provider_id:
                return provider
        return None
    
    @staticmethod
    def get_all():
        """Get all providers"""
        return db['providers']
    
    @staticmethod
    def get_by_location(patient_coords, max_distance=50, specialization=None, languages=None):
        """
        Find providers within a certain distance of the patient
        
        Args:
            patient_coords (tuple): (latitude, longitude) of the patient
            max_distance (float): Maximum distance in kilometers
            specialization (str, optional): Filter by specialization
            languages (str, optional): Filter by languages
            
        Returns:
            list: List of provider objects sorted by distance
        """
        if not patient_coords:
            return Provider.get_all()  # Return all if no coordinates provided
            
        nearby_providers = []
        
        for provider in db['providers']:
            if not provider.coordinates:
                continue  # Skip providers without coordinates
                
            # Calculate distance
            distance = haversine(
                patient_coords[0], patient_coords[1],
                provider.coordinates[0], provider.coordinates[1]
            )
            
            # Apply filters
            if distance <= max_distance:
                if specialization and specialization not in provider.specialization:
                    continue
                    
                if languages and not any(lang in provider.languages for lang in languages.split(',')):
                    continue
                    
                # Add distance to provider object for sorting
                provider.distance = distance
                nearby_providers.append(provider)
        
        # Sort by distance
        return sorted(nearby_providers, key=lambda p: p.distance)

class Patient:
    """Patient model"""
    def __init__(self, id, phone_number, name, age, gender, location, language, coordinates=None, created_at=None):
        self.id = id
        self.phone_number = phone_number
        self.name = name
        self.age = age
        self.gender = gender
        self.location = location  # Text description of location (e.g., "Nairobi, Kenya")
        self.coordinates = coordinates  # Tuple (latitude, longitude) for distance calculations
        self.language = language
        self.created_at = created_at or datetime.now()
        self.symptoms = []
    
    @staticmethod
    def create(phone_number, name, age, gender, location, language, coordinates=None):
        """
        Create a new patient
        
        Args:
            phone_number (str): Patient's phone number
            name (str): Patient's name
            age (int): Patient's age
            gender (str): Patient's gender
            location (str): Text description of patient's location
            language (str): Patient's preferred language code (e.g., 'en', 'sw')
            coordinates (tuple, optional): (latitude, longitude) tuple
            
        Returns:
            Patient: Newly created patient object
        """
        patient_id = len(db['patients']) + 1
        patient = Patient(patient_id, phone_number, name, age, gender, location, language, coordinates)
        db['patients'].append(patient)
        return patient
    
    @staticmethod
    def get_by_phone(phone_number):
        """Get patient by phone number"""
        for patient in db['patients']:
            if patient.phone_number == phone_number:
                return patient
        return None
    
    @staticmethod
    def get_by_id(patient_id):
        """Get patient by ID"""
        for patient in db['patients']:
            if patient.id == patient_id:
                return patient
        return None
    
    @staticmethod
    def get_all():
        """Get all patients"""
        return sorted(db['patients'], key=lambda p: p.created_at, reverse=True)
    
    @staticmethod
    def get_recent(limit=5):
        """Get recently registered patients"""
        patients = sorted(db['patients'], key=lambda p: p.created_at, reverse=True)
        return patients[:limit]
    
    @staticmethod
    def get_count():
        """Get total number of patients"""
        return len(db['patients'])
    
    def add_symptom(self, symptom, severity=None, category=None):
        """
        Add a symptom to patient record
        
        Args:
            symptom (str): The symptom description text
            severity (str, optional): The severity of the symptom ('Mild', 'Moderate', or 'Severe')
            category (str, optional): The category of the symptom (e.g., 'respiratory', 'digestive')
        """
        # Auto-detect severity if not provided
        if not severity:
            if any(word in symptom.lower() for word in ['severe', 'unbearable', 'extreme']):
                severity = 'Severe'
            elif any(word in symptom.lower() for word in ['moderate', 'medium']):
                severity = 'Moderate'
            elif any(word in symptom.lower() for word in ['mild', 'slight', 'minor']):
                severity = 'Mild'
            else:
                severity = 'Unknown'
        
        # Auto-detect category if not provided
        if not category:
            symptom_categories = {
                'respiratory': ['cough', 'breathing', 'chest', 'breath', 'respiratory', 'pneumonia'],
                'digestive': ['stomach', 'diarrhea', 'nausea', 'vomit', 'digest', 'abdominal'],
                'pain': ['pain', 'ache', 'hurt', 'sore', 'headache', 'migraine'],
                'fever': ['fever', 'temperature', 'hot', 'chills', 'cold', 'sweat'],
                'skin': ['rash', 'itching', 'skin', 'lesion', 'bump', 'sore']
            }
            
            symptom_text = symptom.lower()
            for cat, keywords in symptom_categories.items():
                if any(keyword in symptom_text for keyword in keywords):
                    category = cat
                    break
            
            if not category:
                category = 'other'
        
        self.symptoms.append({
            'text': symptom, 
            'date': datetime.now(),
            'severity': severity,
            'category': category
        })
        
    def update_coordinates(self, latitude, longitude):
        """Update patient's geographical coordinates"""
        self.coordinates = (latitude, longitude)
        return True
        
    def find_nearby_providers(self, max_distance=50, specialization=None):
        """
        Find healthcare providers near this patient
        
        Args:
            max_distance (float): Maximum distance in kilometers
            specialization (str, optional): Filter by provider specialization
            
        Returns:
            list: List of provider objects sorted by distance
        """
        if not self.coordinates:
            return Provider.get_all()
            
        return Provider.get_by_location(
            self.coordinates, 
            max_distance=max_distance,
            specialization=specialization,
            languages=self.language
        )

class Appointment:
    """Appointment model"""
    def __init__(self, id, patient_id, provider_id, date, time, status, price=None, payment_status=None, notes=None, created_at=None, reminder_sent=False):
        self.id = id
        self.patient_id = patient_id
        self.provider_id = provider_id
        self.date = date
        self.time = time
        self.status = status  # pending, confirmed, completed, cancelled
        self.price = price  # Price in local currency
        self.payment_status = payment_status  # pending, completed, waived
        self.notes = notes
        self.created_at = created_at or datetime.now()
        self.reminder_sent = reminder_sent
    
    @staticmethod
    def create(patient_id, provider_id, date, time, price=None, notes=None):
        """Create a new appointment"""
        appointment_id = len(db['appointments']) + 1
        appointment = Appointment(
            appointment_id, 
            patient_id, 
            provider_id, 
            date, 
            time, 
            'pending', 
            price=price,
            payment_status='pending' if price else 'waived',
            notes=notes
        )
        db['appointments'].append(appointment)
        return appointment
    
    @staticmethod
    def get_by_id(appointment_id):
        """Get appointment by ID"""
        for appointment in db['appointments']:
            if appointment.id == appointment_id:
                return appointment
        return None
    
    @staticmethod
    def get_by_patient(patient_id):
        """Get all appointments for a patient"""
        return [a for a in db['appointments'] if a.patient_id == patient_id]
    
    @staticmethod
    def get_by_provider(provider_id):
        """Get all appointments for a provider"""
        appointments = [a for a in db['appointments'] if a.provider_id == provider_id]
        return sorted(appointments, key=lambda a: a.created_at, reverse=True)
    
    @staticmethod
    def get_recent_by_provider(provider_id, limit=5):
        """Get recent appointments for a provider"""
        appointments = [a for a in db['appointments'] if a.provider_id == provider_id]
        appointments = sorted(appointments, key=lambda a: a.created_at, reverse=True)
        return appointments[:limit]
    
    @staticmethod
    def get_count_by_status(provider_id, status):
        """Get count of appointments by status"""
        return len([a for a in db['appointments'] if a.provider_id == provider_id and a.status == status])
    
    @staticmethod
    def update_status(appointment_id, status, payment_status=None):
        """
        Update appointment status and payment status
        
        Args:
            appointment_id (int): ID of the appointment
            status (str): New appointment status (pending, confirmed, completed, cancelled)
            payment_status (str, optional): New payment status (pending, completed, waived)
            
        Returns:
            bool: True if updated, False if not found
        """
        for appointment in db['appointments']:
            if appointment.id == appointment_id:
                appointment.status = status
                if payment_status:
                    appointment.payment_status = payment_status
                return True
        return False

class Message:
    """Message model for communication between patients and providers"""
    def __init__(self, id, provider_id, patient_id, content, sender_type, is_read=False, created_at=None):
        self.id = id
        self.provider_id = provider_id
        self.patient_id = patient_id
        self.content = content
        self.sender_type = sender_type  # 'patient' or 'provider'
        self.is_read = is_read
        self.created_at = created_at or datetime.now()
    
    @staticmethod
    def create(provider_id, patient_id, content, sender_type):
        """Create a new message"""
        message_id = len(db['messages']) + 1
        message = Message(message_id, provider_id, patient_id, content, sender_type)
        db['messages'].append(message)
        return message
    
    @staticmethod
    def get_conversation(provider_id, patient_id):
        """Get conversation between provider and patient"""
        messages = [m for m in db['messages'] 
                   if m.provider_id == provider_id and m.patient_id == patient_id]
        return sorted(messages, key=lambda m: m.created_at)
    
    @staticmethod
    def get_conversations(provider_id):
        """Get all conversations for a provider"""
        # Get unique patient IDs from messages
        patient_ids = set()
        for message in db['messages']:
            if message.provider_id == provider_id:
                patient_ids.add(message.patient_id)
        
        # Get latest message for each patient
        conversations = []
        for patient_id in patient_ids:
            patient = Patient.get_by_id(patient_id)
            messages = [m for m in db['messages'] 
                       if m.provider_id == provider_id and m.patient_id == patient_id]
            latest_message = sorted(messages, key=lambda m: m.created_at, reverse=True)[0]
            unread_count = len([m for m in messages 
                               if m.sender_type == 'patient' and not m.is_read])
            
            conversations.append({
                'patient': patient,
                'latest_message': latest_message,
                'unread_count': unread_count
            })
        
        # Sort by latest message timestamp
        return sorted(conversations, key=lambda c: c['latest_message'].created_at, reverse=True)
    
    @staticmethod
    def mark_as_read(patient_id, provider_id):
        """Mark all messages from a patient as read"""
        for message in db['messages']:
            if (message.patient_id == patient_id and 
                message.provider_id == provider_id and 
                message.sender_type == 'patient'):
                message.is_read = True
    
    @staticmethod
    def get_recent_by_provider(provider_id, limit=5):
        """Get recent messages for a provider"""
        messages = [m for m in db['messages'] if m.provider_id == provider_id]
        messages = sorted(messages, key=lambda m: m.created_at, reverse=True)
        return messages[:limit]
    
    @staticmethod
    def get_unread_count(provider_id):
        """Get count of unread messages for a provider"""
        return len([m for m in db['messages'] 
                   if m.provider_id == provider_id and 
                   m.sender_type == 'patient' and 
                   not m.is_read])

class HealthInfo:
    """Health information model"""
    def __init__(self, id, title, content, language, created_at=None):
        self.id = id
        self.title = title
        self.content = content
        self.language = language  # 'en' or 'sw'
        self.created_at = created_at or datetime.now()
    
    @staticmethod
    def create(title, content, language):
        """Create new health information"""
        info_id = len(db['health_info']) + 1
        info = HealthInfo(info_id, title, content, language)
        db['health_info'].append(info)
        return info
    
    @staticmethod
    def get_by_language(language):
        """Get health information by language"""
        return [i for i in db['health_info'] if i.language == language]
    
    @staticmethod
    def get_all():
        """Get all health information"""
        return sorted(db['health_info'], key=lambda i: i.created_at, reverse=True)


class UserInteraction:
    """User interaction model for tracking patient journey"""
    def __init__(self, id, patient_id, interaction_type, description, metadata=None, created_at=None):
        self.id = id
        self.patient_id = patient_id
        self.interaction_type = interaction_type  # 'ussd', 'appointment', 'message', 'symptom', 'health_tip'
        self.description = description
        self.metadata = metadata or {}  # Additional data specific to interaction type
        self.created_at = created_at or datetime.now()
    
    @staticmethod
    def create(patient_id, interaction_type, description, metadata=None):
        """
        Create a new user interaction
        
        Args:
            patient_id (int): ID of the patient
            interaction_type (str): Type of interaction ('ussd', 'appointment', 'message', 'symptom', 'health_tip')
            description (str): Description of the interaction
            metadata (dict, optional): Additional data specific to interaction type
            
        Returns:
            UserInteraction: Newly created interaction object
        """
        if 'user_interactions' not in db:
            db['user_interactions'] = []
            
        interaction_id = len(db['user_interactions']) + 1
        interaction = UserInteraction(interaction_id, patient_id, interaction_type, description, metadata)
        db['user_interactions'].append(interaction)
        return interaction
    
    @staticmethod
    def get_by_patient(patient_id):
        """Get all interactions for a patient"""
        if 'user_interactions' not in db:
            db['user_interactions'] = []
        return sorted([i for i in db['user_interactions'] if i.patient_id == patient_id], 
                      key=lambda i: i.created_at)
    
    @staticmethod
    def get_patient_journey(patient_id):
        """
        Get a structured journey map for a patient
        
        Args:
            patient_id (int): ID of the patient
            
        Returns:
            dict: Journey data structured by interaction types and timeline
        """
        interactions = UserInteraction.get_by_patient(patient_id)
        patient = Patient.get_by_id(patient_id)
        
        # Basic journey structure
        journey = {
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'age': patient.age,
                'gender': patient.gender,
                'registration_date': patient.created_at.strftime('%Y-%m-%d'),
                'days_since_registration': (datetime.now() - patient.created_at).days
            },
            'interactions': {
                'ussd': [],
                'appointments': [],
                'messages': [],
                'symptoms': [],
                'health_tips': []
            },
            'timeline': [],
            'statistics': {
                'total_interactions': len(interactions),
                'interaction_by_type': {},
                'avg_interactions_per_month': 0
            }
        }
        
        # Map interactions to their respective categories
        type_map = {
            'ussd': 'ussd',
            'appointment': 'appointments',
            'message': 'messages',
            'symptom': 'symptoms',
            'health_tip': 'health_tips'
        }
        
        type_counts = {}
        
        for interaction in interactions:
            # Add to type-specific list
            interaction_type = interaction.interaction_type
            if interaction_type in type_map:
                journey['interactions'][type_map[interaction_type]].append({
                    'id': interaction.id,
                    'description': interaction.description,
                    'date': interaction.created_at.strftime('%Y-%m-%d'),
                    'time': interaction.created_at.strftime('%H:%M'),
                    'metadata': interaction.metadata
                })
            
            # Add to timeline
            journey['timeline'].append({
                'id': interaction.id,
                'type': interaction_type,
                'description': interaction.description,
                'date': interaction.created_at.strftime('%Y-%m-%d'),
                'time': interaction.created_at.strftime('%H:%M'),
                'timestamp': interaction.created_at.timestamp(),
                'metadata': interaction.metadata
            })
            
            # Count interaction types
            type_counts[interaction_type] = type_counts.get(interaction_type, 0) + 1
            
        # Sort timeline by timestamp
        journey['timeline'] = sorted(journey['timeline'], key=lambda x: x['timestamp'])
        
        # Calculate statistics
        journey['statistics']['interaction_by_type'] = type_counts
        
        # Calculate average interactions per month if user has been registered for at least a week
        days_since_registration = journey['patient']['days_since_registration']
        if days_since_registration >= 7:
            months = max(days_since_registration / 30, 1)  # At least 1 month
            journey['statistics']['avg_interactions_per_month'] = round(len(interactions) / months, 1)
        
        return journey

class Payment:
    """Payment model for M-Pesa transactions"""
    def __init__(self, id, appointment_id, amount, phone_number, mpesa_reference=None, status="pending", payment_method="mpesa", created_at=None, paid_at=None):
        self.id = id
        self.appointment_id = appointment_id
        self.amount = amount
        self.phone_number = phone_number  # Phone number for M-Pesa payment
        self.mpesa_reference = mpesa_reference  # M-Pesa transaction reference
        self.status = status  # pending, completed, failed
        self.payment_method = payment_method  # mpesa, cash, insurance, etc.
        self.created_at = created_at or datetime.now()
        self.paid_at = paid_at  # When payment was confirmed
    
    @staticmethod
    def create(appointment_id, amount, phone_number, payment_method="mpesa"):
        """
        Create a new payment record
        
        Args:
            appointment_id (int): ID of the appointment
            amount (float): Amount to be paid
            phone_number (str): Patient's phone number for M-Pesa
            payment_method (str): Payment method (default: mpesa)
            
        Returns:
            Payment: Newly created payment object
        """
        payment_id = len(db['payments']) + 1
        payment = Payment(payment_id, appointment_id, amount, phone_number, payment_method=payment_method)
        db['payments'].append(payment)
        return payment
    
    @staticmethod
    def get_by_id(payment_id):
        """Get payment by ID"""
        for payment in db['payments']:
            if payment.id == payment_id:
                return payment
        return None
    
    @staticmethod
    def get_by_appointment(appointment_id):
        """Get payment for an appointment"""
        for payment in db['payments']:
            if payment.appointment_id == appointment_id:
                return payment
        return None
    
    @staticmethod
    def get_all():
        """Get all payments"""
        return sorted(db['payments'], key=lambda p: p.created_at, reverse=True)
    
    @staticmethod
    def update_status(payment_id, status, mpesa_reference=None):
        """
        Update payment status
        
        Args:
            payment_id (int): ID of the payment
            status (str): New status (completed, failed)
            mpesa_reference (str, optional): M-Pesa transaction reference
            
        Returns:
            bool: True if updated, False if not found
        """
        for payment in db['payments']:
            if payment.id == payment_id:
                payment.status = status
                if mpesa_reference:
                    payment.mpesa_reference = mpesa_reference
                if status == "completed":
                    payment.paid_at = datetime.now()
                return True
        return False
    
    @staticmethod
    def generate_payment_summary():
        """
        Generate summary of all payments
        
        Returns:
            dict: Summary statistics
        """
        payments = db['payments']
        total_amount = sum(p.amount for p in payments)
        pending_amount = sum(p.amount for p in payments if p.status == "pending")
        completed_amount = sum(p.amount for p in payments if p.status == "completed")
        
        # Calculate amounts by payment method
        mpesa_amount = sum(p.amount for p in payments if p.payment_method == "mpesa")
        cash_amount = sum(p.amount for p in payments if p.payment_method == "cash")
        insurance_amount = sum(p.amount for p in payments if p.payment_method == "insurance")
        
        # Calculate completed amounts by payment method
        mpesa_completed = sum(p.amount for p in payments if p.payment_method == "mpesa" and p.status == "completed")
        cash_completed = sum(p.amount for p in payments if p.payment_method == "cash" and p.status == "completed")
        insurance_completed = sum(p.amount for p in payments if p.payment_method == "insurance" and p.status == "completed")
        
        return {
            'total_count': len(payments),
            'pending_count': len([p for p in payments if p.status == "pending"]),
            'completed_count': len([p for p in payments if p.status == "completed"]),
            'failed_count': len([p for p in payments if p.status == "failed"]),
            'total_amount': total_amount,
            'pending_amount': pending_amount,
            'completed_amount': completed_amount,
            'payment_methods': {
                'mpesa': {
                    'count': len([p for p in payments if p.payment_method == "mpesa"]),
                    'amount': mpesa_amount,
                    'completed_amount': mpesa_completed
                },
                'cash': {
                    'count': len([p for p in payments if p.payment_method == "cash"]),
                    'amount': cash_amount,
                    'completed_amount': cash_completed
                },
                'insurance': {
                    'count': len([p for p in payments if p.payment_method == "insurance"]),
                    'amount': insurance_amount,
                    'completed_amount': insurance_completed
                }
            }
        }

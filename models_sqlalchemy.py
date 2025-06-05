from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))  # Increased length to 256 for scrypt hashes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    provider = db.relationship('Provider', backref='user', uselist=False, lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        return cls.query.filter_by(username=username).first()
        
    @classmethod
    def username_exists(cls, username):
        """Check if username exists"""
        return cls.query.filter_by(username=username).first() is not None
        
    @classmethod
    def email_exists(cls, email):
        """Check if email exists"""
        return cls.query.filter_by(email=email).first() is not None

class Provider(db.Model):
    __tablename__ = 'providers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))
    license_number = db.Column(db.String(50))
    languages = db.Column(ARRAY(db.String(20)))
    location = db.Column(db.String(200))
    coordinates = db.Column(JSONB)  # Store as {'lat': float, 'lng': float}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='provider', lazy=True)
    prescriptions = db.relationship('Prescription', backref='provider', lazy=True)
    
    @classmethod
    def get_by_user_id(cls, user_id):
        """Get provider by user ID"""
        return cls.query.filter_by(user_id=user_id).first()

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    location = db.Column(db.String(200))
    coordinates = db.Column(JSONB)  # Store as {'lat': float, 'lng': float}
    language = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True)
    
    @classmethod
    def get_count(cls):
        """Get total number of patients"""
        return cls.query.count()
        
    @classmethod
    def get_recent(cls, limit=5):
        """Get most recent patients"""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()
        
    @classmethod
    def get_by_id(cls, patient_id):
        """Get patient by ID"""
        return cls.query.get(patient_id)
        
    @classmethod
    def get_all(cls):
        """Get all patients ordered by creation date (newest first)"""
        return cls.query.order_by(cls.created_at.desc()).all()

class HealthInfo(db.Model):
    __tablename__ = 'health_info_articles'  # Changed to avoid conflict with patient health info
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    language = db.Column(db.String(20), default='en')
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def create(cls, title, content, language='en', category=None, is_published=True):
        """Create a new health information article"""
        article = cls(
            title=title,
            content=content,
            language=language,
            category=category,
            is_published=is_published
        )
        db.session.add(article)
        db.session.commit()
        return article
    
    @classmethod
    def get_all(cls, published_only=True):
        """Get all health info articles, optionally filtered by published status"""
        query = cls.query
        if published_only:
            query = query.filter_by(is_published=True)
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_by_id(cls, info_id, published_only=True):
        """Get health info article by ID, optionally filtered by published status"""
        query = cls.query
        if published_only:
            query = query.filter_by(is_published=True)
        return query.filter_by(id=info_id).first()
    
    @classmethod
    def get_by_category(cls, category, published_only=True):
        """Get health info articles by category"""
        query = cls.query.filter_by(category=category)
        if published_only:
            query = query.filter_by(is_published=True)
        return query.order_by(cls.created_at.desc()).all()
    
    def update(self, **kwargs):
        """Update health info article with provided fields"""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def toggle_publish(self):
        """Toggle the published status of the article"""
        self.is_published = not self.is_published
        db.session.commit()
        return self.is_published
    
    def delete(self):
        """Delete the health info article"""
        db.session.delete(self)
        db.session.commit()
        return True

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    price = db.Column(db.Float)
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, waived
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reminder_sent = db.Column(db.Boolean, default=False)
    
    # Relationships
    payments = db.relationship('Payment', backref='appointment', lazy=True)
    
    @classmethod
    def get_count_by_status(cls, provider_id, status):
        """Get count of appointments by status for a provider"""
        return cls.query.filter_by(provider_id=provider_id, status=status).count()
        
    @classmethod
    def get_recent_by_provider(cls, provider_id, limit=5):
        """Get most recent appointments for a provider"""
        return cls.query.filter_by(provider_id=provider_id)\
                       .order_by(cls.date.desc(), cls.time.desc())\
                       .limit(limit).all()
                       
    @classmethod
    def get_by_id(cls, appointment_id):
        """Get appointment by ID"""
        return cls.query.get(appointment_id)
        
    @classmethod
    def get_by_provider(cls, provider_id):
        """Get all appointments for a provider"""
        return cls.query.filter_by(provider_id=provider_id).all()

class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medication_details = db.Column(JSONB)  # List of medication details
    instructions = db.Column(db.Text)
    collection_method = db.Column(db.String(20), default='pharmacy_pickup')
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id'))
    status = db.Column(db.String(20), default='pending')  # pending, filled, dispensed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pharmacy = db.relationship('Pharmacy', backref='prescriptions', lazy=True)

    @classmethod
    def get_by_provider(cls, provider_id):
        """Get all prescriptions for a specific provider"""
        return cls.query.filter_by(provider_id=provider_id)\
                       .order_by(cls.created_at.desc())\
                       .all()

class Pharmacy(db.Model):
    __tablename__ = 'pharmacies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    coordinates = db.Column(JSONB)  # Store as {'lat': float, 'lng': float}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20))
    mpesa_reference = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    payment_method = db.Column(db.String(20), default='mpesa')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    @classmethod
    def get_all(cls):
        """Get all payments ordered by creation date (newest first)"""
        return cls.query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def generate_payment_summary(cls):
        """Generate payment summary with payment methods breakdown"""
        from sqlalchemy import func, case
        
        # Initialize summary with default values
        summary = {
            'payment_methods': {
                'mpesa': {
                    'amount': 0,
                    'count': 0,
                    'completed_amount': 0
                },
                'cash': {
                    'amount': 0,
                    'count': 0,
                    'completed_amount': 0
                },
                'card': {
                    'amount': 0,
                    'count': 0,
                    'completed_amount': 0
                },
                'insurance': {
                    'amount': 0,
                    'count': 0,
                    'completed_amount': 0
                }
            },
            'total_revenue': 0,
            'pending_payments': 0,
            'completed_payments': 0
        }
        
        # Get total revenue and payment method breakdown for completed payments
        completed_payments = cls.query.filter_by(status='completed').all()
        
        for payment in completed_payments:
            method = payment.payment_method.lower()
            if method in summary['payment_methods']:
                summary['payment_methods'][method]['amount'] += float(payment.amount)
                summary['payment_methods'][method]['count'] += 1
                summary['payment_methods'][method]['completed_amount'] += float(payment.amount)
        
        # Get pending payments count
        pending_count = cls.query.filter_by(status='pending').count()
        summary['pending_payments'] = pending_count
        
        # Get completed payments count and total revenue
        completed_count = len(completed_payments)
        summary['completed_payments'] = completed_count
        
        # Calculate total revenue from completed payments
        total_revenue = sum(float(p.amount) for p in completed_payments)
        summary['total_revenue'] = total_revenue
        
        # Update payment methods with pending amounts if needed
        pending_payments = cls.query.filter_by(status='pending').all()
        for payment in pending_payments:
            method = payment.payment_method.lower()
            if method in summary['payment_methods']:
                summary['payment_methods'][method]['amount'] += float(payment.amount)
                summary['payment_methods'][method]['count'] += 1
        
        return summary

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)  # 'patient' or 'provider'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    provider = db.relationship('Provider', backref='messages', lazy=True)
    patient = db.relationship('Patient', backref='messages', lazy=True)
    
    @classmethod
    def get_unread_count(cls, provider_id):
        """Get count of unread messages for a provider"""
        return cls.query.filter_by(provider_id=provider_id, is_read=False).count()
        
    @classmethod
    def get_recent_by_provider(cls, provider_id, limit=5):
        """Get most recent messages for a provider"""
        return cls.query.filter_by(provider_id=provider_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit).all()
                       
    @classmethod
    def get_conversations(cls, provider_id):
        """Get all conversations for a provider with latest message and unread count"""
        from sqlalchemy import func, desc
        
        # Get the latest message for each patient
        subquery = db.session.query(
            Message.patient_id,
            func.max(Message.created_at).label('latest_message_time')
        ).filter(
            Message.provider_id == provider_id
        ).group_by(
            Message.patient_id
        ).subquery()
        
        # Get the full message details for the latest messages
        latest_messages = db.session.query(Message).join(
            subquery,
            (Message.patient_id == subquery.c.patient_id) & 
            (Message.created_at == subquery.c.latest_message_time)
        ).all()
        
        # Get unread counts for each patient
        unread_counts = db.session.query(
            Message.patient_id,
            func.count(Message.id).label('unread_count')
        ).filter(
            Message.provider_id == provider_id,
            Message.is_read == False,
            Message.sender_type == 'patient'
        ).group_by(
            Message.patient_id
        ).all()
        
        unread_counts_dict = {patient_id: count for patient_id, count in unread_counts}
        
        # Get all unique patient IDs from messages
        patient_ids = list({msg.patient_id for msg in latest_messages})
        patients = {p.id: p for p in Patient.query.filter(Patient.id.in_(patient_ids)).all()}
        
        # Build conversations list
        conversations = []
        for msg in latest_messages:
            patient = patients.get(msg.patient_id)
            if patient:
                conversations.append({
                    'patient': patient,
                    'latest_message': msg,
                    'unread_count': unread_counts_dict.get(msg.patient_id, 0)
                })
        
        # Sort by latest message time (newest first)
        conversations.sort(key=lambda x: x['latest_message'].created_at, reverse=True)
        
        return conversations

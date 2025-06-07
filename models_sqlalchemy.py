from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

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
        
    @classmethod
    def get_patient_statistics(cls):
        """Get statistics for the patients dashboard
        
        Returns:
            dict: A dictionary containing patient statistics with the following structure:
                {
                    'locations': {
                        'Nairobi': int,
                        'Mombasa': int,
                        'Other': int
                    },
                    'age_groups': {
                        '0-18': int,
                        '19-30': int,
                        '31-45': int,
                        '46-60': int,
                        '61+': int
                    },
                    'gender_distribution': {
                        'Male': int,
                        'Female': int,
                        'Other': int
                    }
                }
        """
        from collections import defaultdict
        
        # Initialize statistics
        stats = {
            'locations': defaultdict(int),
            'age_groups': {
                '0-18': 0,
                '19-30': 0,
                '31-45': 0,
                '46-60': 0,
                '61+': 0
            },
            'gender_distribution': defaultdict(int)
        }
        
        # Get all patients
        patients = cls.query.all()
        
        for patient in patients:
            # Count by location (simplify to major cities)
            location = patient.location or 'Unknown'
            if 'nairobi' in location.lower():
                stats['locations']['Nairobi'] += 1
            elif 'mombasa' in location.lower():
                stats['locations']['Mombasa'] += 1
            elif 'kisumu' in location.lower():
                stats['locations']['Kisumu'] += 1
            elif 'nakuru' in location.lower():
                stats['locations']['Nakuru'] += 1
            else:
                stats['locations']['Other'] += 1
            
            # Count by age group
            if patient.age is not None:
                if patient.age <= 18:
                    stats['age_groups']['0-18'] += 1
                elif 19 <= patient.age <= 30:
                    stats['age_groups']['19-30'] += 1
                elif 31 <= patient.age <= 45:
                    stats['age_groups']['31-45'] += 1
                elif 46 <= patient.age <= 60:
                    stats['age_groups']['46-60'] += 1
                else:
                    stats['age_groups']['61+'] += 1
            
            # Count by gender
            gender = patient.gender or 'Unknown'
            stats['gender_distribution'][gender] += 1
        
        # Convert defaultdict to regular dict for JSON serialization
        stats['locations'] = dict(stats['locations'])
        stats['gender_distribution'] = dict(stats['gender_distribution'])
        
        return stats

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
        
    @classmethod
    def get_by_patient(cls, patient_id):
        """Get all appointments for a patient, ordered by most recent first"""
        return cls.query.filter_by(patient_id=patient_id)\
                       .order_by(cls.date.desc(), cls.time.desc())\
                       .all()

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
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded, partially_refunded
    payment_method = db.Column(db.String(20), default='mpesa')  # mpesa, cash, card, insurance, bank_transfer
    currency = db.Column(db.String(3), default='KES')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    receipt_sent = db.Column(db.Boolean, default=False)
    receipt_sent_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    payment_metadata = db.Column('metadata', JSONB)  # Store additional payment gateway response data
    
    # Relationships
    refunds = db.relationship('PaymentRefund', backref='payment', lazy=True)
    
    def __init__(self, **kwargs):
        super(Payment, self).__init__(**kwargs)
        if not self.payment_metadata:
            self.payment_metadata = {}
    
    @property
    def is_refundable(self):
        """Check if payment can be refunded"""
        return self.status == 'completed' and self.amount > 0
    
    @property
    def refunded_amount(self):
        """Get total amount refunded"""
        return sum(refund.amount for refund in self.refunds if refund.status == 'completed')
    
    @property
    def remaining_balance(self):
        """Get remaining balance that can be refunded"""
        return self.amount - self.refunded_amount
    
    def update_status(self, status, reference=None):
        """Update payment status and set timestamps"""
        self.status = status
        if status == 'completed' and not self.paid_at:
            self.paid_at = datetime.utcnow()
        if reference and not self.mpesa_reference:
            self.mpesa_reference = reference
        db.session.commit()
        return True
    
    @classmethod
    def get_all(cls):
        """Get all payments ordered by creation date (newest first)"""
        return cls.query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def generate_payment_summary(cls):
        """Generate payment summary with payment methods breakdown
        
        Returns:
            dict: A dictionary containing payment summary with the following structure:
                {
                    'payment_methods': {
                        'mpesa': {'amount': float, 'count': int, 'completed_amount': float},
                        'cash': {'amount': float, 'count': int, 'completed_amount': float},
                        'card': {'amount': float, 'count': int, 'completed_amount': float},
                        'insurance': {'amount': float, 'count': int, 'completed_amount': float}
                    },
                    'total_revenue': float,
                    'pending_amount': float,
                    'completed_amount': float,
                    'pending_count': int,
                    'completed_count': int,
                    'failed_count': int
                }
        """
        from sqlalchemy import func
        
        # Initialize summary with default values
        summary = {
            'payment_methods': {
                'mpesa': {
                    'amount': 0.0,
                    'count': 0,
                    'completed_amount': 0.0
                },
                'cash': {
                    'amount': 0.0,
                    'count': 0,
                    'completed_amount': 0.0
                },
                'card': {
                    'amount': 0.0,
                    'count': 0,
                    'completed_amount': 0.0
                },
                'insurance': {
                    'amount': 0.0,
                    'count': 0,
                    'completed_amount': 0.0
                }
            },
            'total_revenue': 0.0,
            'pending_amount': 0.0,
            'completed_amount': 0.0,
            'pending_count': 0,
            'completed_count': 0,
            'failed_count': 0,
            'refunded_amount': 0.0,
            'refunded_count': 0
        }
        
        # Get all payments grouped by status
        payments = cls.query.all()
        
        # Get all refunds to calculate refunded amounts
        refunds = db.session.query(
            PaymentRefund.payment_id,
            db.func.sum(PaymentRefund.amount).label('total_refunded')
        ).filter(
            PaymentRefund.status == 'completed'
        ).group_by(PaymentRefund.payment_id).all()
        
        # Create a dictionary of payment_id to total refunded amount
        refunds_dict = {refund.payment_id: float(refund.total_refunded) for refund in refunds}
        
        # Calculate total refunded amount and count
        total_refunded = sum(refunds_dict.values())
        summary['refunded_amount'] = total_refunded
        summary['refunded_count'] = len(refunds_dict)
        
        for payment in payments:
            amount = float(payment.amount or 0)
            method = (payment.payment_method or 'cash').lower()
            
            # Ensure method exists in our summary
            if method not in summary['payment_methods']:
                method = 'cash'  # Default to cash if method is unknown
                
            # Update payment method stats
            summary['payment_methods'][method]['amount'] += amount
            summary['payment_methods'][method]['count'] += 1
            
            # Update status-based stats
            if payment.status == 'completed':
                summary['payment_methods'][method]['completed_amount'] += amount
                summary['completed_amount'] += amount
                summary['completed_count'] += 1
            elif payment.status == 'pending':
                summary['pending_amount'] += amount
                summary['pending_count'] += 1
            elif payment.status == 'failed':
                summary['failed_count'] += 1
        
        # Calculate total revenue (only from completed payments)
        summary['total_revenue'] = summary['completed_amount']
        
        return summary

class PaymentRefund(db.Model):
    __tablename__ = 'payment_refunds'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, ForeignKey('payments.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    processed_by = db.Column(db.Integer, ForeignKey('users.id'))
    reference = db.Column(db.String(50))  # External reference/ID from payment processor
    refund_metadata = db.Column('metadata', JSONB)  # Store additional refund details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    processor = relationship('User')
    
    @classmethod
    def create(cls, payment_id, amount, reason=None, processed_by=None, reference=None):
        """Create a new refund record"""
        refund = cls(
            payment_id=payment_id,
            amount=amount,
            reason=reason,
            processed_by=processed_by,
            reference=reference,
            status='pending'
        )
        db.session.add(refund)
        db.session.commit()
        return refund
    
    def update_status(self, status, reference=None):
        """Update refund status"""
        self.status = status
        if status == 'completed' and not self.processed_at:
            self.processed_at = datetime.utcnow()
        if reference and not self.reference:
            self.reference = reference
        db.session.commit()
        return True


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
    def get_conversation(cls, provider_id, patient_id):
        """Get conversation between a provider and a specific patient"""
        return cls.query.filter(
            ((cls.provider_id == provider_id) & (cls.patient_id == patient_id)) |
            ((cls.provider_id == provider_id) & (cls.patient_id == patient_id))
        ).order_by(cls.created_at.asc()).all()
        
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
        
    @classmethod
    def mark_as_read(cls, patient_id, provider_id):
        """
        Mark all unread messages from a patient to a provider as read
        
        Args:
            patient_id (int): The ID of the patient
            provider_id (int): The ID of the provider
            
        Returns:
            int: Number of messages marked as read
        """
        try:
            # Update all unread messages from this patient to this provider
            updated = cls.query.filter_by(
                patient_id=patient_id,
                provider_id=provider_id,
                is_read=False,
                sender_type='patient'  # Only mark patient's messages as read
            ).update({
                'is_read': True
            }, synchronize_session=False)
            
            db.session.commit()
            return updated
            
        except Exception as e:
            db.session.rollback()
            raise e


class LabResult(db.Model):
    """Stores laboratory test results for patients"""
    __tablename__ = 'lab_results'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    test_name = db.Column(db.String(200), nullable=False)
    test_type = db.Column(db.String(100))  # e.g., 'blood', 'urine', 'imaging'
    test_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    result_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    notes = db.Column(db.Text)
    results = db.Column(JSONB)  # Store test results as JSON
    reference_range = db.Column(JSONB)  # Normal reference ranges
    is_abnormal = db.Column(db.Boolean, default=False)
    is_urgent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', backref=db.backref('lab_results', lazy=True))
    provider = db.relationship('Provider', backref=db.backref('ordered_lab_tests', lazy=True))
    
    def to_dict(self):
        """Convert lab result to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'provider_id': self.provider_id,
            'test_name': self.test_name,
            'test_type': self.test_type,
            'test_date': self.test_date.isoformat() if self.test_date else None,
            'result_date': self.result_date.isoformat() if self.result_date else None,
            'status': self.status,
            'notes': self.notes,
            'results': self.results,
            'reference_range': self.reference_range,
            'is_abnormal': self.is_abnormal,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def create(cls, patient_id, provider_id, test_name, test_type=None, results=None, 
              reference_range=None, notes=None, status='pending'):
        """Create a new lab result"""
        lab_result = cls(
            patient_id=patient_id,
            provider_id=provider_id,
            test_name=test_name,
            test_type=test_type,
            results=results or {},
            reference_range=reference_range or {},
            notes=notes,
            status=status
        )
        db.session.add(lab_result)
        db.session.commit()
        return lab_result
    
    @classmethod
    def get_by_patient(cls, patient_id, limit=100):
        """Get all lab results for a specific patient"""
        return cls.query.filter_by(patient_id=patient_id)\
            .order_by(cls.test_date.desc())\
            .limit(limit).all()
    
    @classmethod
    def get_by_provider(cls, provider_id, limit=100):
        """Get all lab results ordered by a specific provider"""
        return cls.query.filter_by(provider_id=provider_id)\
            .order_by(cls.test_date.desc())\
            .limit(limit).all()
    
    def update_results(self, results, reference_range=None, notes=None, status='completed'):
        """Update test results"""
        self.results = results
        if reference_range:
            self.reference_range = reference_range
        if notes is not None:
            self.notes = notes
        self.status = status
        self.result_date = datetime.utcnow()
        db.session.commit()
        return self
    
    def mark_as_abnormal(self, is_abnormal=True):
        """Mark test result as abnormal"""
        self.is_abnormal = is_abnormal
        db.session.commit()
        return self


class UserInteraction(db.Model):
    """
    Tracks user interactions with the system for analytics and user journey mapping
    """
    __tablename__ = 'user_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False)  # e.g., 'message', 'appointment', 'payment', etc.
    description = db.Column(db.String(255))
    interaction_metadata = db.Column('metadata', JSONB)  # Store additional context as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    patient = db.relationship('Patient', backref=db.backref('interactions', lazy=True))
    
    @classmethod
    def create(cls, patient_id, interaction_type, description=None, metadata=None):
        """Create a new user interaction"""
        interaction = cls(
            patient_id=patient_id,
            interaction_type=interaction_type,
            description=description,
            interaction_metadata=metadata or {}
        )
        db.session.add(interaction)
        db.session.commit()
        return interaction
    
    @classmethod
    def get_by_patient(cls, patient_id, limit=100):
        """Get all interactions for a specific patient"""
        return cls.query.filter_by(patient_id=patient_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit)\
                       .all()
    
    def to_dict(self):
        """Convert interaction to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'interaction_type': self.interaction_type,
            'description': self.description,
            'metadata': self.interaction_metadata,  # Using the renamed attribute
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
    @classmethod
    def get_patient_journey(cls, patient_id, limit=100):
        """
        Get the complete journey of a patient including all interactions
        
        Args:
            patient_id (int): The ID of the patient
            limit (int): Maximum number of interactions to return
            
        Returns:
            dict: A dictionary containing the patient's journey data
        """
        from sqlalchemy import desc
        
        # Get all interactions for the patient
        interactions = cls.query.filter_by(patient_id=patient_id)\
                             .order_by(desc(cls.created_at))\
                             .limit(limit)\
                             .all()
        
        # Group interactions by type
        interactions_by_type = {}
        for interaction in interactions:
            if interaction.interaction_type not in interactions_by_type:
                interactions_by_type[interaction.interaction_type] = []
            interactions_by_type[interaction.interaction_type].append(interaction.to_dict())
        
        # Get patient details
        patient = Patient.get_by_id(patient_id)
        
        # Get appointment history
        appointments = []
        if hasattr(Patient, 'appointments'):
            appointments = [{
                'id': appt.id,
                'date': appt.date.isoformat() if appt.date else None,
                'time': appt.time.isoformat() if appt.time else None,
                'status': appt.status,
                'type': 'appointment'
            } for appt in patient.appointments] if patient else []
        
        # Get message history
        messages = []
        if hasattr(Patient, 'messages'):
            messages = [{
                'id': msg.id,
                'content': msg.content[:100] + '...' if msg.content and len(msg.content) > 100 else msg.content,
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
                'type': 'message',
                'sender': msg.sender_type
            } for msg in patient.messages] if patient else []
        
        # Get payment history
        payments = []
        if hasattr(Patient, 'appointments') and patient:
            for appt in patient.appointments:
                for payment in appt.payments:
                    payments.append({
                        'id': payment.id,
                        'amount': payment.amount,
                        'status': payment.status,
                        'created_at': payment.created_at.isoformat() if payment.created_at else None,
                        'type': 'payment',
                        'appointment_id': payment.appointment_id
                    })
        
        return {
            'patient': {
                'id': patient.id,
                'name': patient.name if patient else 'Unknown',
                'phone_number': patient.phone_number if patient else None,
                'age': patient.age if patient else None,
                'gender': patient.gender if patient else None,
                'location': patient.location if patient else None,
                'created_at': patient.created_at.isoformat() if patient and patient.created_at else None
            },
            'interactions': interactions_by_type,
            'appointments': appointments,
            'messages': messages,
            'payments': payments,
            'stats': {
                'total_interactions': len(interactions),
                'appointment_count': len(appointments),
                'message_count': len(messages),
                'payment_count': len(payments)
            }
        }

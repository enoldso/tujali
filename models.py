"""
Database models for Tujali.

All models are SQLAlchemy models backed by the database configured in
DATABASE_URL (PostgreSQL in production, SQLite for local development/tests).
Each model keeps the static helper API (get_by_id, create, ...) that the
views and the USSD handler use, so callers don't talk to the session directly.
"""
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import MutableDict, MutableList
from werkzeug.security import generate_password_hash, check_password_hash  # noqa: F401 (re-exported)

db = SQLAlchemy()

JSONList = MutableList.as_mutable(db.JSON)
JSONDict = MutableDict.as_mutable(db.JSON)


def _save(obj):
    db.session.add(obj)
    db.session.commit()
    return obj


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres between two (lat, lon) points."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * asin(sqrt(a)) * 6371


LANGUAGE_NAMES = {'en': 'english', 'sw': 'swahili', 'fr': 'french', 'om': 'oromo',
                  'so': 'somali', 'am': 'amharic', 'ar': 'arabic'}


def _speaks_any(provider_languages, wanted):
    """True if a provider's language list ("English, Swahili") covers any of
    `wanted` (comma-separated codes like "en" or names like "Swahili")."""
    spoken = (provider_languages or '').lower()
    for lang in str(wanted).split(','):
        lang = lang.strip().lower()
        if lang and LANGUAGE_NAMES.get(lang, lang) in spoken:
            return True
    return False


def _categorize_symptom(symptom):
    text = symptom.lower()
    if any(w in text for w in ['severe', 'unbearable', 'extreme']):
        severity = 'Severe'
    elif any(w in text for w in ['moderate', 'medium']):
        severity = 'Moderate'
    elif any(w in text for w in ['mild', 'slight', 'minor']):
        severity = 'Mild'
    else:
        severity = 'Unknown'

    categories = {
        'respiratory': ['cough', 'breathing', 'chest', 'breath', 'respiratory', 'pneumonia'],
        'digestive': ['stomach', 'diarrhea', 'nausea', 'vomit', 'digest', 'abdominal'],
        'pain': ['pain', 'ache', 'hurt', 'sore', 'headache', 'migraine'],
        'fever': ['fever', 'temperature', 'hot', 'chills', 'cold', 'sweat'],
        'skin': ['rash', 'itching', 'skin', 'lesion', 'bump', 'sore'],
    }
    category = next((c for c, kws in categories.items() if any(k in text for k in kws)), 'other')
    return severity, category


# ---------------------------------------------------------------------------
# Staff users
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # 'super_admin', 'provider', 'finance_manager', 'lab_supervisor', ...
    role = db.Column(db.String(50), nullable=False, default='provider')
    # 'clinical', 'finance', 'laboratory', 'pharmacy', 'administration'
    department = db.Column(db.String(50))
    permissions = db.Column(JSONList, nullable=False, default=list)
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    @property
    def is_active(self):
        return self.is_active_account

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission):
        return self.role == 'super_admin' or permission in (self.permissions or [])

    def can_access_department(self, department):
        if self.role == 'super_admin':
            return True
        return self.department == department or department in (self.permissions or [])

    @staticmethod
    def get_by_role(role):
        return User.query.filter_by(role=role).all()

    @staticmethod
    def get_by_department(department):
        return User.query.filter_by(department=department).all()

    @staticmethod
    def get_by_id(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def create(username, email, password, role='provider', department=None, permissions=None):
        """Create a user. `password` is the plain-text password; it is hashed here."""
        user = User(username=username, email=email, role=role,
                    department=department, permissions=list(permissions or []))
        user.set_password(password)
        return _save(user)

    @staticmethod
    def username_exists(username):
        return User.query.filter_by(username=username).first() is not None

    @staticmethod
    def email_exists(email):
        return User.query.filter_by(email=email).first() is not None

    @staticmethod
    def get_all():
        return User.query.order_by(User.id).all()

    @staticmethod
    def count():
        return User.query.count()


# ---------------------------------------------------------------------------
# Providers and patients
# ---------------------------------------------------------------------------

class Provider(db.Model):
    __tablename__ = 'providers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(150))
    languages = db.Column(db.String(255), default='English')
    location = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    license_number = db.Column(db.String(100))
    phone_number = db.Column(db.String(30))
    years_experience = db.Column(db.Integer)

    user = db.relationship('User', backref='providers')

    @property
    def coordinates(self):
        if self.latitude is None or self.longitude is None:
            return None
        return (self.latitude, self.longitude)

    @staticmethod
    def get_by_user_id(user_id):
        return Provider.query.filter_by(user_id=user_id).order_by(Provider.id).first()

    @staticmethod
    def get_by_id(provider_id):
        try:
            return db.session.get(Provider, int(provider_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_all():
        return Provider.query.order_by(Provider.id).all()

    @staticmethod
    def create(user_id, full_name, specialization, license_number, phone_number, location,
               years_experience, languages='English', coordinates=None):
        provider = Provider(user_id=user_id, name=full_name, specialization=specialization,
                            license_number=license_number, phone_number=phone_number,
                            location=location, years_experience=years_experience,
                            languages=languages)
        if coordinates:
            provider.latitude, provider.longitude = coordinates
        return _save(provider)

    @staticmethod
    def get_by_location(patient_coords, max_distance=50, specialization=None, languages=None):
        """Providers within max_distance km of patient_coords, nearest first.

        Each returned provider has a transient `distance` attribute (km).
        """
        if not patient_coords:
            return Provider.get_all()

        nearby = []
        for provider in Provider.query.filter(Provider.latitude.isnot(None),
                                              Provider.longitude.isnot(None)).all():
            distance = haversine(patient_coords[0], patient_coords[1],
                                 provider.latitude, provider.longitude)
            if distance > max_distance:
                continue
            if specialization and specialization not in (provider.specialization or ''):
                continue
            if languages and not _speaks_any(provider.languages, languages):
                continue
            provider.distance = distance
            nearby.append(provider)
        return sorted(nearby, key=lambda p: p.distance)


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    location = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    language = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    symptoms = db.relationship('Symptom', backref='patient', order_by='Symptom.date',
                               cascade='all, delete-orphan')

    @property
    def coordinates(self):
        if self.latitude is None or self.longitude is None:
            return None
        return (self.latitude, self.longitude)

    @staticmethod
    def create(phone_number, name, age, gender, location, language, coordinates=None):
        patient = Patient(phone_number=phone_number, name=name, age=age, gender=gender,
                          location=location, language=language)
        if coordinates:
            patient.latitude, patient.longitude = coordinates
        return _save(patient)

    @staticmethod
    def get_by_phone(phone_number):
        return Patient.query.filter_by(phone_number=phone_number).first()

    @staticmethod
    def get_by_id(patient_id):
        try:
            return db.session.get(Patient, int(patient_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_all():
        return Patient.query.order_by(Patient.created_at.desc()).all()

    @staticmethod
    def get_recent(limit=5):
        return Patient.query.order_by(Patient.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_count():
        return Patient.query.count()

    def add_symptom(self, symptom, severity=None, category=None, date=None):
        auto_severity, auto_category = _categorize_symptom(symptom)
        entry = Symptom(patient=self, text=symptom, date=date or datetime.now(),
                        severity=severity or auto_severity, category=category or auto_category)
        return _save(entry)

    def update_coordinates(self, latitude, longitude):
        self.latitude, self.longitude = latitude, longitude
        db.session.commit()
        return True

    def find_nearby_providers(self, max_distance=50, specialization=None):
        if not self.coordinates:
            return Provider.get_all()
        return Provider.get_by_location(self.coordinates, max_distance=max_distance,
                                        specialization=specialization, languages=self.language)


class Symptom(db.Model):
    __tablename__ = 'symptoms'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    severity = db.Column(db.String(20))
    category = db.Column(db.String(50))

    def __getitem__(self, key):
        # Symptoms used to be dicts; keep symptom['text'] style access working.
        return getattr(self, key)


# ---------------------------------------------------------------------------
# Appointments, messages, content
# ---------------------------------------------------------------------------

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False, index=True)
    date = db.Column(db.String(20))   # 'DD-MM-YYYY' as captured over USSD
    time = db.Column(db.String(20))
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, completed, cancelled
    price = db.Column(db.Float)
    payment_status = db.Column(db.String(20))  # pending, completed, waived
    notes = db.Column(db.Text)
    source = db.Column(db.String(20), default='web')  # web, ussd
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    reminder_sent = db.Column(db.Boolean, nullable=False, default=False)

    patient = db.relationship('Patient')
    provider = db.relationship('Provider')

    @staticmethod
    def create(patient_id, provider_id, date, time, price=None, notes=None, source='web'):
        appointment = Appointment(patient_id=patient_id, provider_id=provider_id, date=date,
                                  time=time, status='pending', price=price,
                                  payment_status='pending' if price else 'waived',
                                  notes=notes, source=source)
        return _save(appointment)

    @staticmethod
    def get_by_id(appointment_id):
        try:
            return db.session.get(Appointment, int(appointment_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_all():
        return Appointment.query.order_by(Appointment.created_at.desc()).all()

    @staticmethod
    def get_by_patient(patient_id):
        return Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.id).all()

    @staticmethod
    def get_by_provider(provider_id):
        return (Appointment.query.filter_by(provider_id=provider_id)
                .order_by(Appointment.created_at.desc()).all())

    @staticmethod
    def get_recent_by_provider(provider_id, limit=5):
        return (Appointment.query.filter_by(provider_id=provider_id)
                .order_by(Appointment.created_at.desc()).limit(limit).all())

    @staticmethod
    def get_count_by_status(provider_id, status):
        return Appointment.query.filter_by(provider_id=provider_id, status=status).count()

    @staticmethod
    def update_status(appointment_id, status, payment_status=None):
        appointment = Appointment.get_by_id(appointment_id)
        if not appointment:
            return False
        appointment.status = status
        if payment_status:
            appointment.payment_status = payment_status
        db.session.commit()
        return True


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'patient' or 'provider'
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    patient = db.relationship('Patient')

    @staticmethod
    def create(provider_id, patient_id, content, sender_type):
        return _save(Message(provider_id=provider_id, patient_id=patient_id,
                             content=content, sender_type=sender_type))

    @staticmethod
    def get_conversation(provider_id, patient_id):
        return (Message.query.filter_by(provider_id=provider_id, patient_id=patient_id)
                .order_by(Message.created_at, Message.id).all())

    @staticmethod
    def get_conversations(provider_id):
        messages = (Message.query.filter_by(provider_id=provider_id)
                    .order_by(Message.created_at.desc(), Message.id.desc()).all())
        conversations = {}
        for m in messages:
            conv = conversations.setdefault(m.patient_id, {
                'patient': m.patient, 'latest_message': m, 'unread_count': 0})
            if m.sender_type == 'patient' and not m.is_read:
                conv['unread_count'] += 1
        return sorted(conversations.values(),
                      key=lambda c: c['latest_message'].created_at, reverse=True)

    @staticmethod
    def mark_as_read(patient_id, provider_id):
        (Message.query.filter_by(patient_id=patient_id, provider_id=provider_id,
                                 sender_type='patient', is_read=False)
         .update({'is_read': True}))
        db.session.commit()

    @staticmethod
    def get_recent_by_provider(provider_id, limit=5):
        return (Message.query.filter_by(provider_id=provider_id)
                .order_by(Message.created_at.desc()).limit(limit).all())

    @staticmethod
    def get_unread_count(provider_id):
        return Message.query.filter_by(provider_id=provider_id, sender_type='patient',
                                       is_read=False).count()

    @staticmethod
    def count():
        return Message.query.count()


class HealthInfo(db.Model):
    __tablename__ = 'health_info'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), nullable=False, default='en')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    @staticmethod
    def create(title, content, language):
        return _save(HealthInfo(title=title, content=content, language=language))

    @staticmethod
    def get_by_language(language):
        return HealthInfo.query.filter_by(language=language).order_by(HealthInfo.id).all()

    @staticmethod
    def get_all():
        return HealthInfo.query.order_by(HealthInfo.created_at.desc()).all()


class UserInteraction(db.Model):
    """Patient journey events (USSD use, symptoms, appointments, messages, ...)."""
    __tablename__ = 'user_interactions'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    interaction_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    # `metadata` is reserved by SQLAlchemy, so the attribute is `details`.
    details = db.Column('metadata', JSONDict, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    @staticmethod
    def create(patient_id, interaction_type, description, metadata=None, created_at=None):
        return _save(UserInteraction(patient_id=patient_id, interaction_type=interaction_type,
                                     description=description, details=dict(metadata or {}),
                                     created_at=created_at or datetime.now()))

    @staticmethod
    def get_by_patient(patient_id):
        return (UserInteraction.query.filter_by(patient_id=patient_id)
                .order_by(UserInteraction.created_at).all())

    @staticmethod
    def count_by_patient():
        rows = (db.session.query(UserInteraction.patient_id, db.func.count(UserInteraction.id))
                .group_by(UserInteraction.patient_id).all())
        return dict(rows)

    @staticmethod
    def get_patient_journey(patient_id):
        interactions = UserInteraction.get_by_patient(patient_id)
        patient = Patient.get_by_id(patient_id)
        if patient is None:
            return None

        journey = {
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'age': patient.age,
                'gender': patient.gender,
                'registration_date': patient.created_at.strftime('%Y-%m-%d'),
                'days_since_registration': (datetime.now() - patient.created_at).days,
            },
            'interactions': {'ussd': [], 'appointments': [], 'messages': [],
                             'symptoms': [], 'health_tips': []},
            'timeline': [],
            'statistics': {'total_interactions': len(interactions),
                           'interaction_by_type': {},
                           'avg_interactions_per_month': 0},
        }
        type_map = {'ussd': 'ussd', 'appointment': 'appointments', 'message': 'messages',
                    'symptom': 'symptoms', 'health_tip': 'health_tips'}
        type_counts = {}
        for i in interactions:
            entry = {'id': i.id, 'description': i.description,
                     'date': i.created_at.strftime('%Y-%m-%d'),
                     'time': i.created_at.strftime('%H:%M'),
                     'metadata': i.details}
            if i.interaction_type in type_map:
                journey['interactions'][type_map[i.interaction_type]].append(entry)
            journey['timeline'].append(dict(entry, type=i.interaction_type,
                                             timestamp=i.created_at.timestamp()))
            type_counts[i.interaction_type] = type_counts.get(i.interaction_type, 0) + 1

        journey['timeline'].sort(key=lambda x: x['timestamp'])
        journey['statistics']['interaction_by_type'] = type_counts
        days = journey['patient']['days_since_registration']
        if days >= 7:
            months = max(days / 30, 1)
            journey['statistics']['avg_interactions_per_month'] = round(len(interactions) / months, 1)
        return journey


# ---------------------------------------------------------------------------
# Finance
# ---------------------------------------------------------------------------

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), index=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), index=True)
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(30))
    mpesa_reference = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed
    payment_method = db.Column(db.String(20), nullable=False, default='mpesa')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    paid_at = db.Column(db.DateTime)

    appointment = db.relationship('Appointment')
    bill = db.relationship('Bill', backref='payments')

    @property
    def patient(self):
        if self.appointment is not None:
            return self.appointment.patient
        if self.bill is not None:
            return self.bill.patient
        return None

    @staticmethod
    def create(appointment_id, amount, phone_number, payment_method='mpesa', bill_id=None):
        return _save(Payment(appointment_id=appointment_id, bill_id=bill_id, amount=amount,
                             phone_number=phone_number, payment_method=payment_method or 'mpesa'))

    @staticmethod
    def get_by_id(payment_id):
        try:
            return db.session.get(Payment, int(payment_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_by_appointment(appointment_id):
        return Payment.query.filter_by(appointment_id=appointment_id).first()

    @staticmethod
    def get_all():
        return Payment.query.order_by(Payment.created_at.desc()).all()

    @staticmethod
    def get_by_provider(provider_id):
        """Payments for a provider's appointments or bills, newest first."""
        return (Payment.query
                .outerjoin(Appointment, Payment.appointment_id == Appointment.id)
                .outerjoin(Bill, Payment.bill_id == Bill.id)
                .filter(db.or_(Appointment.provider_id == provider_id,
                               Bill.provider_id == provider_id))
                .order_by(Payment.created_at.desc()).all())

    @staticmethod
    def update_status(payment_id, status, mpesa_reference=None):
        payment = Payment.get_by_id(payment_id)
        if not payment:
            return False
        payment.status = status
        if mpesa_reference:
            payment.mpesa_reference = mpesa_reference
        if status == 'completed':
            payment.paid_at = datetime.now()
        db.session.commit()
        return True

    @staticmethod
    def generate_payment_summary(payments=None):
        """Totals by status and method, for `payments` (default: all payments)."""
        if payments is None:
            payments = Payment.query.all()

        def total(method=None, status=None):
            return sum(p.amount for p in payments
                       if (method is None or p.payment_method == method)
                       and (status is None or p.status == status))

        return {
            'total_count': len(payments),
            'pending_count': len([p for p in payments if p.status == 'pending']),
            'completed_count': len([p for p in payments if p.status == 'completed']),
            'failed_count': len([p for p in payments if p.status == 'failed']),
            'total_amount': total(),
            'pending_amount': total(status='pending'),
            'completed_amount': total(status='completed'),
            'payment_methods': {
                m: {'count': len([p for p in payments if p.payment_method == m]),
                    'amount': total(method=m),
                    'completed_amount': total(method=m, status='completed')}
                for m in ('mpesa', 'cash', 'insurance')
            },
        }


class Bill(db.Model):
    __tablename__ = 'bills'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), index=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    items = db.Column(JSONList, nullable=False, default=list)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, partially_paid, paid, cancelled
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    paid_at = db.Column(db.DateTime)

    patient = db.relationship('Patient')

    @staticmethod
    def create(patient_id, provider_id, appointment_id=None):
        return _save(Bill(patient_id=patient_id, provider_id=provider_id,
                          appointment_id=appointment_id, items=[]))

    def add_item(self, item_type, description, amount, quantity=1):
        self.items.append({'type': item_type, 'description': description, 'amount': amount,
                           'quantity': quantity, 'total': amount * quantity})
        self.calculate_total()
        db.session.commit()

    def calculate_total(self):
        self.total_amount = sum(item['total'] for item in self.items)

    @property
    def amount_paid(self):
        return sum(p.amount for p in self.payments if p.status == 'completed')

    @staticmethod
    def get_by_id(bill_id):
        try:
            return db.session.get(Bill, int(bill_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_all():
        return Bill.query.order_by(Bill.created_at.desc()).all()

    @staticmethod
    def get_by_patient(patient_id):
        return Bill.query.filter_by(patient_id=patient_id).order_by(Bill.id).all()

    @staticmethod
    def get_by_provider(provider_id):
        return Bill.query.filter_by(provider_id=provider_id).order_by(Bill.id).all()


# ---------------------------------------------------------------------------
# Clinical services
# ---------------------------------------------------------------------------

class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), index=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    medications = db.Column(JSONList, nullable=False, default=list)
    instructions = db.Column(db.Text)
    delivery_method = db.Column(db.String(20), default='pickup')  # drone, bike, pickup
    delivery_address = db.Column(db.String(255))
    delivery_fee = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, dispensed, delivered, cancelled
    source = db.Column(db.String(20), default='web')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    dispensed_at = db.Column(db.DateTime)

    patient = db.relationship('Patient')
    appointment = db.relationship('Appointment')

    @staticmethod
    def create(patient_id, provider_id, appointment_id, medications, instructions,
               delivery_method='pickup', delivery_address=None, delivery_fee=0.0):
        return _save(Prescription(patient_id=patient_id, provider_id=provider_id,
                                  appointment_id=appointment_id, medications=list(medications),
                                  instructions=instructions, delivery_method=delivery_method,
                                  delivery_address=delivery_address, delivery_fee=delivery_fee))

    @staticmethod
    def get_by_id(prescription_id):
        try:
            return db.session.get(Prescription, int(prescription_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_all():
        return Prescription.query.order_by(Prescription.created_at.desc()).all()

    @staticmethod
    def get_by_patient(patient_id):
        return Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.id).all()

    @staticmethod
    def get_by_provider(provider_id):
        return Prescription.query.filter_by(provider_id=provider_id).order_by(Prescription.id).all()

    @staticmethod
    def update_status(prescription_id, status, dispensed_at=None):
        prescription = Prescription.get_by_id(prescription_id)
        if not prescription or not status:
            return False
        prescription.status = status
        if status == 'dispensed':
            prescription.dispensed_at = dispensed_at or datetime.now()
        db.session.commit()
        return True


class WalkInPatient(db.Model):
    __tablename__ = 'walkin_patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), index=True)
    arrival_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    status = db.Column(db.String(20), nullable=False, default='waiting')  # waiting, in_consultation, completed, cancelled
    priority = db.Column(db.String(20), nullable=False, default='normal')  # urgent, normal, low
    notes = db.Column(db.Text)
    consultation_start = db.Column(db.DateTime)
    consultation_end = db.Column(db.DateTime)

    patient = db.relationship('Patient')

    @staticmethod
    def create(patient_id, provider_id, priority='normal', notes=None):
        return _save(WalkInPatient(patient_id=patient_id, provider_id=provider_id,
                                   arrival_time=datetime.now(), priority=priority or 'normal',
                                   notes=notes))

    @staticmethod
    def get_by_provider(provider_id, status=None):
        query = WalkInPatient.query.filter_by(provider_id=provider_id)
        if status:
            query = query.filter_by(status=status)
        return sorted(query.all(), key=lambda w: (w.priority != 'urgent', w.arrival_time))

    @staticmethod
    def get_by_id(walkin_id):
        try:
            return db.session.get(WalkInPatient, int(walkin_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def count_by_status(status):
        return WalkInPatient.query.filter_by(status=status).count()

    @staticmethod
    def update_status(walkin_id, status):
        walkin = WalkInPatient.get_by_id(walkin_id)
        if not walkin or not status:
            return False
        walkin.status = status
        if status == 'in_consultation':
            walkin.consultation_start = datetime.now()
        elif status == 'completed':
            walkin.consultation_end = datetime.now()
        db.session.commit()
        return True

    @property
    def wait_time(self):
        """Wait time in minutes."""
        end = self.consultation_start or datetime.now()
        return int((end - self.arrival_time).total_seconds() / 60)


class LabTest(db.Model):
    __tablename__ = 'lab_tests'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), index=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    test_name = db.Column(db.String(255), nullable=False)
    test_type = db.Column(db.String(50))  # blood, urine, imaging, other
    status = db.Column(db.String(30), nullable=False, default='ordered')
    cost = db.Column(db.Float, default=0.0)
    instructions = db.Column(db.Text)
    source = db.Column(db.String(20), default='web')
    ordered_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    sample_collected_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    patient = db.relationship('Patient')

    @staticmethod
    def create(patient_id, provider_id, appointment_id, test_name, test_type, cost=0.0, instructions=None):
        return _save(LabTest(patient_id=patient_id, provider_id=provider_id,
                             appointment_id=appointment_id, test_name=test_name,
                             test_type=test_type, cost=cost, instructions=instructions))

    @staticmethod
    def get_by_id(test_id):
        try:
            return db.session.get(LabTest, int(test_id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_all():
        return LabTest.query.order_by(LabTest.ordered_at.desc()).all()

    @staticmethod
    def get_by_patient(patient_id):
        return LabTest.query.filter_by(patient_id=patient_id).order_by(LabTest.id).all()

    @staticmethod
    def get_by_provider(provider_id):
        return LabTest.query.filter_by(provider_id=provider_id).order_by(LabTest.id).all()

    @staticmethod
    def update_status(test_id, status):
        test = LabTest.get_by_id(test_id)
        if not test:
            return False
        test.status = status
        if status == 'sample_collected':
            test.sample_collected_at = datetime.now()
        elif status == 'completed':
            test.completed_at = datetime.now()
        db.session.commit()
        return True


class LabResult(db.Model):
    __tablename__ = 'lab_results'

    id = db.Column(db.Integer, primary_key=True)
    lab_test_id = db.Column(db.Integer, db.ForeignKey('lab_tests.id'), nullable=False,
                            unique=True, index=True)
    results = db.Column(JSONDict, nullable=False, default=dict)
    normal_ranges = db.Column(JSONDict, default=dict)
    notes = db.Column(db.Text)
    technician_name = db.Column(db.String(150))
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    reviewed_by_provider = db.Column(db.Boolean, nullable=False, default=False)

    lab_test = db.relationship('LabTest', backref=db.backref('result', uselist=False))

    @staticmethod
    def create(lab_test_id, results, normal_ranges=None, notes=None, technician_name=None):
        result = LabResult(lab_test_id=lab_test_id, results=dict(results),
                           normal_ranges=dict(normal_ranges or {}), notes=notes,
                           technician_name=technician_name)
        db.session.add(result)
        test = LabTest.get_by_id(lab_test_id)
        if test:
            test.status = 'completed'
            test.completed_at = datetime.now()
        db.session.commit()
        return result

    @staticmethod
    def get_by_lab_test(lab_test_id):
        return LabResult.query.filter_by(lab_test_id=lab_test_id).first()

    @staticmethod
    def get_by_patient(patient_id):
        return (LabResult.query.join(LabTest)
                .filter(LabTest.patient_id == patient_id).order_by(LabResult.id).all())

    def mark_reviewed(self):
        self.reviewed_by_provider = True
        db.session.commit()


# ---------------------------------------------------------------------------
# USSD session state (shared across worker processes)
# ---------------------------------------------------------------------------

class UssdSession(db.Model):
    __tablename__ = 'ussd_sessions'

    session_id = db.Column(db.String(100), primary_key=True)
    phone_number = db.Column(db.String(30), nullable=False)
    state = db.Column(db.String(50), nullable=False, default='start')
    language = db.Column(db.String(10), nullable=False, default='en')
    data = db.Column(db.JSON, nullable=False, default=dict)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

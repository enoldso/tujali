"""Database models.

PostgreSQL in production (DATABASE_URL), SQLite for local development/tests.
"""
import secrets
from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from reference import SPECIALTY_NAMES, SPECIALTY_LABELS, SYNDROME_LABELS

db = SQLAlchemy()


def now():
    return datetime.now()


# ---------------------------------------------------------------------------
# Staff (web dashboard users)
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    """A staff account. Patients never log in to the web; they use USSD."""
    __tablename__ = 'users'

    ROLES = ('admin', 'specialist', 'health_officer')

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    organisation = db.Column(db.String(150))  # e.g. county health department, NGO
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    last_login_at = db.Column(db.DateTime)

    specialist = db.relationship('Specialist', back_populates='user', uselist=False,
                                 cascade='all, delete-orphan')

    @property
    def is_active(self):
        return self.is_active_account

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_label(self):
        return {'admin': 'Administrator', 'specialist': 'Specialist',
                'health_officer': 'Health officer'}.get(self.role, self.role)

    @property
    def initials(self):
        parts = [p for p in self.name.replace('Dr.', '').split() if p]
        return ''.join(p[0] for p in parts[:2]).upper() or '?'


# ---------------------------------------------------------------------------
# Specialists
# ---------------------------------------------------------------------------

class Specialist(db.Model):
    __tablename__ = 'specialists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    specialty = db.Column(db.String(30), nullable=False, index=True)
    license_number = db.Column(db.String(60), nullable=False)
    facility = db.Column(db.String(150))
    county = db.Column(db.String(40), nullable=False, index=True)
    bio = db.Column(db.Text)
    languages = db.Column(db.String(100), nullable=False, default='English, Kiswahili')
    fee_kes = db.Column(db.Integer, nullable=False, default=500)
    offers_phone = db.Column(db.Boolean, nullable=False, default=True)
    offers_in_person = db.Column(db.Boolean, nullable=False, default=False)
    accepting = db.Column(db.Boolean, nullable=False, default=True)  # pause new bookings
    verified = db.Column(db.Boolean, nullable=False, default=False)
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=now)

    user = db.relationship('User', back_populates='specialist')
    availability = db.relationship('Availability', back_populates='specialist',
                                   cascade='all, delete-orphan',
                                   order_by='(Availability.weekday, Availability.start_time)')

    @property
    def display_name(self):
        name = self.user.name
        return name if name.lower().startswith('dr') else f'Dr. {name}'

    @property
    def short_name(self):
        """'Dr. A. Otieno' style, for USSD screens."""
        parts = self.user.name.replace('Dr.', '').replace('Dr ', '').split()
        if len(parts) >= 2:
            return f'Dr. {parts[0][0]}. {parts[-1]}'
        return self.display_name

    @property
    def specialty_name(self):
        return SPECIALTY_NAMES.get(self.specialty, self.specialty)

    @property
    def is_bookable(self):
        return self.verified and self.accepting and self.user.is_active_account

    @property
    def modes_label(self):
        modes = []
        if self.offers_phone:
            modes.append('Phone')
        if self.offers_in_person:
            modes.append('In person')
        return ' & '.join(modes) or 'None'


class Availability(db.Model):
    """Weekly recurring consultation hours."""
    __tablename__ = 'availability'

    WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    id = db.Column(db.Integer, primary_key=True)
    specialist_id = db.Column(db.Integer, db.ForeignKey('specialists.id'), nullable=False, index=True)
    weekday = db.Column(db.Integer, nullable=False)  # 0 = Monday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_minutes = db.Column(db.Integer, nullable=False, default=20)

    specialist = db.relationship('Specialist', back_populates='availability')

    @property
    def weekday_name(self):
        return self.WEEKDAYS[self.weekday]


# ---------------------------------------------------------------------------
# Patients and consultations
# ---------------------------------------------------------------------------

class Patient(db.Model):
    """A USSD user, identified by phone number."""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))  # female, male, other
    county = db.Column(db.String(40), index=True)
    language = db.Column(db.String(5), nullable=False, default='en')
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    last_seen_at = db.Column(db.DateTime, default=now)

    consultations = db.relationship('Consultation', back_populates='patient',
                                    order_by='Consultation.created_at.desc()')

    @property
    def first_name(self):
        return self.name.split()[0] if self.name else ''


def new_reference():
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # no 0/O/1/I confusion
    return 'TJ-' + ''.join(secrets.choice(alphabet) for _ in range(5))


class Consultation(db.Model):
    __tablename__ = 'consultations'

    STATUSES = ('waitlist', 'booked', 'completed', 'cancelled', 'no_show')
    MODES = ('phone', 'in_person')

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(12), unique=True, nullable=False, default=new_reference)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    specialist_id = db.Column(db.Integer, db.ForeignKey('specialists.id'), index=True)
    specialty = db.Column(db.String(30), nullable=False, index=True)
    mode = db.Column(db.String(12), nullable=False, default='phone')
    scheduled_at = db.Column(db.DateTime, index=True)
    status = db.Column(db.String(12), nullable=False, default='booked', index=True)
    complaint = db.Column(db.String(200))
    county = db.Column(db.String(40), index=True)  # patient's county when booking
    fee_kes = db.Column(db.Integer, nullable=False, default=0)
    payment_status = db.Column(db.String(10), nullable=False, default='unpaid')  # unpaid, paid, waived
    payment_ref = db.Column(db.String(40))
    clinical_notes = db.Column(db.Text)  # private to the specialist
    advice = db.Column(db.Text)  # shared with the patient by SMS / USSD
    source = db.Column(db.String(10), nullable=False, default='ussd')
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)
    completed_at = db.Column(db.DateTime)
    # Last automated SMS for this request (call reminder, or "specialist now available").
    notified_at = db.Column(db.DateTime)
    cancelled_by = db.Column(db.String(12))  # patient, specialist, admin

    patient = db.relationship('Patient', back_populates='consultations')
    specialist = db.relationship('Specialist')

    @property
    def specialty_name(self):
        return SPECIALTY_NAMES.get(self.specialty, self.specialty)

    def specialty_label(self, lang='en'):
        return SPECIALTY_LABELS.get(self.specialty, {}).get(lang, self.specialty_name)

    @property
    def mode_label(self):
        return 'Phone call' if self.mode == 'phone' else 'In person'

    @property
    def is_upcoming(self):
        return self.status == 'booked' and self.scheduled_at is not None and self.scheduled_at >= now()


# ---------------------------------------------------------------------------
# Outbreak surveillance
# ---------------------------------------------------------------------------

class SymptomReport(db.Model):
    """Community illness report submitted over USSD."""
    __tablename__ = 'symptom_reports'
    __table_args__ = (db.Index('ix_symptom_reports_county_created', 'county', 'created_at'),)

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), index=True)
    # Salted hash of the reporter's phone: limits repeat reports without storing the number.
    reporter_hash = db.Column(db.String(64), index=True)
    county = db.Column(db.String(40), nullable=False)
    syndrome = db.Column(db.String(20), nullable=False, index=True)
    people_affected = db.Column(db.Integer, nullable=False, default=1)
    danger_signs = db.Column(db.Boolean, nullable=False, default=False)
    source = db.Column(db.String(10), nullable=False, default='ussd')
    created_at = db.Column(db.DateTime, nullable=False, default=now, index=True)

    patient = db.relationship('Patient')

    @property
    def syndrome_label(self):
        return SYNDROME_LABELS.get(self.syndrome, {}).get('en', self.syndrome)


class HealthAlert(db.Model):
    """Public health message shown on USSD (and optionally sent by SMS)."""
    __tablename__ = 'health_alerts'

    LEVELS = ('advisory', 'warning', 'emergency')

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60), nullable=False)
    message_en = db.Column(db.String(320), nullable=False)
    message_sw = db.Column(db.String(320))
    county = db.Column(db.String(40), index=True)  # None = nationwide
    syndrome = db.Column(db.String(20))
    level = db.Column(db.String(12), nullable=False, default='advisory')
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    expires_at = db.Column(db.DateTime)
    sms_recipients = db.Column(db.Integer, nullable=False, default=0)

    created_by = db.relationship('User')

    def message(self, lang='en'):
        return self.message_sw if lang == 'sw' and self.message_sw else self.message_en

    @property
    def is_live(self):
        return self.active and (self.expires_at is None or self.expires_at > now())

    @staticmethod
    def live_for_county(county):
        query = HealthAlert.query.filter(
            HealthAlert.active.is_(True),
            db.or_(HealthAlert.expires_at.is_(None), HealthAlert.expires_at > now()),
            db.or_(HealthAlert.county.is_(None), HealthAlert.county == county))
        return query.order_by(HealthAlert.created_at.desc()).all()


# ---------------------------------------------------------------------------
# Messaging and USSD state
# ---------------------------------------------------------------------------

class SmsMessage(db.Model):
    __tablename__ = 'sms_messages'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    body = db.Column(db.String(480), nullable=False)
    purpose = db.Column(db.String(30))  # booking, cancellation, advice, alert, ...
    status = db.Column(db.String(10), nullable=False, default='queued')  # sent, failed, logged
    provider_ref = db.Column(db.String(80))
    error = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=now, index=True)


class UssdSession(db.Model):
    __tablename__ = 'ussd_sessions'

    session_id = db.Column(db.String(100), primary_key=True)
    phone = db.Column(db.String(20), nullable=False)
    state = db.Column(db.String(40), nullable=False, default='start')
    language = db.Column(db.String(5), nullable=False, default='en')
    data = db.Column(db.JSON, nullable=False, default=dict)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)

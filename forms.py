import re

from flask_wtf import FlaskForm
from wtforms import (BooleanField, IntegerField, PasswordField, SelectField, StringField,
                     TextAreaField, TimeField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length, NumberRange, Optional,
                                ValidationError)

from models import Availability, HealthAlert, User
from reference import COUNTIES, SPECIALTIES, SYNDROMES

SPECIALTY_CHOICES = [(code, clinical) for code, clinical, _ in SPECIALTIES]
COUNTY_CHOICES = [(c, c) for c in COUNTIES]


def normalize_phone(value):
    """Kenyan numbers to +2547XXXXXXXX / +2541XXXXXXXX. Returns None if invalid."""
    digits = re.sub(r'[^\d+]', '', value or '')
    if digits.startswith('+254'):
        digits = digits[4:]
    elif digits.startswith('254'):
        digits = digits[3:]
    elif digits.startswith('0'):
        digits = digits[1:]
    if re.fullmatch(r'[17]\d{8}', digits):
        return '+254' + digits
    return None


def kenyan_phone(form, field):
    if field.data:
        normalized = normalize_phone(field.data)
        if not normalized:
            raise ValidationError('Enter a Kenyan mobile number, e.g. 0712 345 678.')
        field.data = normalized


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Keep me signed in')


class JoinForm(FlaskForm):
    """Specialist application. Accounts start unverified."""
    name = StringField('Full name', validators=[DataRequired(), Length(2, 120)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField('Mobile number (for booking alerts)', validators=[DataRequired(), kenyan_phone])
    specialty = SelectField('Specialty', choices=SPECIALTY_CHOICES)
    license_number = StringField('KMPDC licence number', validators=[DataRequired(), Length(3, 60)])
    facility = StringField('Facility / clinic', validators=[Optional(), Length(max=150)])
    county = SelectField('County', choices=COUNTY_CHOICES)
    fee_kes = IntegerField('Consultation fee (KES)', default=500,
                           validators=[DataRequired(), NumberRange(0, 20000)])
    offers_phone = BooleanField('Phone consultations', default=True)
    offers_in_person = BooleanField('In-person visits')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=10)])
    confirm = PasswordField('Confirm password', validators=[EqualTo('password', 'Passwords must match.')])
    attest = BooleanField('I confirm these licence details are accurate and may be verified.',
                          validators=[DataRequired()])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError('An account with this email already exists.')

    def validate_offers_in_person(self, field):
        if not (field.data or self.offers_phone.data):
            raise ValidationError('Offer at least one type of consultation.')


class ProfileForm(FlaskForm):
    phone = StringField('Mobile number', validators=[DataRequired(), kenyan_phone])
    facility = StringField('Facility / clinic', validators=[Optional(), Length(max=150)])
    county = SelectField('County', choices=COUNTY_CHOICES)
    fee_kes = IntegerField('Consultation fee (KES)', validators=[DataRequired(), NumberRange(0, 20000)])
    languages = StringField('Languages', validators=[DataRequired(), Length(max=100)])
    bio = TextAreaField('Short bio', validators=[Optional(), Length(max=600)])
    offers_phone = BooleanField('Phone consultations')
    offers_in_person = BooleanField('In-person visits')
    accepting = BooleanField('Accepting new bookings')


class AvailabilityForm(FlaskForm):
    weekday = SelectField('Day', coerce=int,
                          choices=list(enumerate(Availability.WEEKDAYS)))
    start_time = TimeField('From', validators=[DataRequired()])
    end_time = TimeField('To', validators=[DataRequired()])
    slot_minutes = SelectField('Slot length', coerce=int, default=20,
                               choices=[(15, '15 min'), (20, '20 min'), (30, '30 min'),
                                        (45, '45 min'), (60, '60 min')])

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError('End time must be after the start time.')


class ConsultationForm(FlaskForm):
    clinical_notes = TextAreaField('Private clinical notes', validators=[Optional(), Length(max=4000)])
    advice = TextAreaField('Advice for the patient (sent by SMS)', validators=[Optional(), Length(max=400)])
    payment_status = SelectField('Payment', choices=[('unpaid', 'Unpaid'), ('paid', 'Paid'),
                                                     ('waived', 'Waived')])
    payment_ref = StringField('M-Pesa reference', validators=[Optional(), Length(max=40)])


class AlertForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=60)])
    message_en = TextAreaField('Message (English)', validators=[DataRequired(), Length(max=320)])
    message_sw = TextAreaField('Message (Kiswahili)', validators=[Optional(), Length(max=320)])
    county = SelectField('Area', choices=[('', 'Nationwide')] + COUNTY_CHOICES)
    syndrome = SelectField('Related illness', choices=[('', 'None')] +
                           [(code, labels['en']) for code, labels, _ in SYNDROMES])
    level = SelectField('Level', choices=[(lvl, lvl.title()) for lvl in HealthAlert.LEVELS])
    expires_in_days = SelectField('Show for', coerce=int, default=14,
                                  choices=[(3, '3 days'), (7, '1 week'), (14, '2 weeks'),
                                           (30, '1 month'), (0, 'Until removed')])
    send_sms = BooleanField('Also SMS registered patients in this area')


class StaffForm(FlaskForm):
    name = StringField('Full name', validators=[DataRequired(), Length(2, 120)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField('Mobile number', validators=[Optional(), kenyan_phone])
    role = SelectField('Role', choices=[('health_officer', 'Health officer'), ('admin', 'Administrator')])
    organisation = StringField('Organisation', validators=[Optional(), Length(max=150)])
    password = PasswordField('Temporary password', validators=[DataRequired(), Length(min=10)])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError('An account with this email already exists.')

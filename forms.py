from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, DecimalField, HiddenField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Optional, NumberRange, EqualTo

class LoginForm(FlaskForm):
    """Login form for healthcare providers"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    """Registration form for healthcare providers"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    specialization = SelectField('Specialization', choices=[
        ('general', 'General Practitioner'),
        ('pediatric', 'Pediatrician'),
        ('internal', 'Internal Medicine'),
        ('emergency', 'Emergency Medicine'),
        ('family', 'Family Medicine'),
        ('gynecology', 'Gynecology'),
        ('dermatology', 'Dermatology'),
        ('cardiology', 'Cardiology'),
        ('orthopedic', 'Orthopedic'),
        ('psychiatry', 'Psychiatry'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    license_number = StringField('Medical License Number', validators=[DataRequired(), Length(min=5, max=50)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    location = StringField('Practice Location', validators=[DataRequired(), Length(min=2, max=100)])
    years_experience = IntegerField('Years of Experience', validators=[DataRequired(), NumberRange(min=0, max=50)])
    submit = SubmitField('Register')

class MessageForm(FlaskForm):
    """Form for sending messages to patients"""
    content = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

class HealthInfoForm(FlaskForm):
    """Form for adding health information"""
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    language = SelectField('Language', choices=[('en', 'English'), ('sw', 'Swahili')], validators=[DataRequired()])
    submit = SubmitField('Add Information')

class HealthTipsForm(FlaskForm):
    """Form for generating AI-powered health tips"""
    patient_id = SelectField('Patient', validators=[DataRequired()])
    custom_prompt = TextAreaField('Additional Context (Optional)', validators=[Optional()])
    language = SelectField('Language', 
                          choices=[('en', 'English'), 
                                  ('sw', 'Swahili'), 
                                  ('fr', 'French'), 
                                  ('or', 'Oromo'),
                                  ('so', 'Somali'),
                                  ('am', 'Amharic')], 
                          validators=[DataRequired()])
    submit = SubmitField('Generate Health Tips')

class HealthEducationForm(FlaskForm):
    """Form for generating AI-powered health education content"""
    topic = StringField('Health Topic', validators=[DataRequired()])
    language = SelectField('Language', 
                          choices=[('en', 'English'), 
                                  ('sw', 'Swahili'), 
                                  ('fr', 'French'),
                                  ('or', 'Oromo'),
                                  ('so', 'Somali'),
                                  ('am', 'Amharic')], 
                          validators=[DataRequired()])
    submit = SubmitField('Generate Content')


class PrescriptionForm(FlaskForm):
    """Form for creating prescriptions"""
    patient_id = SelectField('Patient', validators=[DataRequired()])
    appointment_id = SelectField('Appointment', validators=[Optional()])
    medication_name = StringField('Medication Name', validators=[DataRequired()])
    dosage = StringField('Dosage', validators=[DataRequired()])
    frequency = StringField('Frequency', validators=[DataRequired()])
    duration = StringField('Duration', validators=[DataRequired()])
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    delivery_method = SelectField('Delivery Method', 
                                 choices=[('pickup', 'Physical Pickup'),
                                         ('bike', 'Bike Delivery'),
                                         ('drone', 'Drone Delivery')], 
                                 validators=[DataRequired()])
    delivery_address = TextAreaField('Delivery Address', validators=[Optional()])
    submit = SubmitField('Create Prescription')


class WalkInForm(FlaskForm):
    """Form for registering walk-in patients"""
    patient_id = SelectField('Patient', validators=[DataRequired()])
    priority = SelectField('Priority', 
                          choices=[('normal', 'Normal'),
                                  ('urgent', 'Urgent'),
                                  ('low', 'Low Priority')], 
                          validators=[DataRequired()])
    notes = TextAreaField('Notes/Reason for Visit', validators=[Optional()])
    submit = SubmitField('Register Walk-In')


class QuickPatientForm(FlaskForm):
    """Form for quickly adding new patients"""
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    name = StringField('Full Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=120)])
    gender = SelectField('Gender', 
                        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], 
                        validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    language = SelectField('Preferred Language', 
                          choices=[('en', 'English'), ('sw', 'Swahili'), ('fr', 'French'),
                                  ('or', 'Oromo'), ('so', 'Somali'), ('am', 'Amharic')], 
                          validators=[DataRequired()])
    submit = SubmitField('Add Patient')


class LabTestForm(FlaskForm):
    """Form for ordering lab tests"""
    patient_id = SelectField('Patient', validators=[DataRequired()])
    appointment_id = SelectField('Appointment', validators=[Optional()])
    test_name = StringField('Test Name', validators=[DataRequired()])
    test_type = SelectField('Test Type', 
                           choices=[('blood', 'Blood Test'),
                                   ('urine', 'Urine Test'),
                                   ('imaging', 'Imaging'),
                                   ('other', 'Other')], 
                           validators=[DataRequired()])
    cost = DecimalField('Cost (KSh)', validators=[DataRequired(), NumberRange(min=0)])
    instructions = TextAreaField('Special Instructions', validators=[Optional()])
    submit = SubmitField('Order Test')


class LabResultForm(FlaskForm):
    """Form for recording lab results"""
    lab_test_id = HiddenField('Lab Test ID', validators=[DataRequired()])
    technician_name = StringField('Technician Name', validators=[DataRequired()])
    notes = TextAreaField('Notes/Observations', validators=[Optional()])
    submit = SubmitField('Save Results')


class BillItemForm(FlaskForm):
    """Form for adding items to a bill"""
    item_type = SelectField('Item Type', 
                           choices=[('consultation', 'Consultation'),
                                   ('lab_test', 'Lab Test'),
                                   ('prescription', 'Prescription'),
                                   ('delivery', 'Delivery Fee')], 
                           validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    amount = DecimalField('Amount (KSh)', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)], default=1)
    submit = SubmitField('Add Item')


class PaymentRecordForm(FlaskForm):
    """Form for recording payments"""
    bill_id = SelectField('Bill', validators=[DataRequired()])
    amount = DecimalField('Amount Paid (KSh)', validators=[DataRequired(), NumberRange(min=0)])
    payment_method = SelectField('Payment Method', 
                                choices=[('mpesa', 'M-Pesa'),
                                        ('cash', 'Cash'),
                                        ('insurance', 'Insurance')], 
                                validators=[DataRequired()])
    reference = StringField('Reference/Transaction ID', validators=[Optional()])
    submit = SubmitField('Record Payment')

class UserManagementForm(FlaskForm):
    """Form for creating and managing users"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    role = SelectField('Role', choices=[
        ('provider', 'Healthcare Provider'),
        ('finance', 'Finance Staff'),
        ('lab_tech', 'Lab Technician'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    department = SelectField('Department', choices=[
        ('clinical', 'Clinical'),
        ('finance', 'Finance'),
        ('laboratory', 'Laboratory'),
        ('pharmacy', 'Pharmacy'),
        ('administration', 'Administration')
    ], validators=[DataRequired()])
    permissions = SelectMultipleField('Additional Permissions', choices=[
        ('billing', 'Billing Access'),
        ('payments', 'Payment Management'),
        ('lab_tests', 'Lab Test Management'),
        ('prescriptions', 'Prescription Management'),
        ('user_management', 'User Management'),
        ('reports', 'System Reports')
    ])
    submit = SubmitField('Create User')

class DepartmentForm(FlaskForm):
    """Form for managing departments"""
    name = StringField('Department Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    head_user_id = SelectField('Department Head', validators=[Optional()])
    active = BooleanField('Active', default=True)
    submit = SubmitField('Save Department')

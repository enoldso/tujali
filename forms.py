from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, SelectMultipleField, FieldList, FormField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo, ValidationError, NumberRange

class RegistrationForm(FlaskForm):
    """Registration form for new healthcare providers"""
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
    full_name = StringField('Full Name', validators=[DataRequired()])
    license_number = StringField('Medical License Number', validators=[
        DataRequired(),
        Length(min=5, max=20, message='License number must be between 5 and 20 characters')
    ])
    specialization = StringField('Specialization', validators=[DataRequired()])
    languages = SelectMultipleField('Languages Spoken', 
        choices=[
            ('en', 'English'),
            ('sw', 'Swahili'),
            ('fr', 'French'),
            ('so', 'Somali'),
            ('am', 'Amharic'),
            ('or', 'Oromo')
        ],
        validators=[DataRequired()]
    )
    location = StringField('Practice Location', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        from models import User
        user = User.get_by_username(username.data)
        if user is not None:
            raise ValidationError('Please use a different username.')


class LoginForm(FlaskForm):
    """Login form for healthcare providers"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

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


class WalkInPatientForm(FlaskForm):
    """Form for adding walk-in patients with symptom details"""
    # Basic Information
    name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=15, message='Please enter a valid phone number')
    ])
    age = IntegerField('Age', validators=[
        DataRequired(),
        NumberRange(min=0, max=120, message='Please enter a valid age')
    ])
    gender = SelectField('Gender', choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    ], validators=[DataRequired()])
    
    # Symptom Details
    chief_complaint = TextAreaField('Chief Complaint', validators=[DataRequired()], 
                                  render_kw={"placeholder": "Describe the main symptoms or reason for visit"})
    
    symptom_duration = SelectField('Duration of Symptoms', choices=[
        ('less_than_day', 'Less than a day'),
        ('1-3_days', '1-3 days'),
        ('4-7_days', '4-7 days'),
        ('1-2_weeks', '1-2 weeks'),
        ('more_than_2_weeks', 'More than 2 weeks')
    ], validators=[DataRequired()])
    
    symptom_severity = SelectField('Severity', choices=[
        ('mild', 'Mild - Minor discomfort, no disruption to daily activities'),
        ('moderate', 'Moderate - Noticeable discomfort, some disruption to daily activities'),
        ('severe', 'Severe - Significant pain or impairment, unable to perform daily activities')
    ], validators=[DataRequired()])
    
    symptom_location = SelectField('Location of Symptoms', choices=[
        ('head', 'Head'),
        ('chest', 'Chest'),
        ('abdomen', 'Abdomen'),
        ('back', 'Back'),
        ('arms_legs', 'Arms/Legs'),
        ('pelvic', 'Pelvic'),
        ('all_over', 'All over')
    ], validators=[DataRequired()])
    
    additional_notes = TextAreaField('Additional Notes', 
                                   render_kw={"placeholder": "Any other relevant information about the symptoms"})
    
    submit = SubmitField('Add Patient')


class MedicationForm(FlaskForm):
    """Sub-form for medication details"""
    name = StringField('Medication Name', validators=[DataRequired()])
    dosage = StringField('Dosage (e.g., 500mg, 1 tablet)', validators=[DataRequired()])
    frequency = StringField('Frequency (e.g., Twice daily, Every 6 hours)', validators=[DataRequired()])
    duration = StringField('Duration (e.g., 7 days, 2 weeks)', validators=[DataRequired()])


class PrescriptionForm(FlaskForm):
    """Form for creating prescriptions"""
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    
    # Dynamic list of medications
    medications = FieldList(FormField(MedicationForm), min_entries=1)
    
    instructions = TextAreaField('Additional Instructions', validators=[Optional()])
    
    collection_method = SelectField('Collection Method', 
        choices=[
            ('local_delivery', 'Local Delivery'),
            ('drone_delivery', 'Drone Delivery (where available)'),
            ('pickup', 'Pharmacy Pickup')
        ], 
        validators=[DataRequired()]
    )
    
    pharmacy_id = SelectField('Preferred Pharmacy', coerce=int, validators=[])
    
    submit = SubmitField('Create Prescription')
    
    def __init__(self, *args, **kwargs):
        super(PrescriptionForm, self).__init__(*args, **kwargs)
        
        # Populate patient choices
        from models import Patient
        self.patient_id.choices = [(p.id, f"{p.name} ({p.phone_number})") 
                                 for p in Patient.get_all()]
        
        # Populate pharmacy choices
        from models import Pharmacy, db
        self.pharmacy_id.choices = [(0, 'Any Pharmacy')] + \
                                  [(p.id, f"{p.name} - {p.city}, {p.state}") 
                                   for p in Pharmacy.get_all()]
    
    def validate(self, **kwargs):
        # Standard validation
        if not super(PrescriptionForm, self).validate():
            return False
            
        # Additional validation for pharmacy selection if pickup is chosen
        if self.collection_method.data == 'pickup' and not self.pharmacy_id.data:
            self.pharmacy_id.errors.append('Please select a pharmacy for pickup')
            return False
            
        return True

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo, ValidationError

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

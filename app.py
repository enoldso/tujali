import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError, validate_csrf
import json
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from config import config
from extensions import db as db_ext, migrate, db
# Import models after db initialization to avoid circular imports
from models_sqlalchemy import User, Provider, Patient, Appointment, Message, Payment, PaymentRefund, Prescription, Pharmacy, HealthInfo, UserInteraction, LabResult
from forms import (LoginForm, MessageForm, HealthInfoForm, HealthTipsForm, 
                 HealthEducationForm, RegistrationForm, WalkInPatientForm, 
                 PrescriptionForm, PaymentForm, LabResultForm)
from ussd_handler import ussd_callback
import utils
import ai_service
import mock_ai_service  # Import the mock AI service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Add custom Jinja2 filters
@app.template_filter('from_json')
def from_json(value):
    if not value:
        return {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return {}
    return value

# Initialize extensions
db_ext.init_app(app)
migrate.init_app(app, db_ext)

# Configure CSRF protection
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
app.config['WTF_CSRF_SSL_STRICT'] = False  # For development only

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Add CSRF token to all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

# Error handler for CSRF errors
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning(f'CSRF Error: {e.description}')
    return render_template('errors/csrf_error.html', reason=e.description), 400

def verify_csrf(token):
    """Verify the CSRF token"""
    try:
        validate_csrf(token)
        return True
    except:
        return False

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add template filters
from datetime import datetime

@app.template_filter('now')
def _jinja2_filter_now():
    """Return current datetime for templates"""
# Database initialization is now handled above

# Debug information
print("Application initialized")

# USSD simulator route
@app.route('/ussd_simulator.html')
def ussd_simulator():
    """Serve the USSD simulator HTML page"""
    with open('ussd_simulator.html', 'r') as file:
        simulator_html = file.read()
    return simulator_html

# USSD endpoint
@app.route('/ussd', methods=['POST'])
def ussd():
    """Handle USSD requests from Africa's Talking API"""
    session_id = request.form.get('sessionId')
    service_code = request.form.get('serviceCode')
    phone_number = request.form.get('phoneNumber')
    text = request.form.get('text', '')
    
    # Log USSD request details
    logger.debug(f"USSD Request: {phone_number}, {session_id}, {text}")
    
    # Process USSD request and get response
    response = ussd_callback(session_id, service_code, phone_number, text)
    
    # Log response for debugging
    logger.debug(f"USSD Response: {response}")
    
    return response

# Web routes for provider dashboard
@app.route('/')
def index():
    """Landing page with login option"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/api/check-username')
def check_username():
    """Check if username is available"""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'error': 'Username is required'}), 400
        
    exists = User.username_exists(username)
    return jsonify({'exists': exists})


@app.route('/api/check-email')
def check_email():
    """Check if email is available"""
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email is required'}), 400
        
    exists = User.email_exists(email)
    return jsonify({'exists': exists})


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new healthcare provider"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        if User.username_exists(form.username.data):
            flash('Username already taken. Please choose a different one.', 'danger')
            return render_template('register.html', form=form)
            
        # Check if email already exists
        if User.email_exists(form.email.data):
            flash('Email address is already registered. Please use a different email or log in.', 'danger')
            return render_template('register.html', form=form)
            
        try:
            # Create new user with hashed password
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)  # This will hash the password
            
            # Add user to database session
            db_ext.session.add(user)
            
            # Create provider profile
            provider = Provider(
                user=user,  # This sets up the relationship
                name=form.full_name.data,
                specialization=form.specialization.data,
                license_number=form.license_number.data,
                languages=form.languages.data if isinstance(form.languages.data, list) else [form.languages.data],
                location=form.location.data,
                coordinates=None  # Could be set using geocoding in a real app
            )
            
            # Add provider to database session
            db_ext.session.add(provider)
            
            # Commit both user and provider to the database
            db_ext.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            logger.info(f"New provider registered: {user.username} (ID: {user.id})")
            return redirect(url_for('login'))
            
        except Exception as e:
            db_ext.session.rollback()  # Rollback in case of error
            # Log the full error details including traceback
            logger.error("Error during registration:")
            logger.exception(e)  # This will log the full traceback
            # Log form data (without password) for debugging
            form_data = {k: v for k, v in form.data.items() if k != 'password' and k != 'confirm_password'}
            logger.error(f"Form data: {form_data}")
            # Log SQLAlchemy session state
            logger.error(f"Session new: {db_ext.session.new}")
            logger.error(f"Session dirty: {db_ext.session.dirty}")
            flash(f'An error occurred during registration: {str(e)}', 'danger')
    
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for healthcare providers"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Debug info
        logger.debug(f"Login attempt: {username}")
        
        user = User.get_by_username(username)
        
        if user:
            logger.debug(f"User found: {user.username}")
            
            # Use the User model's check_password method
            if user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(f'Invalid password. Debug info has been logged.', 'danger')
        else:
            logger.debug(f"User not found: {username}")
            flash('Invalid username.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Logout the current user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/add_walkin', methods=['GET', 'POST'])
@login_required
def add_walkin():
    """Add a walk-in patient with detailed symptom information"""
    provider = Provider.get_by_user_id(current_user.id)
    if not provider:
        flash('Provider profile not found', 'danger')
        return redirect(url_for('login'))
    
    form = WalkInPatientForm()
    if form.validate_on_submit():
        try:
            # Create new patient
            patient = Patient(
                name=form.name.data,
                phone_number=form.phone.data,
                age=form.age.data,
                gender=form.gender.data,
            )
            db_ext.session.add(patient)
            db_ext.session.flush()  # To get the patient.id
            
            # Helper function to get choice label from value
            def get_choice_label(choices, value):
                for choice_value, label in choices:
                    if choice_value == value:
                        return label
                return str(value)  # Return the raw value if not found

            # Format symptom details for notes
            symptom_details = {
                'chief_complaint': form.chief_complaint.data,
                'duration': get_choice_label(form.symptom_duration.choices, form.symptom_duration.data),
                'severity': form.symptom_severity.data.split(' - ')[0],
                'location': get_choice_label(form.symptom_location.choices, form.symptom_location.data),
                'additional_notes': form.additional_notes.data
            }
            
            # Create an appointment based on the selected type
            from datetime import datetime, timedelta
            
            if form.schedule_type.data == 'walkin':
                # For walk-ins, create a completed appointment for now
                appointment_date = datetime.now().date()
                appointment_time = datetime.now().time()
                status = 'completed'
                notes = """Walk-in patient. 
                Chief Complaint: {}
                Duration: {}
                Severity: {}
                Location: {}
                Notes: {}""".format(
                    symptom_details['chief_complaint'],
                    symptom_details['duration'],
                    symptom_details['severity'],
                    symptom_details['location'],
                    symptom_details['additional_notes']
                )
            else:
                # For scheduled appointments
                appointment_date = datetime.strptime(form.appointment_date.data, '%Y-%m-%d').date()
                appointment_time = datetime.strptime(form.appointment_time.data, '%H:%M').time()
                status = 'pending'  # Will need confirmation
                notes = """Scheduled appointment. 
                Chief Complaint: {}
                Duration: {}
                Severity: {}
                Location: {}
                Notes: {}""".format(
                    symptom_details['chief_complaint'],
                    symptom_details['duration'],
                    symptom_details['severity'],
                    symptom_details['location'],
                    form.additional_notes.data
                )
            
            # Create the appointment
            appointment = Appointment(
                patient_id=patient.id,
                provider_id=provider.id,
                date=appointment_date,
                time=appointment_time,
                status=status,
                notes=notes
            )
            db_ext.session.add(appointment)
            
            # Add symptom to patient's health record
            health_info = HealthInfo(
                title=f"{symptom_details['severity']} {symptom_details['location']} symptoms",
                content=(
                    f"Chief Complaint: {symptom_details['chief_complaint']}\n"
                    f"Duration: {symptom_details['duration']}\n"
                    f"Severity: {symptom_details['severity']}\n"
                    f"Location: {symptom_details['location']}\n"
                    f"Additional Notes: {symptom_details['additional_notes']}"
                ),
                category='symptom',
                language='en'  # Default language
            )
            db_ext.session.add(health_info)
            
            # Track this interaction
            track_interaction(
                patient_id=patient.id,
                interaction_type='walk_in_registration',
                description='Patient registered via walk-in',
                metadata={
                    'symptom_severity': symptom_details['severity'],
                    'symptom_location': symptom_details['location']
                }
            )
            
            # Commit all changes
            db_ext.session.commit()
            
            flash(f'Walk-in patient {patient.name} added successfully!', 'success')
            logger.info(f'New walk-in patient added: {patient.name} (ID: {patient.id}) with symptoms')
            return redirect(url_for('patient_detail', patient_id=patient.id))
            
        except Exception as e:
            db_ext.session.rollback()
            error_details = str(e)
            logger.error(f'Error adding walk-in patient: {error_details}')
            logger.exception('Error details:')
            flash(f'Error adding walk-in patient: {error_details}. Please check the logs for more details.', 'danger')
    
    # Get unread message count for the sidebar
    unread_count = Message.get_unread_count(provider.id) if provider else 0
    
    return render_template('add_walkin.html', 
                         form=form, 
                         provider=provider,
                         unread_count=unread_count)

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for healthcare providers"""
    provider = Provider.get_by_user_id(current_user.id)
    
    # Get statistics
    total_patients = Patient.get_count()
    pending_appointments = Appointment.get_count_by_status(provider.id, 'pending')
    unread_messages = Message.get_unread_count(provider.id)
    
    # Get recent activity
    recent_patients = Patient.get_recent(5)
    recent_appointments = Appointment.get_recent_by_provider(provider.id, 5)
    recent_messages = Message.get_recent_by_provider(provider.id, 5)
    
    # Get payment summary
    payment_summary = Payment.generate_payment_summary()
    
    return render_template('dashboard.html', 
                          provider=provider,
                          total_patients=total_patients,
                          pending_appointments=pending_appointments,
                          unread_messages=unread_messages,
                          recent_patients=recent_patients,
                          recent_appointments=recent_appointments,
                          recent_messages=recent_messages,
                          payment_summary=payment_summary)

@app.route('/patients')
@login_required
def patients():
    """List all patients with statistics"""
    provider = Provider.get_by_user_id(current_user.id)
    patients_list = Patient.get_all()
    
    # Get patient statistics for charts
    patient_stats = Patient.get_patient_statistics()
    
    return render_template('patients.html', 
                         provider=provider, 
                         patients=patients_list,
                         patient_stats=patient_stats)

@app.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    """View patient details"""
    provider = Provider.get_by_user_id(current_user.id)
    patient = Patient.get_by_id(patient_id)
    
    if not patient:
        flash('Patient not found.', 'danger')
        return redirect(url_for('patients'))
    
    # Get appointments and messages
    appointments = Appointment.get_by_patient(patient_id)
    messages = Message.get_conversation(provider.id, patient_id)
    
    # Get symptom data from user interactions
    symptom_interactions = db_ext.session.query(UserInteraction).filter(
        UserInteraction.patient_id == patient_id,
        UserInteraction.interaction_type == 'symptom_report'
    ).order_by(UserInteraction.created_at.desc()).all()
    
    print(f"Found {len(symptom_interactions)} symptom reports for patient {patient_id}")
    
    # Prepare symptoms data for the template
    symptoms = []
    for interaction in symptom_interactions:
        symptom_data = {
            'date': interaction.created_at,
            'text': interaction.description,
            'metadata': {}
        }
        
        # Handle interaction_metadata if it exists
        if hasattr(interaction, 'interaction_metadata') and interaction.interaction_metadata:
            if isinstance(interaction.interaction_metadata, dict):
                symptom_data['metadata'].update(interaction.interaction_metadata)
            else:
                try:
                    # Try to parse as JSON if it's a string
                    metadata = json.loads(interaction.interaction_metadata)
                    if isinstance(metadata, dict):
                        symptom_data['metadata'].update(metadata)
                except (json.JSONDecodeError, TypeError):
                    print(f"Could not parse metadata for interaction {interaction.id}")
                    
        symptoms.append(symptom_data)
        print(f"Symptom: {symptom_data}")
    
    # Get medical history from interactions
    medical_history = db_ext.session.query(UserInteraction).filter(
        UserInteraction.patient_id == patient_id,
        UserInteraction.interaction_type.in_(['medical_history', 'diagnosis', 'treatment'])
    ).order_by(UserInteraction.created_at.desc()).all()
    
    print(f"Found {len(medical_history)} medical history records")
    
    # Get recent lab results for the patient (most recent 5)
    lab_results = LabResult.query.filter_by(
        patient_id=patient_id
    ).order_by(
        LabResult.result_date.desc()
    ).limit(5).all()
    
    return render_template('patient_detail.html', 
                          provider=provider,
                          patient=patient,
                          appointments=appointments,
                          messages=messages,
                          symptoms=symptoms,
                          medical_history=medical_history,
                          lab_results=lab_results)

@app.route('/appointments')
@login_required
def appointments():
    """List and manage appointments with calendar view"""
    provider = Provider.get_by_user_id(current_user.id)
    
    # Get all appointments for the provider
    appointment_list = Appointment.query.filter_by(provider_id=provider.id).order_by(Appointment.date.asc(), Appointment.time.asc()).all()
    
    # Prepare calendar events in FullCalendar format
    calendar_events = []
    for appt in appointment_list:
        # Skip if date or time is None
        if not appt.date or not appt.time:
            continue
            
        # Combine date and time
        start_datetime = datetime.combine(appt.date, appt.time)
        end_datetime = start_datetime + timedelta(minutes=30)  # Default 30-minute appointment
        
        # Determine event color based on status
        status_colors = {
            'pending': '#ffc107',    # Yellow
            'confirmed': '#198754',  # Green
            'completed': '#0dcaf0',  # Cyan
            'cancelled': '#dc3545'   # Red
        }
        
        # Get patient name if available
        patient = Patient.query.get(appt.patient_id)
        patient_name = patient.name if patient else f"Patient {appt.patient_id}"
        
        # Create event object
        event = {
            'id': appt.id,
            'title': f"{patient_name} - {appt.status.upper()}",
            'start': start_datetime.isoformat(),
            'end': end_datetime.isoformat(),
            'status': appt.status,
            'patient_id': appt.patient_id,
            'patient_name': patient_name,
            'notes': appt.notes or '',
            'color': status_colors.get(appt.status, '#6c757d'),  # Default gray
            'textColor': '#ffffff',  # White text for better contrast
            'editable': appt.status in ['pending', 'confirmed'],
            'extendedProps': {
                'patient_phone': patient.phone_number if patient else 'N/A'
            }
        }
        calendar_events.append(event)
    
    # Get dates with appointments for the mini-calendar
    appointment_dates = list(set([appt.date for appt in appointment_list if appt.date]))
    
    return render_template('appointments.html', 
                         provider=provider, 
                         appointments=appointment_list,
                         calendar_events=calendar_events,
                         appointment_dates=appointment_dates)

@app.route('/appointment/create', methods=['GET', 'POST'])
@login_required
def create_appointment():
    """Create a new appointment"""
    provider = Provider.get_by_user_id(current_user.id)
    
    if request.method == 'POST':
        try:
            patient_id = request.form.get('patient_id')
            date_str = request.form.get('date')
            time_str = request.form.get('time')
            notes = request.form.get('notes', '')
            
            # Validate required fields
            if not all([patient_id, date_str, time_str]):
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('create_appointment'))
            
            # Parse date and time
            try:
                appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                appointment_time = datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                flash('Invalid date or time format.', 'danger')
                return redirect(url_for('create_appointment'))
            
            # Check for time conflicts
            existing = Appointment.query.filter(
                Appointment.provider_id == provider.id,
                Appointment.date == appointment_date,
                Appointment.time == appointment_time,
                Appointment.status.in_(['pending', 'confirmed'])
            ).first()
            
            if existing:
                flash('There is already an appointment scheduled at this time.', 'danger')
                return redirect(url_for('create_appointment'))
            
            # Create new appointment
            appointment = Appointment(
                patient_id=patient_id,
                provider_id=provider.id,
                date=appointment_date,
                time=appointment_time,
                status='pending',
                notes=notes
            )
            
            db_ext.session.add(appointment)
            db_ext.session.commit()
            
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('appointments'))
            
        except Exception as e:
            db_ext.session.rollback()
            app.logger.error(f"Error creating appointment: {str(e)}")
            flash('An error occurred while creating the appointment.', 'danger')
    
    # Get patients for the dropdown
    patients = Patient.query.order_by(Patient.name).all()
    return render_template('create_appointment.html', 
                         provider=provider, 
                         patients=patients,
                         min_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/appointment/update', methods=['POST'])
@login_required
def update_appointment():
    """Update appointment status or details"""
    provider = Provider.get_by_user_id(current_user.id)
    appointment_id = request.form.get('appointment_id')
    status = request.form.get('status')
    
    if not appointment_id or not status:
        return jsonify({'success': False, 'message': 'Appointment ID and status are required.'}), 400
    
    try:
        appointment = Appointment.query.get(int(appointment_id))
        if not appointment:
            return jsonify({'success': False, 'message': 'Appointment not found.'}), 404
            
        if appointment.provider_id != provider.id:
            return jsonify({'success': False, 'message': 'Unauthorized.'}), 403
        
        # Update status
        appointment.status = status
        
        # If completing an appointment, set the completion time
        if status == 'completed':
            appointment.completed_at = datetime.utcnow()
        
        db_ext.session.commit()
        
        # Track this interaction
        track_interaction(
            patient_id=appointment.patient_id,
            interaction_type='appointment_status_update',
            description=f'Appointment status changed to {status}',
            metadata={
                'appointment_id': appointment.id,
                'previous_status': appointment.status,
                'new_status': status,
                'provider_id': provider.id
            }
        )
        
        return jsonify({
            'success': True, 
            'message': 'Appointment updated successfully.',
            'appointment': {
                'id': appointment.id,
                'status': appointment.status,
                'status_display': appointment.status.capitalize(),
                'status_badge': f'<span class="badge bg-{"success" if status == "completed" else "warning" if status == "pending" else "danger" if status == "cancelled" else "info"}">{appointment.status.capitalize()}</span>'
            }
        })
        
    except Exception as e:
        db_ext.session.rollback()
        app.logger.error(f"Error updating appointment: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update appointment.'}), 500

@app.route('/messages')
@login_required
def messages():
    """Message center for provider"""
    provider = Provider.get_by_user_id(current_user.id)
    conversations = Message.get_conversations(provider.id)
    return render_template('messages.html', provider=provider, conversations=conversations)

@app.route('/messages/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def patient_messages(patient_id):
    """Messages with a specific patient"""
    provider = Provider.get_by_user_id(current_user.id)
    patient = Patient.get_by_id(patient_id)
    
    if not patient:
        flash('Patient not found.', 'danger')
        return redirect(url_for('messages'))
    
    if request.method == 'POST':
        content = request.form.get('message')
        if content:
            Message.create(provider.id, patient_id, content, 'provider')
            flash('Message sent.', 'success')
        else:
            flash('Message cannot be empty.', 'warning')
    
    # Mark messages as read
    Message.mark_as_read(patient_id, provider.id)
    
    messages_list = Message.get_conversation(provider.id, patient_id)
    return render_template('messages.html', 
                          provider=provider,
                          patient=patient,
                          messages=messages_list,
                          active_patient_id=patient_id,
                          conversations=Message.get_conversations(provider.id))

@app.route('/health-info', methods=['GET', 'POST'])
@login_required
def health_info():
    """Manage health information content"""
    provider = Provider.get_by_user_id(current_user.id)
    form = HealthInfoForm()
    
    if form.validate_on_submit():
        HealthInfo.create(form.title.data, form.content.data, form.language.data)
        flash('Health information added successfully.', 'success')
        return redirect(url_for('health_info'))
    elif request.method == 'POST':
        flash('All fields are required.', 'warning')
    
    info_list = HealthInfo.get_all()
    return render_template('health_info.html', form=form, info_list=info_list, provider=provider)

@app.route('/symptom-dashboard')
@login_required
def symptom_dashboard():
    """Interactive Health Symptom Visualization Dashboard with Enhanced Tracking"""
    provider = Provider.get_by_user_id(current_user.id)
    patients = Patient.get_all()
    
    # Enhanced symptom categories with more specific keywords and metadata
    symptom_categories = {
        'respiratory': {
            'keywords': ['cough', 'breath', 'wheeze', 'sneeze', 'congest', 'phlegm', 'mucus', 
                        'nasal', 'runny nose', 'stuffy nose', 'shortness of breath', 'sob',
                        'difficulty breathing', 'chest tightness', 'wheezing', 'sore throat',
                        'throat pain', 'hoarse', 'laryngitis', 'pneumonia', 'bronchitis'],
            'color': '#0d6efd',
            'icon': 'wind'
        },
        'fever': {
            'keywords': ['fever', 'temperature', 'chills', 'sweat', 'hot', 'warm', 'high temp',
                        'feverish', 'running a temperature', 'pyrexia', 'high fever', 'low-grade fever'],
            'color': '#dc3545',
            'icon': 'thermometer'
        },
        'gastrointestinal': {
            'keywords': ['nausea', 'vomit', 'diarrhea', 'constipat', 'stomach', 'belly', 'abdomen',
                        'indigestion', 'heartburn', 'bloat', 'cramp', 'upset stomach', 'stomachache',
                        'stomach pain', 'abdominal pain', 'diarrhoea', 'loose stool', 'vomiting'],
            'color': '#198754',
            'icon': 'activity'
        },
        'pain': {
            'keywords': ['headache', 'migraine', 'pain', 'ache', 'sore', 'hurt', 'throb', 'sting', 
                        'cramp', 'spasm', 'tender', 'tenderness', 'body ache', 'muscle pain',
                        'joint pain', 'back pain', 'neck pain', 'earache', 'toothache'],
            'color': '#fd7e14',
            'icon': 'alert-triangle'
        },
        'fatigue': {
            'keywords': ['tire', 'exhaust', 'fatigue', 'weak', 'letharg', 'drain', 'run down',
                        'low energy', 'weary', 'sleepy', 'drowsy', 'lack of energy'],
            'color': '#6f42c1',
            'icon': 'moon'
        },
        'neurological': {
            'keywords': ['dizzy', 'lightheaded', 'faint', 'numb', 'tingl', 'seizure', 'confus', 
                        'memory loss', 'forget', 'head spin', 'vertigo', 'vision problem',
                        'blurred vision', 'double vision', 'loss of balance', 'coordination'],
            'color': '#20c997',
            'icon': 'alert-circle'
        },
        'skin': {
            'keywords': ['rash', 'itch', 'hive', 'bump', 'lesion', 'sore', 'blister', 'dry skin',
                        'peeling', 'redness', 'swelling', 'inflammation', 'skin irritation',
                        'hives', 'urticaria', 'dermatitis', 'eczema'],
            'color': '#ffc107',
            'icon': 'layers'
        }
    }

    # Initialize data structures
    symptom_data = []
    location_data = {}
    severity_data = {'Mild': 0, 'Moderate': 0, 'Severe': 0, 'Unknown': 0}
    category_counts = {cat: 0 for cat in symptom_categories}
    category_counts['other'] = 0
    
    # Track symptoms for outbreak detection
    from collections import defaultdict
    from datetime import datetime, timedelta
    recent_symptoms = defaultdict(lambda: {'count': 0, 'dates': set()})
    one_week_ago = datetime.utcnow() - timedelta(days=7)

    # Get all health info records with category 'symptom'
    symptom_records = HealthInfo.query.filter_by(category='symptom').all()
    
    for record in symptom_records:
        # Extract symptom details from the content
        content = record.content.lower()
        symptom_text = ''
        symptom_date = record.created_at
        
        # Extract symptom text from the content (first line is usually the main symptom)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if lines:
            symptom_text = lines[0].replace('chief complaint:', '').strip()
            
        if not symptom_text:
            continue
            
        # Extract severity and location from content
        severity = 'Unknown'
        location = 'Not specified'
        for line in lines:
            if 'severity:' in line:
                severity = line.split('severity:')[-1].strip().capitalize()
                if 'mild' in severity.lower():
                    severity = 'Mild'
                elif 'moderate' in severity.lower():
                    severity = 'Moderate'
                elif 'severe' in severity.lower():
                    severity = 'Severe'
            elif 'location:' in line:
                location = line.split('location:')[-1].strip()
        
        # Add to symptom data with structure expected by the template
        symptom_data.append({
            'patient_id': 0,  # Default ID for walk-in patients
            'patient_name': 'Walk-in Patient',
            'symptom': symptom_text,
            'normalized_name': symptom_text.split()[0] if symptom_text else 'unknown',
            'category': 'other',  # Will be updated in the category detection
            'confidence': 0.0,  # Will be calculated
            'severity': severity,
            'location': location,
            'reported_via': 'Walk-in',
            'date': symptom_date,
            'patient_location': location,  # Using symptom location as fallback
            'matched_keywords': [],  # Will be populated
            'raw_data': {
                'content': content,
                'severity': severity,
                'location': location,
                'reported_via': 'Walk-in'
            }
        })
        
        # Update severity data
        if severity in severity_data:
            severity_data[severity] += 1
        else:
            severity_data['Unknown'] += 1
            
        # Update location data with structure expected by the template
        location_key = f"{location} (Patient: {location})"  # Using symptom location for both
        location_data[location_key] = location_data.get(location_key, 0) + 1
            
        # Update recent symptoms for outbreak detection
        if symptom_date >= one_week_ago:
            recent_symptoms[symptom_text]['count'] += 1
            recent_symptoms[symptom_text]['dates'].add(symptom_date.date())
                    # Determine symptom category and confidence
            category = 'other'
            confidence = 0
            matched_keywords = []
            
            # First check for exact matches in the symptom text
            symptom_words = symptom_text.lower().split()
            
            for cat, data in symptom_categories.items():
                for keyword in data['keywords']:
                    # Check if keyword matches any word in the symptom text
                    if any(keyword in word for word in symptom_words):
                        category = cat
                        confidence += 1
                        matched_keywords.append(keyword)
                        break  # Count each category only once per keyword match
            
            # Normalize confidence score (0.0 to 1.0)
            confidence = min(1.0, confidence / 3) if confidence > 0 else 0
            
            # Track for outbreak detection
            symptom_key = f"{category}:{symptom_text.split()[0]}"  # First word as key
            recent_symptoms[symptom_key]['count'] += 1
            recent_symptoms[symptom_key]['dates'].add(symptom_date.date())
            
            # Update severity and category counts
            severity_data[severity] = severity_data.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Get symptom metadata with defaults
            reported_via = 'Walk-in'  # Default for walk-in patients
            
            # Add to symptom data with enhanced metadata for walk-in patients
            symptom_data.append({
                'patient_id': 0,  # Default ID for walk-in patients
                'patient_name': 'Walk-in Patient',
                'symptom': symptom_text,
                'normalized_name': symptom_text.split()[0] if symptom_text else 'unknown',
                'category': category,
                'confidence': confidence,
                'severity': severity,
                'location': location,
                'reported_via': reported_via,
                'date': symptom_date,
                'patient_location': location or 'Unknown',
                'matched_keywords': matched_keywords,
                'raw_data': {
                    'content': content,
                    'severity': severity,
                    'location': location,
                    'reported_via': reported_via,
                    'date': symptom_date.isoformat() if symptom_date else None
                }
            })
            
            # Update location data (using symptom-specific location if available)
            location_key = f"{location} (Walk-in Patient)"
            location_data[location_key] = location_data.get(location_key, 0) + 1
            
            # Track reporting method
            if 'reporting_methods' not in locals():
                reporting_methods = {}
            reporting_methods[reported_via] = reporting_methods.get(reported_via, 0) + 1
    
    # Detect potential outbreaks (symptoms with high frequency in last 7 days)
    outbreak_signals = []
    for symptom_key, data in recent_symptoms.items():
        if not data['dates']:
            continue
            
        days_span = (max(data['dates']) - min(data['dates'])).days + 1
        if days_span <= 7 and data['count'] >= 3:  # At least 3 cases in 7 days
            category, symptom = symptom_key.split(':', 1)
            outbreak_signals.append({
                'symptom': symptom,
                'category': category,
                'count': data['count'],
                'first_seen': min(data['dates']),
                'last_seen': max(data['dates']),
                'severity': 'High' if data['count'] > 5 else 'Medium'
            })
    
    # Sort outbreak signals by count (highest first) and then by most recent
    outbreak_signals.sort(key=lambda x: (-x['count'], x['last_seen']))
    
    # Sort locations by frequency
    sorted_locations = dict(sorted(location_data.items(), 
                                 key=lambda item: item[1], 
                                 reverse=True))
    
    # Prepare time-based data
    time_data = {}
    for entry in symptom_data:
        date_str = entry['date'].strftime('%Y-%m-%d')
        time_data[date_str] = time_data.get(date_str, 0) + 1
    
    # Sort time data chronologically
    sorted_time_data = dict(sorted(time_data.items()))
    
    # Get top 5 symptoms by frequency
    symptom_freq = {}
    for entry in symptom_data:
        symptom = entry['symptom'].lower()
        symptom_freq[symptom] = symptom_freq.get(symptom, 0) + 1
    
    top_symptoms = dict(sorted(symptom_freq.items(), 
                              key=lambda x: x[1], 
                              reverse=True)[:5])
    provider = Provider.get_by_user_id(current_user.id)
    
    # Get all patients for the dropdown
    patients = Patient.get_all()
    
    # Create form with patient choices
    form = HealthTipsForm()
    form.patient_id.choices = [(str(p.id), f"{p.name} ({p.phone_number})") for p in patients]
    
    # Store generated tips
    generated_tips = None
    selected_patient = None
    
    if form.validate_on_submit():
        patient_id = int(form.patient_id.data)
        language = form.language.data
        custom_prompt = form.custom_prompt.data
        
        # Get patient data
        patient = Patient.get_by_id(patient_id)
        selected_patient = patient
        
        if not patient:
            flash('Patient not found.', 'danger')
            return redirect(url_for('health_tips'))
        
        # Prepare patient data for AI
        patient_data = {
            'id': patient.id,
            'name': patient.name,
            'age': patient.age,
            'gender': patient.gender,
            'location': patient.location,
            'language': patient.language
        }
        
        # Get symptoms if available
        symptoms = []
        if hasattr(patient, 'symptoms') and patient.symptoms:
            for symptom_entry in patient.symptoms:
                # Determine symptom category from text
                symptom_text = symptom_entry['text'].lower()
                category = 'other'
                for cat, keywords in {
                    'respiratory': ['cough', 'breathing', 'chest', 'breath', 'respiratory', 'pneumonia'],
                    'digestive': ['stomach', 'diarrhea', 'nausea', 'vomit', 'digest', 'abdominal'],
                    'pain': ['pain', 'ache', 'hurt', 'sore', 'headache', 'migraine'],
                    'fever': ['fever', 'temperature', 'hot', 'chills', 'cold', 'sweat'],
                    'skin': ['rash', 'itching', 'skin', 'lesion', 'bump', 'sore']
                }.items():
                    if any(keyword in symptom_text for keyword in keywords):
                        category = cat
                        break
                
                # Determine severity from text
                severity = 'Unknown'
                if 'severe' in symptom_text or 'unbearable' in symptom_text:
                    severity = 'Severe'
                elif 'mild' in symptom_text or 'slight' in symptom_text:
                    severity = 'Mild'
                elif 'moderate' in symptom_text:
                    severity = 'Moderate'
                
                symptoms.append({
                    'description': symptom_entry['text'],
                    'severity': severity,
                    'category': category,
                    'date': symptom_entry['date']
                })
        
        try:
            # Generate personalized health tips
            logger.debug(f"Generating health tips for patient {patient.id}")
            
            # Due to API quota limitations, we'll use the mock service directly
            # This ensures the feature still works when APIs are unavailable
            generated_tips = mock_ai_service.generate_health_tips(patient_data, symptoms, language)
            logger.debug(f"Successfully generated health tips with mock service")
            flash('Using Health AI Recommendations service (offline mode active).', 'info')
            
            # Store in session for shared with patient
            session['last_generated_tips'] = generated_tips
            session['last_tips_patient_id'] = patient.id
            
            # Log success
            logger.debug(f"Health tips generated: {generated_tips}")
            
            flash('Health tips generated successfully.', 'success')
        except Exception as e:
            logger.error(f"Error generating health tips: {str(e)}")
            flash(f'Error generating health tips: {str(e)}', 'danger')
    
    # Prepare data for the symptom dashboard
    return render_template('symptom_dashboard.html',
                         provider=provider,
                         patients=patients,
                         symptom_data=symptom_data,
                         category_counts=category_counts,
                         severity_data=severity_data,
                         location_data=sorted_locations,
                         time_data=sorted_time_data,
                         top_symptoms=top_symptoms,
                         outbreak_signals=outbreak_signals,
                         total_symptoms=len(symptom_data),
                         unique_symptoms=list(set([s['symptom'] for s in symptom_data])),
                         avg_severity=sum(s.get('severity_level', 0) for s in symptom_data) / len(symptom_data) if symptom_data else 0,
                         top_location=(max(location_data.items(), key=lambda x: x[1]) if location_data else ('None', 0)))

@app.route('/health-tips/share/<int:patient_id>', methods=['POST'])
@login_required
def share_health_tips(patient_id):
    """Share generated health tips with a patient via SMS"""
    provider = Provider.get_by_user_id(current_user.id)
    
    # Check if there are tips in the session
    if 'last_generated_tips' not in session or session.get('last_tips_patient_id') != patient_id:
        flash('No health tips found to share. Please generate tips first.', 'warning')
        return redirect(url_for('health_tips'))
    
    patient = Patient.get_by_id(patient_id)
    if not patient:
        flash('Patient not found.', 'danger')
        return redirect(url_for('health_tips'))
    
    # Get tips from session
    tips = session['last_generated_tips']
    
    # Create a simplified message version for SMS
    if tips and 'health_tips' in tips:
        message = f"Health tips for {patient.name}:\n\n"
        
        # Add health tips
        for i, tip in enumerate(tips['health_tips'], 1):
            message += f"{i}. {tip['title']}:\n{tip['description']}\n\n"
        
        # Add follow-up advice if available
        if 'follow_up' in tips:
            message += f"Follow-up: {tips['follow_up']}"
        
        # Save this as a message
        Message.create(provider.id, patient_id, message, 'provider')
        
        flash('Health tips shared with patient as a message.', 'success')
    else:
        flash('Invalid health tips format.', 'danger')
    
    return redirect(url_for('health_tips'))

@app.route('/health-education', methods=['GET', 'POST'])
@login_required
def health_education():
    """AI-Generated Health Education Content"""
    provider = Provider.get_by_user_id(current_user.id)
    form = HealthEducationForm()
    
    generated_content = None
    
    if form.validate_on_submit():
        topic = form.topic.data
        language = form.language.data
        
        try:
            # Generate health education content
            logger.debug(f"Generating health education content on: {topic}")
            
            # Due to API quota limitations, we'll use the mock service directly
            # This ensures the feature still works when APIs are unavailable
            generated_content = mock_ai_service.generate_health_education(topic, language)
            logger.debug(f"Successfully generated health education content with mock service")
            flash('Using Health Education service (offline mode active).', 'info')
            
            # Store in session for later use
            session['last_education_content'] = generated_content
            
            # Log success
            logger.debug(f"Successfully generated health education content: {generated_content}")
            
            # Optionally save to HealthInfo database
            if generated_content and 'title' in generated_content and 'overview' in generated_content:
                # Create simplified content from the structured data
                title = generated_content['title']
                
                # Combine overview and key points
                content = generated_content['overview'] + "\n\n"
                
                if 'key_points' in generated_content:
                    content += "Key Points:\n"
                    for i, point in enumerate(generated_content['key_points'], 1):
                        content += f"{i}. {point}\n"
                    content += "\n"
                
                if 'prevention' in generated_content:
                    content += "Prevention:\n"
                    for i, tip in enumerate(generated_content['prevention'], 1):
                        content += f"{i}. {tip}\n"
                    content += "\n"
                
                if 'when_to_seek_help' in generated_content:
                    content += f"When to Seek Help:\n{generated_content['when_to_seek_help']}"
                
                # Save to database
                HealthInfo.create(title, content, language)
                
                flash('Health education content generated and saved to the database.', 'success')
            else:
                flash('Health education content generated.', 'success')
                
        except Exception as e:
            logger.error(f"Error generating health education content: {str(e)}")
            flash(f'Error generating health education content: {str(e)}', 'danger')
    
    # Get existing health info
    info_list = HealthInfo.get_all()
    
    return render_template('health_education.html', 
                          provider=provider,
                          form=form,
                          generated_content=generated_content,
                          info_list=info_list)


@app.route('/user-journey')
@login_required
def user_journey_list():
    """List patients for user journey tracking"""
    provider = Provider.get_by_user_id(current_user.id)
    patients = Patient.get_all()
    
    # For each patient, get a count of their interactions
    for patient in patients:
        try:
            interactions = UserInteraction.get_by_patient(patient.id)
            patient.interaction_count = len(interactions) if interactions else 0
        except Exception as e:
            app.logger.error(f"Error getting interactions for patient {patient.id}: {str(e)}")
            patient.interaction_count = 0
    
    return render_template('user_journey_list.html', 
                          provider=provider,
                          patients=patients)


@app.route('/user-journey/<int:patient_id>')
@login_required
def user_journey_detail(patient_id):
    """Display detailed user journey for a specific patient"""
    provider = Provider.get_by_user_id(current_user.id)
    patient = Patient.get_by_id(patient_id)
    
    if not patient:
        flash('Patient not found.', 'danger')
        return redirect(url_for('user_journey_list'))
    
    # Get the full journey data
    journey_data = UserInteraction.get_patient_journey(patient_id)
    
    return render_template('user_journey_detail.html', 
                          provider=provider,
                          patient=patient,
                          journey_data=journey_data)


@app.route('/api/user-journey/<int:patient_id>')
@login_required
def user_journey_api(patient_id):
    """API endpoint for user journey data"""
    journey_data = UserInteraction.get_patient_journey(patient_id)
    return jsonify(journey_data)


# Add interaction tracking hooks to existing functions

def track_interaction(patient_id, interaction_type, description, metadata=None):
    """Helper function to track user interactions"""
    try:
        UserInteraction.create(patient_id, interaction_type, description, metadata)
    except Exception as e:
        logger.error(f"Error tracking interaction: {str(e)}")


# Hook into patient message route to track interactions
old_patient_messages = app.view_functions['patient_messages']

def patient_messages_with_tracking(patient_id):
    """Wrap patient_messages to track interactions"""
    patient = Patient.get_by_id(patient_id)
    
    if request.method == 'POST':
        form = MessageForm()
        if form.validate_on_submit():
            # Track the interaction when a message is sent
            track_interaction(
                patient_id,
                'message',
                f"Message sent to {patient.name}",
                {'content': form.content.data}
            )
    
    return old_patient_messages(patient_id)

app.view_functions['patient_messages'] = patient_messages_with_tracking


# Hook into update_appointment to track interactions
old_update_appointment = app.view_functions['update_appointment']

def update_appointment_with_tracking():
    """Wrap update_appointment to track interactions"""
    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        status = request.form.get('status')
        
        appointment = Appointment.get_by_id(appointment_id)
        if appointment:
            # Track the interaction when an appointment status is updated
            track_interaction(
                appointment.patient_id,
                'appointment',
                f"Appointment status updated to {status}",
                {'appointment_id': appointment_id, 'status': status}
            )
    
    return old_update_appointment()

app.view_functions['update_appointment'] = update_appointment_with_tracking


# Prescription Management Routes

@app.route('/prescriptions')
@login_required
def prescriptions():
    """List all prescriptions"""
    from models_sqlalchemy import Patient, Pharmacy  # Import models here to avoid circular imports
    
    provider = Provider.get_by_user_id(current_user.id)
    if not provider:
        flash('Provider profile not found', 'danger')
        return redirect(url_for('dashboard'))
        
    # Debug: Print provider ID
    print(f"DEBUG: Fetching prescriptions for provider ID: {provider.id}")
    
    # Get all prescriptions for the current provider using SQLAlchemy query directly
    all_prescriptions = Prescription.query.filter_by(provider_id=provider.id)\
                                       .order_by(Prescription.created_at.desc())\
                                       .all()
    
    # Get all patient and pharmacy IDs for the prescriptions
    patient_ids = list({p.patient_id for p in all_prescriptions})
    pharmacy_ids = list({p.pharmacy_id for p in all_prescriptions if p.pharmacy_id is not None})
    
    # Get all patients and pharmacies in a single query
    patients = {p.id: p for p in Patient.query.filter(Patient.id.in_(patient_ids)).all()} if patient_ids else {}
    pharmacies = {p.id: p for p in Pharmacy.query.filter(Pharmacy.id.in_(pharmacy_ids)).all()} if pharmacy_ids else {}
    
    # Debug: Print number of prescriptions found
    print(f"DEBUG: Found {len(all_prescriptions)} prescriptions")
    if all_prescriptions:
        print(f"DEBUG: First prescription: {all_prescriptions[0].__dict__}")
    
    # Get unread message count for sidebar
    unread_count = Message.get_unread_count(provider.id)
    
    return render_template('prescriptions/list.html', 
                         prescriptions=all_prescriptions,
                         provider=provider,
                         patients=patients,
                         pharmacies=pharmacies,
                         unread_count=unread_count)


@app.route('/prescriptions/create', methods=['GET', 'POST'])
@login_required
def create_prescription():
    """Create a new prescription"""
    try:
        print("DEBUG: Entered create_prescription route")
        
        # Temporarily disable CSRF for testing
        from flask_wtf.csrf import CSRFError
        if request.method == 'POST' and 'csrf_token' not in request.form:
            print("WARNING: CSRF token missing, but continuing for testing")
        
        # Get the current provider
        provider = Provider.get_by_user_id(current_user.id)
        if not provider:
            error_msg = 'Provider profile not found. Please complete your provider profile first.'
            print(f"ERROR: {error_msg}")
            flash(error_msg, 'danger')
            return redirect(url_for('dashboard'))
        
        print(f"DEBUG: Found provider with ID: {provider.id}")
        
        # Initialize form
        form = PrescriptionForm()
        
        # Debug CSRF token
        print(f"DEBUG: CSRF Token in form: {form.csrf_token.current_token}")
        print(f"DEBUG: CSRF Token in session: {session.get('_csrf_token')}")
        
        # Populate patient and pharmacy choices
        try:
            form.patient_id.choices = [(0, 'Select Patient')] + [(p.id, p.name) for p in Patient.query.all()]
            form.pharmacy_id.choices = [(0, 'Select Pharmacy')] + [(p.id, p.name) for p in Pharmacy.query.all()]
            print(f"DEBUG: Form initialized with {len(form.patient_id.choices)-1} patients and {len(form.pharmacy_id.choices)-1} pharmacies")
        except Exception as e:
            print(f"ERROR: Failed to populate form choices: {str(e)}")
            flash('Error loading form data. Please try again.', 'danger')
            return redirect(url_for('dashboard'))
        
        if form.validate_on_submit():
            print("DEBUG: Form validation passed")
            print(f"DEBUG: Form data: {request.form}")
            print(f"DEBUG: CSRF Token in form: {form.csrf_token.data}")
            print(f"DEBUG: CSRF Token in session: {session.get('_csrf_token')}")
            
            # Validate patient selection
            if not form.patient_id.data or form.patient_id.data == 0:
                flash('Please select a patient', 'danger')
                return render_template('prescriptions/create.html', form=form, provider=provider)
            
            # Validate pharmacy selection if collection method is 'pharmacy'
            if form.collection_method.data == 'pharmacy' and (not form.pharmacy_id.data or form.pharmacy_id.data == 0):
                flash('Please select a pharmacy for pharmacy collection', 'danger')
                return render_template('prescriptions/create.html', form=form, provider=provider)
            
            try:
                # Prepare medication details
                medications = []
                if not form.medications.data:
                    flash('Please add at least one medication', 'danger')
                    return render_template('prescriptions/create.html', form=form, provider=provider)
                
                for i, med in enumerate(form.medications.data):
                    if not all([med.get('name'), med.get('dosage'), med.get('frequency'), med.get('duration')]):
                        flash(f'Please fill in all fields for medication {i+1}', 'danger')
                        return render_template('prescriptions/create.html', form=form, provider=provider)
                    
                    medications.append({
                        'name': med['name'].strip(),
                        'dosage': med['dosage'].strip(),
                        'frequency': med['frequency'].strip(),
                        'duration': med['duration'].strip()
                    })
                
                print(f"DEBUG: Creating prescription for provider_id={provider.id}, patient_id={form.patient_id.data}")
                print(f"DEBUG: Medications: {medications}")
                
                # Create prescription
                prescription = Prescription(
                    provider_id=provider.id,
                    patient_id=form.patient_id.data,
                    medication_details=medications,
                    instructions=form.instructions.data.strip() if form.instructions.data else None,
                    collection_method=form.collection_method.data,
                    pharmacy_id=form.pharmacy_id.data if form.collection_method.data == 'pharmacy' and form.pharmacy_id.data != 0 else None,
                    status='pending'  # Initial status
                )
                
                print(f"DEBUG: Prescription object created: {prescription.__dict__}")
                
                # Add to session and commit
                db_ext.session.add(prescription)
                db_ext.session.flush()
                print(f"DEBUG: After flush - Prescription ID: {prescription.id}")
                
                # Commit the transaction
                db_ext.session.commit()
                print(f"DEBUG: After commit - Prescription ID: {prescription.id}")
                
                # Verify the prescription was saved
                saved_prescription = Prescription.query.get(prescription.id)
                if not saved_prescription:
                    raise Exception("Failed to verify prescription was saved")
                
                print(f"DEBUG: Successfully saved prescription with ID: {prescription.id}")
                
                flash('Prescription created successfully!', 'success')
                return redirect(url_for('view_prescription', prescription_id=prescription.id))
                
            except Exception as e:
                db_ext.session.rollback()
                error_msg = f'Error creating prescription: {str(e)}'
                print(f"ERROR: {error_msg}")
                import traceback
                traceback.print_exc()
                flash('An error occurred while creating the prescription. Please try again.', 'danger')
        else:
            # Form validation failed
            if form.errors:
                print(f"DEBUG: Form validation errors: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"{field}: {error}", 'danger')
        
        # If we get here, there was an error or it's a GET request
        return render_template('prescriptions/create.html', form=form, provider=provider)
        
    except Exception as e:
        error_msg = f'Unexpected error in create_prescription: {str(e)}'
        print(f"CRITICAL ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        flash('An unexpected error occurred. Please try again.', 'danger')
        return redirect(url_for('dashboard'))
    
@app.route('/test/create_prescription')
@login_required
def test_create_prescription():
    """Test route to create a prescription directly in the database"""
    try:
        print("DEBUG: Starting test prescription creation")
        
        # Get the first provider and patient for testing
        provider = Provider.query.first()
        if not provider:
            return "No providers found in the database"
            
        patient = Patient.query.first()
        if not patient:
            return "No patients found in the database"
            
        print(f"DEBUG: Using provider_id={provider.id}, patient_id={patient.id}")
        
        # Create a test prescription
        test_prescription = {
            'provider_id': provider.id,
            'patient_id': patient.id,
            'medication_details': [{
                'name': 'Test Medication',
                'dosage': '500mg',
                'frequency': 'Twice daily',
                'duration': '7 days'
            }],
            'instructions': 'Take with food',
            'collection_method': 'pickup',
            'status': 'active'
        }
        
        print(f"DEBUG: Creating test prescription: {test_prescription}")
        
        # Create and save the prescription
        prescription = Prescription(**test_prescription)
        db_ext.session.add(prescription)
        db_ext.session.commit()
        
        print(f"DEBUG: Test prescription created with ID: {prescription.id}")
        
        # Verify it was saved
        saved = Prescription.query.get(prescription.id)
        if saved:
            print(f"DEBUG: Successfully retrieved test prescription: {saved.id}")
            return f"Success! Created test prescription with ID: {saved.id}"
        else:
            return "Error: Could not verify test prescription was saved"
            
    except Exception as e:
        db_ext.session.rollback()
        error_msg = f"Error in test_create_prescription: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return f"Error: {error_msg}"


@app.route('/prescriptions/<int:prescription_id>')
@login_required
def view_prescription(prescription_id):
    """View prescription details"""
    from models_sqlalchemy import Patient, Pharmacy  # Import models here to avoid circular imports
    
    provider = Provider.get_by_user_id(current_user.id)
    if not provider:
        flash('Provider profile not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get the prescription using SQLAlchemy's query.get()
    prescription = Prescription.query.get(prescription_id)
    if not prescription:
        flash('Prescription not found', 'danger')
        return redirect(url_for('prescriptions'))
    
    # Verify the prescription belongs to the provider
    if prescription.provider_id != provider.id:
        flash('You are not authorized to view this prescription', 'danger')
        return redirect(url_for('prescriptions'))
    
    # Get patient and pharmacy details in a single query
    patient = Patient.query.get(prescription.patient_id)
    pharmacy = Pharmacy.query.get(prescription.pharmacy_id) if prescription.pharmacy_id else None
    
    # Get unread message count for sidebar
    unread_count = Message.get_unread_count(provider.id)
    
    return render_template('prescriptions/view.html',
                         prescription=prescription,
                         patient=patient,
                         pharmacy=pharmacy,
                         provider=provider,
                         unread_count=unread_count)


@app.route('/prescriptions/<int:prescription_id>/update_status', methods=['POST'])
@login_required
def update_prescription_status(prescription_id):
    """Update prescription status (e.g., mark as filled, dispensed)"""
    provider = Provider.get_by_user_id(current_user.id)
    if not provider:
        return jsonify({'success': False, 'message': 'Provider not found'}), 403
    
    # Get the prescription
    prescription = Prescription.get_by_id(prescription_id)
    if not prescription:
        return jsonify({'success': False, 'message': 'Prescription not found'}), 404
    
    # Verify the prescription belongs to the provider
    if prescription.provider_id != provider.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get status from request
    status = request.form.get('status')
    if status not in ['pending', 'filled', 'dispensed', 'cancelled']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    # Update status
    prescription.update_status(status)
    
    # Track this interaction
    track_interaction(
        prescription.patient_id,
        'prescription',
        f'Prescription status updated to {status}',
        {'prescription_id': prescription_id, 'status': status}
    )
    
    return jsonify({
        'success': True,
        'message': f'Prescription marked as {status}',
        'status': status,
        'status_display': status.capitalize(),
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


# Hook into share_health_tips to track interactions
old_share_health_tips = app.view_functions['share_health_tips']

def share_health_tips_with_tracking(patient_id):
    """Wrap share_health_tips to track interactions"""
    if request.method == 'POST':
        patient = Patient.get_by_id(patient_id)
        # Track the interaction when health tips are shared
        track_interaction(
            patient_id,
            'health_tip',
            f"Health tips shared with {patient.name}",
            {'method': 'sms'}
        )
    
    return old_share_health_tips(patient_id)

app.view_functions['share_health_tips'] = share_health_tips_with_tracking

# Payment routes
@app.route('/lab-results')
@login_required
def lab_results():
    """Lab results dashboard"""
    provider = Provider.get_by_user_id(current_user.id)
    
    # Get recent lab results
    recent_results = LabResult.query.filter_by(provider_id=provider.id).order_by(LabResult.test_date.desc()).limit(10).all()
    
    # Get counts by status
    pending_count = LabResult.query.filter_by(provider_id=provider.id, status='pending').count()
    completed_count = LabResult.query.filter_by(provider_id=provider.id, status='completed').count()
    abnormal_count = LabResult.query.filter_by(provider_id=provider.id, is_abnormal=True).count()
    
    # Get test type distribution
    test_types = db_ext.session.query(
        LabResult.test_type,
        db_ext.func.count(LabResult.id).label('count')
    ).filter_by(provider_id=provider.id).group_by(LabResult.test_type).all()
    
    return render_template(
        'lab_results.html',
        provider=provider,
        recent_results=recent_results,
        pending_count=pending_count,
        completed_count=completed_count,
        abnormal_count=abnormal_count,
        test_types=test_types
    )


@app.route('/lab-results/<int:result_id>')
@login_required
def view_lab_result(result_id):
    """View a specific lab result"""
    result = LabResult.query.get_or_404(result_id)
    provider = Provider.get_by_user_id(current_user.id)
    
    # Ensure the provider has access to this result
    if result.provider_id != provider.id:
        abort(403)
    
    return render_template('view_lab_result.html', result=result, provider=provider)


@app.route('/lab-results/<int:result_id>/enter-results', methods=['GET', 'POST'])
@login_required
def enter_lab_results(result_id):
    """Enter or update lab test results"""
    result = LabResult.query.get_or_404(result_id)
    provider = Provider.get_by_user_id(current_user.id)
    
    # Ensure the provider has access to this result
    if result.provider_id != provider.id:
        abort(403)
    
    if request.method == 'POST':
        try:
            # Verify CSRF token
            if not verify_csrf(request.form.get('csrf_token')):
                if request.is_json:
                    return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 400
                else:
                    flash('Session expired. Please try again.', 'error')
                    return redirect(url_for('enter_lab_results', result_id=result.id))
            
            # Get form data
            status = request.form.get('status', 'pending')
            is_abnormal = request.form.get('is_abnormal', 'false').lower() == 'true'
            notes = request.form.get('notes', '')
            
            # Process test results from dynamic rows
            test_components = request.form.getlist('test_component')
            results = request.form.getlist('result')
            reference_ranges = request.form.getlist('reference_range')
            
            # Create a list of test results
            test_results = []
            for i in range(len(test_components)):
                if test_components[i] and results[i]:  # Only add if test component and result are provided
                    test_results.append({
                        'component': test_components[i],
                        'result': results[i],
                        'reference_range': reference_ranges[i] if i < len(reference_ranges) else ''
                    })
            
            # Update result data
            result.results = json.dumps(test_results) if test_results else None
            result.status = status
            result.is_abnormal = is_abnormal
            result.notes = notes
            
            # Update result date if completing the test
            if status == 'completed' and not result.result_date:
                result.result_date = datetime.utcnow()
            
            db_ext.session.commit()
            
            flash('Lab results saved successfully', 'success')
            return redirect(url_for('view_lab_result', result_id=result.id))
            
        except Exception as e:
            db_ext.session.rollback()
            logger.error(f"Error saving lab results: {str(e)}")
            flash(f'Error saving lab results: {str(e)}', 'error')
            return redirect(url_for('enter_lab_results', result_id=result.id))
    
    # GET request - show the form
    return render_template('enter_lab_results.html', 
                         result=result, 
                         provider=provider,
                         now=datetime.utcnow())


@app.route('/lab-results/new', methods=['GET', 'POST'])
@login_required
def new_lab_result():
    """Create a new lab test order"""
    provider = Provider.get_by_user_id(current_user.id)
    form = LabResultForm()
    
    # Populate patient choices
    form.patient_id.choices = [(p.id, f"{p.name} ({p.phone_number})") for p in Patient.query.all()]
    
    if form.validate_on_submit():
        try:
            # Create new lab result
            result = LabResult(
                patient_id=form.patient_id.data,
                provider_id=provider.id,
                test_name=form.test_name.data,
                test_type=form.test_type.data,
                test_date=form.test_date.data,
                notes=form.notes.data,
                status='pending',
                is_abnormal=False,
                is_urgent=form.urgent.data
            )
            
            db_ext.session.add(result)
            db_ext.session.commit()
            
            flash('Lab test ordered successfully!', 'success')
            return redirect(url_for('view_lab_result', result_id=result.id))
            
        except Exception as e:
            db_ext.session.rollback()
            logger.error(f"Error creating lab test: {str(e)}")
            flash('An error occurred while creating the lab test. Please try again.', 'danger')
    
    return render_template('new_lab_result.html', 
                         provider=provider,
                         form=form,
                         now=datetime.utcnow())


@app.route('/lab-results/patient/<int:patient_id>')
@login_required
def patient_lab_results(patient_id):
    """View all lab results for a specific patient"""
    provider = Provider.get_by_user_id(current_user.id)
    patient = Patient.query.get_or_404(patient_id)
    
    # Get all results for this patient ordered by test date
    results = LabResult.query.filter_by(
        patient_id=patient_id,
        provider_id=provider.id
    ).order_by(LabResult.test_date.desc()).all()
    
    return render_template(
        'patient_lab_results.html',
        provider=provider,
        patient=patient,
        results=results
    )



    form = LabResultForm()
    
    # Populate patient choices
    form.patient_id.choices = [(p.id, f"{p.name} ({p.phone_number})") for p in Patient.query.all()]
    
    if form.validate_on_submit():
        try:
            # Create new lab result
            result = LabResult(
                patient_id=form.patient_id.data,
                provider_id=provider.id,
                test_name=form.test_name.data,
                test_type=form.test_type.data,
                test_date=form.test_date.data,
                notes=form.notes.data,
                status='pending',
                is_abnormal=False
            )
            
            db_ext.session.add(result)
            db_ext.session.commit()
            
            flash('Lab test created successfully!', 'success')
            return redirect(url_for('view_lab_result', result_id=result.id))
            
        except Exception as e:
            db_ext.session.rollback()
            logger.error(f"Error creating lab result: {str(e)}")
            flash('An error occurred while creating the lab test. Please try again.', 'danger')
    
    return render_template('new_lab_result.html', 
                         provider=provider,
                         form=form,
                         now=datetime.utcnow())


@app.route('/lab-results/<int:result_id>/update', methods=['POST'])
@login_required
def update_lab_result(result_id):
    """Update lab result (AJAX endpoint)"""
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400
    
    try:
        result = LabResult.query.get_or_404(result_id)
        provider = Provider.get_by_user_id(current_user.id)
        
        # Ensure the provider has access to this result
        if result.provider_id != provider.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update result data
        if 'results' in data:
            result.results = data['results']
        if 'status' in data:
            result.status = data['status']
        if 'is_abnormal' in data:
            result.is_abnormal = data['is_abnormal']
        if 'notes' in data:
            result.notes = data['notes']
        
        # Update result date if completing the test
        if data.get('status') == 'completed' and not result.result_date:
            result.result_date = datetime.utcnow()
        
        db_ext.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lab result updated successfully',
            'result': result.to_dict()
        })
        
    except Exception as e:
        db_ext.session.rollback()
        logger.error(f"Error updating lab result: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/payments', methods=['GET', 'POST'])
@login_required
def payments():
    """Payment dashboard for managing appointment payments"""
    provider = Provider.get_by_user_id(current_user.id)
    
    # Create payment form
    form = PaymentForm()
    
    # Get all payment records with related data
    all_payments = db_ext.session.query(Payment).join(
        Appointment, Payment.appointment_id == Appointment.id
    ).join(
        Patient, Appointment.patient_id == Patient.id
    ).order_by(Payment.created_at.desc()).all()
    
    # Get appointments that can have payments (pending, confirmed, or completed status)
    pending_appointments = db_ext.session.query(Appointment).filter(
        Appointment.provider_id == provider.id,
        Appointment.payment_status.in_(['pending', 'unpaid', 'partially_paid']),
        Appointment.price > 0
    ).outerjoin(Patient).options(
        db_ext.joinedload(Appointment.patient)
    ).all()
    
    # Populate appointment choices with patient and appointment details
    form.appointment_id.choices = [
        (str(appt.id), f"{appt.patient.name if appt.patient else 'Walk-in Patient'} - {appt.date.strftime('%b %d, %I:%M %p')} - {appt.price}")
        for appt in pending_appointments
    ]
    
    # Add data attributes for JavaScript
    for appt in pending_appointments:
        for option in form.appointment_id:
            if option.data == str(appt.id):
                option.data_attrs = {
                    'amount': str(appt.price),
                    'patient': appt.patient.name if appt.patient else 'Walk-in Patient'
                }
    
    # Handle form submission
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Process payment here
                appointment = db_ext.session.query(Appointment).get(form.appointment_id.data)
                if not appointment:
                    flash('Invalid appointment selected', 'danger')
                    return redirect(url_for('payments'))
                    
                # Create new payment record
                payment = Payment(
                    appointment_id=appointment.id,
                    amount=form.amount.data,
                    payment_method=form.payment_method.data,
                    mpesa_reference=form.mpesa_reference.data if form.payment_method.data == 'mpesa' else None,
                    notes=form.notes.data,
                    status='completed',
                    created_by=current_user.id
                )
                
                # Update appointment payment status
                total_paid = sum(p.amount for p in appointment.payments if p.status == 'completed')
                total_paid += payment.amount
                
                if total_paid >= appointment.price:
                    appointment.payment_status = 'paid'
                elif total_paid > 0:
                    appointment.payment_status = 'partially_paid'
                else:
                    appointment.payment_status = 'unpaid'
                
                # Save changes
                db_ext.session.add(payment)
                db_ext.session.commit()
                
                flash('Payment recorded successfully!', 'success')
                return redirect(url_for('payments'))
                
            except Exception as e:
                db_ext.session.rollback()
                app.logger.error(f"Error processing payment: {str(e)}")
                flash('An error occurred while processing the payment. Please try again.', 'danger')
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    # Get payment summary statistics
    payment_summary = Payment.generate_payment_summary()
    
    # Get recent refunds
    recent_refunds = db_ext.session.query(PaymentRefund).join(
        Payment, PaymentRefund.payment_id == Payment.id
    ).filter(
        PaymentRefund.status.in_(['pending', 'completed'])
    ).order_by(PaymentRefund.created_at.desc()).limit(5).all()
    
    return render_template('payments.html', 
                         provider=provider,
                         payments=all_payments,
                         pending_appointments=pending_appointments,
                         payment_summary=payment_summary,
                         recent_refunds=recent_refunds,
                         form=form)

@app.route('/create_payment', methods=['POST'])
@login_required
def create_payment():
    """Create a new payment record"""
    try:
        provider = Provider.get_by_user_id(current_user.id)
        
        appointment_id = request.form.get('appointment_id')
        amount = float(request.form.get('amount', 0))
        payment_method = request.form.get('payment_method', 'cash').lower()
        mpesa_reference = request.form.get('mpesa_reference')
        notes = request.form.get('notes')
        
        if not appointment_id or amount <= 0:
            flash('Valid appointment ID and amount are required.', 'danger')
            return redirect(url_for('payments'))
        
        appointment = Appointment.get_by_id(int(appointment_id))
        if not appointment:
            flash('Appointment not found.', 'danger')
            return redirect(url_for('payments'))
        
        patient = Patient.get_by_id(appointment.patient_id)
        if not patient:
            flash('Patient not found.', 'danger')
            return redirect(url_for('payments'))
        
        # Create payment record with additional fields
        payment = Payment(
            appointment_id=int(appointment_id),
            amount=amount,
            phone_number=patient.phone_number,
            payment_method=payment_method,
            status='pending',
            notes=notes,
            payment_metadata={
                'created_by': current_user.id,
                'payment_processor': 'manual'
            }
        )
        
        db_ext.session.add(payment)
        db_ext.session.commit()
        
        # If M-Pesa reference is provided, mark as completed
        if mpesa_reference and payment_method == 'mpesa':
            payment.mpesa_reference = mpesa_reference
            payment.status = 'completed'
            payment.paid_at = datetime.utcnow()
            
            # Update appointment payment status
            appointment.payment_status = 'completed'
            db_ext.session.commit()
            
            flash('Payment recorded and marked as completed successfully!', 'success')
            
            flash('Payment recorded as completed with M-Pesa reference.', 'success')
        else:
            flash('Payment record created. Please update status once payment is confirmed.', 'info')
        
        # Track this interaction
        UserInteraction.create(
            patient.id,
            'payment_created',
            f'Payment of {amount} {payment.currency} recorded for appointment on {appointment.date}',
            {
                'payment_id': payment.id,
                'amount': amount,
                'method': payment_method,
                'appointment_id': appointment.id
            }
        )
        
        return redirect(url_for('view_payment', payment_id=payment.id))
        
    except ValueError as e:
        db.session.rollback()
        app.logger.error(f"Payment creation error: {str(e)}")
        flash('Invalid amount or payment details. Please check and try again.', 'danger')
        return redirect(url_for('payments'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Payment creation error: {str(e)}")
        flash('An error occurred while creating the payment. Please try again.', 'danger')
        return redirect(url_for('payments'))

@app.route('/payments/<int:payment_id>')
@login_required
def view_payment(payment_id):
    """View payment details"""
    payment = db_ext.session.query(Payment).get_or_404(payment_id)
    appointment = db_ext.session.query(Appointment).get(payment.appointment_id)
    patient = db_ext.session.query(Patient).get(appointment.patient_id) if appointment else None
    refunds = db_ext.session.query(PaymentRefund).filter_by(payment_id=payment_id).all()
    
    return render_template('payment_details.html',
                         payment=payment,
                         appointment=appointment,
                         patient=patient,
                         refunds=refunds)

@app.route('/payments/update_status', methods=['POST'])
@login_required
def update_payment_status():
    """Update payment status via AJAX"""
    try:
        payment_id = request.form.get('payment_id')
        status = request.form.get('status')
        notes = request.form.get('notes')
        
        if not payment_id or not status:
            return jsonify({'success': False, 'error': 'Missing payment_id or status'}), 400
            
        payment = db_ext.session.query(Payment).get_or_404(payment_id)
        
        # Validate status
        valid_statuses = ['pending', 'completed', 'failed', 'refunded', 'partially_refunded']
        if status not in valid_statuses:
            return jsonify({'success': False, 'error': 'Invalid status provided'}), 400
    
        # Update payment status
        previous_status = payment.status
        payment.status = status
        payment.notes = notes if notes else payment.notes
        
        # Update timestamps
        if status == 'completed' and not payment.paid_at:
            payment.paid_at = datetime.utcnow()
        
        # Update appointment payment status if applicable
        appointment = db_ext.session.query(Appointment).get(payment.appointment_id)
        if appointment:
            appointment.payment_status = status
        
        db_ext.session.commit()
        
        # Track this interaction
        if appointment and appointment.patient_id:
            UserInteraction.create(
                appointment.patient_id,
                f'payment_{status}',
                f'Payment status updated to {status} for payment {payment.id}',
                {
                    'payment_id': payment.id,
                    'amount': payment.amount,
                    'previous_status': previous_status,
                    'new_status': status
                }
            )
        
        return jsonify({
            'success': True, 
            'message': f'Payment status updated to {status}',
            'new_status': status,
            'status_badge': payment_status_badge(status)
        })
        
    except Exception as e:
        db_ext.session.rollback()
        app.logger.error(f"Error updating payment status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/payments/refund', methods=['POST'])
@login_required
def create_refund():
    """Create a refund for a payment via AJAX"""
    try:
        payment_id = request.form.get('payment_id')
        amount = float(request.form.get('amount', 0))
        reason = request.form.get('reason', 'Refund requested')
        
        if not payment_id:
            return jsonify({'success': False, 'error': 'Missing payment_id'}), 400
            
        payment = db_ext.session.query(Payment).get_or_404(payment_id)
        
        # Calculate remaining balance
        refunded_amount = sum(r.amount for r in payment.refunds if r.status == 'completed')
        remaining_balance = payment.amount - refunded_amount
        
        # Validate amount
        if amount <= 0 or amount > remaining_balance:
            return jsonify({
                'success': False, 
                'error': f'Invalid amount. Must be between 0 and {remaining_balance}',
                'remaining_balance': remaining_balance
            }), 400
        
        # Create refund record
        refund = PaymentRefund(
            payment_id=payment_id,
            amount=amount,
            reason=reason,
            status='completed',
            processed_by=current_user.id,
            processed_at=datetime.utcnow()
        )
        db_ext.session.add(refund)
        
        # Update payment status based on remaining balance
        new_balance = remaining_balance - amount
        if new_balance <= 0:
            payment.status = 'refunded'
        else:
            payment.status = 'partially_refunded'
        
        db_ext.session.commit()
        
        # Update appointment payment status if fully refunded
        if new_balance <= 0:
            appointment = db_ext.session.query(Appointment).get(payment.appointment_id)
            if appointment:
                appointment.payment_status = 'refunded'
                db_ext.session.commit()
        
        # Send refund confirmation
        try:
            send_refund_confirmation(payment_id, amount, reason)
        except Exception as e:
            app.logger.error(f"Error sending refund confirmation: {str(e)}")
        
        # Get updated payment data
        payment_data = {
            'id': payment.id,
            'status': payment.status,
            'status_badge': payment_status_badge(payment.status),
            'refunded_amount': refunded_amount + amount,
            'remaining_balance': new_balance
        }
        
        return jsonify({
            'success': True, 
            'message': f'Refund of {amount} processed successfully.',
            'payment': payment_data,
            'refund': {
                'id': refund.id,
                'amount': refund.amount,
                'reason': refund.reason,
                'status': refund.status,
                'processed_at': refund.processed_at.isoformat(),
                'processed_by': refund.processed_by
            }
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid amount specified'}), 400
    except Exception as e:
        db_ext.session.rollback()
        app.logger.error(f"Refund processing error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/payments/<int:payment_id>/receipt')
@login_required
def download_receipt(payment_id):
    """Download payment receipt as PDF"""
    payment = db_ext.session.query(Payment).get_or_404(payment_id)
    
    try:
        receipt_path = generate_payment_receipt(payment.id)
        if not receipt_path or not os.path.exists(receipt_path):
            flash('Receipt not found. Please try again.', 'danger')
            return redirect(url_for('view_payment', payment_id=payment_id))
        
        # Mark receipt as sent
        payment.receipt_sent = True
        payment.receipt_sent_at = datetime.utcnow()
        db_ext.session.commit()
        
        return send_from_directory(
            os.path.dirname(receipt_path),
            os.path.basename(receipt_path),
            as_attachment=True,
            download_name=f'receipt_{payment_id}.pdf'
        )
    except Exception as e:
        app.logger.error(f"Error generating receipt: {str(e)}")
        flash('Failed to generate receipt. Please try again.', 'danger')
        return redirect(url_for('view_payment', payment_id=payment_id))


# Helper function to send refund confirmation
def send_refund_confirmation(payment_id, amount, reason):
    """
    Send a refund confirmation to the patient
    In a real application, this would send an email or SMS
    """
    try:
        payment = db_ext.session.query(Payment).get(payment_id)
        if not payment:
            app.logger.error(f"Payment {payment_id} not found for refund confirmation")
            return False
            
        # In a real app, send an email or SMS here
        app.logger.info(f"Refund confirmation sent for payment {payment_id}: {amount} - {reason}")
        return True
    except Exception as e:
        app.logger.error(f"Error sending refund confirmation: {str(e)}")
        return False

# Helper function to generate payment receipt
def generate_payment_receipt(payment_id):
    """
    Generate a PDF receipt for a payment
    Returns the path to the generated receipt file
    """
    try:
        payment = db_ext.session.query(Payment).get(payment_id)
        if not payment:
            app.logger.error(f"Payment {payment_id} not found for receipt generation")
            return None
            
        # Create receipts directory if it doesn't exist
        receipt_dir = os.path.join(app.static_folder, 'receipts')
        os.makedirs(receipt_dir, exist_ok=True)
        
        # In a real app, generate a proper PDF receipt
        receipt_path = os.path.join(receipt_dir, f'receipt_{payment_id}.pdf')
        
        # For now, just create a simple text file
        with open(receipt_path, 'w') as f:
            f.write(f"Receipt for Payment #{payment_id}\n")
            f.write("=" * 30 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Amount: {payment.amount} {payment.currency or 'KES'}\n")
            f.write(f"Payment Method: {payment.payment_method.upper()}\n")
            f.write(f"Status: {payment.status.upper()}\n")
            if payment.mpesa_reference:
                f.write(f"M-Pesa Reference: {payment.mpesa_reference}\n")
        
        return receipt_path
    except Exception as e:
        app.logger.error(f"Error generating receipt: {str(e)}")
        return None

# Add payment-related template filters
@app.template_filter('format_currency')
def format_currency(amount, currency='KES'):
    """Format currency for display"""
    try:
        return f"{currency} {float(amount):,.2f}"
    except (ValueError, TypeError):
        return f"{currency} 0.00"

@app.template_filter('payment_status_badge')
def payment_status_badge(status):
    """Return a Bootstrap badge for payment status"""
    status_classes = {
        'pending': 'bg-warning',
        'completed': 'bg-success',
        'failed': 'bg-danger',
        'refunded': 'bg-info',
        'partially_refunded': 'bg-primary',
        'cancelled': 'bg-secondary'
    }
    return status_classes.get(status.lower(), 'bg-secondary')

if __name__ == '__main__':
    # Create upload directories if they don't exist
    os.makedirs('static/receipts', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)

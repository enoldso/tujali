import os
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import (User, Provider, Patient, Appointment, Message, HealthInfo, UserInteraction, Payment, 
                   Prescription, WalkInPatient, LabTest, LabResult, Bill, db, init_db)
from forms import (LoginForm, RegistrationForm, MessageForm, HealthInfoForm, HealthTipsForm, HealthEducationForm,
                  PrescriptionForm, WalkInForm, QuickPatientForm, LabTestForm, LabResultForm, 
                  BillItemForm, PaymentRecordForm, UserManagementForm, DepartmentForm)
from ussd_handler import ussd_callback
import utils
from utils import requires_permission, requires_department, get_navigation_items
import ai_service
import mock_ai_service  # Import the mock AI service

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "tujali-dev-secret-key")

# Add template filters
from datetime import datetime
@app.template_filter('now')
def _jinja2_filter_now():
    """Return current datetime for templates"""
    return datetime.now()

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize database (in-memory for MVP)
# Double check database initialization
init_db()

# For debugging user authentication
print("Initial users:", [f"{u.username}:{u.password_hash}" for u in db['users']])

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for healthcare providers"""
    # Always reinitialize database to ensure admin user exists
    init_db()
    
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
            logger.debug(f"User found: {user.username}, with hash: {user.password_hash}")
            # Store expected hash to compare
            expected_hash = f"hashed_{password}"
            logger.debug(f"Expected hash would be: {expected_hash}")
            
            # Debug check_password_hash function directly
            valid_password = user.password_hash == expected_hash
            logger.debug(f"Direct comparison: {valid_password}")
            
            # Also try the function
            func_valid = check_password_hash(user.password_hash, password)
            logger.debug(f"Function validity check: {func_valid}")
            
            if valid_password:
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(f'Invalid password. Debug info has been logged.', 'danger')
        else:
            logger.debug(f"User not found: {username}")
            flash('Invalid username.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page for healthcare providers"""
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.username_exists(form.username.data):
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form)
        
        if User.email_exists(form.email.data):
            flash('Email already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user
        password_hash = generate_password_hash(form.password.data)
        user = User.create(form.username.data, form.email.data, password_hash)
        
        # Create provider profile
        provider = Provider.create(
            user.id,
            form.full_name.data,
            form.specialization.data,
            form.license_number.data,
            form.phone_number.data,
            form.location.data,
            form.years_experience.data
        )
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Logout the current user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Enhanced dashboard with role-based content"""
    # Role-based dashboard routing
    if hasattr(current_user, 'role'):
        if current_user.role == 'super_admin':
            return redirect(url_for('admin_dashboard'))
        elif hasattr(current_user, 'department'):
            if current_user.department == 'finance':
                return redirect(url_for('finance_dashboard'))
            elif current_user.department == 'laboratory':
                return redirect(url_for('lab_dashboard'))
            elif current_user.department == 'clinical':
                return redirect(url_for('clinical_dashboard'))
    
    # Default provider dashboard
    provider = Provider.get_by_user_id(current_user.id)
    
    # Get statistics with safe defaults
    total_patients = len(db.get('patients', []))
    recent_patients = sorted(db.get('patients', []), key=lambda x: getattr(x, 'created_at', datetime.now()), reverse=True)[:5]
    
    # Get appointments and messages data
    appointments = db.get('appointments', [])
    user_appointments = [a for a in appointments if hasattr(a, 'provider_id') and a.provider_id == current_user.id]
    recent_appointments = sorted(user_appointments, key=lambda x: getattr(x, 'created_at', datetime.now()), reverse=True)[:5]
    
    messages = db.get('messages', [])
    user_messages = [m for m in messages if hasattr(m, 'provider_id') and m.provider_id == current_user.id]
    recent_messages = sorted(user_messages, key=lambda x: getattr(x, 'created_at', datetime.now()), reverse=True)[:5]
    
    prescriptions = db.get('prescriptions', [])
    user_prescriptions = [p for p in prescriptions if hasattr(p, 'provider_id') and p.provider_id == current_user.id]
    recent_prescriptions = sorted(user_prescriptions, key=lambda x: getattr(x, 'created_at', datetime.now()), reverse=True)[:5]
    
    # Navigation items based on user permissions
    nav_items = get_navigation_items()
    
    return render_template('dashboard.html', 
                         provider=provider,
                         total_patients=total_patients,
                         recent_patients=recent_patients,
                         recent_appointments=recent_appointments,
                         recent_messages=recent_messages,
                         recent_prescriptions=recent_prescriptions,
                         nav_items=nav_items)

@app.route('/patients')
@login_required
def patients():
    """List all patients"""
    provider = Provider.get_by_user_id(current_user.id)
    patients_list = Patient.get_all()
    return render_template('patients.html', provider=provider, patients=patients_list)

@app.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    """View patient details"""
    provider = Provider.get_by_user_id(current_user.id)
    patient = Patient.get_by_id(patient_id)
    
    if not patient:
        flash('Patient not found.', 'danger')
        return redirect(url_for('patients'))
    
    appointments = Appointment.get_by_patient(patient_id)
    messages = Message.get_conversation(provider.id, patient_id)
    
    return render_template('patient_detail.html', 
                          provider=provider,
                          patient=patient,
                          appointments=appointments,
                          messages=messages)

@app.route('/appointments')
@login_required
def appointments():
    """List and manage appointments"""
    provider = Provider.get_by_user_id(current_user.id)
    appointment_list = Appointment.get_by_provider(provider.id)
    return render_template('appointments.html', provider=provider, appointments=appointment_list)

@app.route('/appointment/update', methods=['POST'])
@login_required
def update_appointment():
    """Update appointment status"""
    provider = Provider.get_by_user_id(current_user.id)
    appointment_id = request.form.get('appointment_id')
    status = request.form.get('status')
    
    if not appointment_id or not status:
        flash('Invalid request. Appointment ID and status are required.', 'danger')
        return redirect(url_for('appointments'))
    
    success = Appointment.update_status(int(appointment_id), status)
    
    if success:
        flash('Appointment updated successfully.', 'success')
    else:
        flash('Failed to update appointment.', 'danger')
    
    return redirect(url_for('appointments'))

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
    return render_template('health_info.html', provider=provider, info_list=info_list, form=form)

@app.route('/symptom-dashboard')
@login_required
def symptom_dashboard():
    """Interactive Health Symptom Visualization Dashboard"""
    provider = Provider.get_by_user_id(current_user.id)
    
    # Get all patients
    patients = Patient.get_all()
    
    # Collect symptom data for visualization
    symptom_data = []
    symptom_categories = {
        'respiratory': ['cough', 'breathing', 'chest', 'breath', 'respiratory', 'pneumonia'],
        'digestive': ['stomach', 'diarrhea', 'nausea', 'vomit', 'digest', 'abdominal'],
        'pain': ['pain', 'ache', 'hurt', 'sore', 'headache', 'migraine'],
        'fever': ['fever', 'temperature', 'hot', 'chills', 'cold', 'sweat'],
        'skin': ['rash', 'itching', 'skin', 'lesion', 'bump', 'sore'],
        'other': []
    }
    
    location_data = {}
    severity_data = {'Mild': 0, 'Moderate': 0, 'Severe': 0}
    
    # Process patient symptom data for visualization
    for patient in patients:
        if not hasattr(patient, 'symptoms') or not patient.symptoms:
            continue
            
        for symptom_entry in patient.symptoms:
            symptom_text = symptom_entry['text'].lower()
            symptom_date = symptom_entry['date']
            
            # Determine symptom category
            category = 'other'
            for cat, keywords in symptom_categories.items():
                if any(keyword in symptom_text for keyword in keywords):
                    category = cat
                    break
            
            # Determine severity (if mentioned in text or if available)
            severity = 'Unknown'
            if 'severe' in symptom_text or 'unbearable' in symptom_text:
                severity = 'Severe'
                severity_data['Severe'] += 1
            elif 'mild' in symptom_text or 'slight' in symptom_text:
                severity = 'Mild'
                severity_data['Mild'] += 1
            elif 'moderate' in symptom_text:
                severity = 'Moderate'
                severity_data['Moderate'] += 1
            
            # Add to symptom data
            symptom_data.append({
                'patient_id': patient.id,
                'patient_name': patient.name,
                'symptom': symptom_text,
                'category': category,
                'severity': severity,
                'date': symptom_date,
                'location': patient.location
            })
            
            # Add to location data
            if patient.location not in location_data:
                location_data[patient.location] = 0
            location_data[patient.location] += 1
    
    # Sort locations by frequency
    sorted_locations = dict(sorted(location_data.items(), key=lambda item: item[1], reverse=True))
    
    # Calculate sum of counts for locations beyond the top 5
    other_locations_count = 0
    if len(sorted_locations) > 5:
        other_locations_count = sum(list(sorted_locations.values())[5:])
    
    # Prepare data for time-based visualization
    time_data = {}
    for entry in symptom_data:
        date_str = entry['date'].strftime('%Y-%m-%d')
        if date_str not in time_data:
            time_data[date_str] = 0
        time_data[date_str] += 1
    
    # Sort time data chronologically
    sorted_time_data = dict(sorted(time_data.items()))
    
    # Count symptoms by category
    category_counts = {}
    for entry in symptom_data:
        category = entry['category']
        if category not in category_counts:
            category_counts[category] = 0
        category_counts[category] += 1
    
    return render_template('symptom_dashboard.html', 
                          provider=provider,
                          symptom_data=symptom_data,
                          location_data=sorted_locations,
                          severity_data=severity_data,
                          time_data=sorted_time_data,
                          category_counts=category_counts,
                          other_locations_count=other_locations_count,
                          patients=patients)

@app.route('/health-tips', methods=['GET', 'POST'])
@login_required
def health_tips():
    """AI-Powered Personalized Health Tips"""
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
    
    return render_template('health_tips.html', 
                          provider=provider,
                          form=form,
                          generated_tips=generated_tips,
                          selected_patient=selected_patient)

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
        interactions = UserInteraction.get_by_patient(patient.id)
        patient.interaction_count = len(interactions)
    
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

# Legacy payment route handling - now managed by finance dashboard

@app.route('/create_payment', methods=['POST'])
@login_required
def create_payment():
    """Create a new payment record"""
    provider = Provider.get_by_user_id(current_user.id)
    
    appointment_id = request.form.get('appointment_id')
    amount = request.form.get('amount')
    payment_method = request.form.get('payment_method')
    mpesa_reference = request.form.get('mpesa_reference')
    
    if not appointment_id or not amount:
        flash('Appointment ID and amount are required.', 'danger')
        return redirect(url_for('payments'))
    
    appointment = Appointment.get_by_id(int(appointment_id))
    if not appointment:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('payments'))
    
    patient = Patient.get_by_id(appointment.patient_id)
    if not patient:
        flash('Patient not found.', 'danger')
        return redirect(url_for('payments'))
    
    # Create payment record
    payment = Payment.create(
        int(appointment_id),
        float(amount),
        patient.phone_number,
        payment_method
    )
    
    # Update payment reference if provided (for M-Pesa)
    if payment_method == 'mpesa' and mpesa_reference:
        Payment.update_status(payment.id, 'completed', mpesa_reference)
        # Update appointment payment status
        Appointment.update_status(appointment.id, appointment.status, 'completed')
        flash('Payment recorded as completed with M-Pesa reference.', 'success')
    else:
        flash('Payment record created.', 'success')
    
    # Track this interaction
    UserInteraction.create(
        patient.id,
        'payment',
        f'Payment recorded for appointment on {appointment.date}',
        {
            'payment_id': payment.id,
            'amount': float(amount),
            'method': payment_method
        }
    )
    
    return redirect(url_for('payments'))

@app.route('/update_payment_status', methods=['POST'])
@login_required
def update_payment_status():
    """Update payment status"""
    payment_id = request.form.get('payment_id')
    status = request.form.get('status')
    
    if not payment_id or not status:
        flash('Payment ID and status are required.', 'danger')
        return redirect(url_for('payments'))
    
    payment = Payment.get_by_id(int(payment_id))
    if not payment:
        flash('Payment not found.', 'danger')
        return redirect(url_for('payments'))
    
    # Update payment status
    success = Payment.update_status(int(payment_id), status)
    
    if success:
        # Update appointment payment status
        appointment = Appointment.get_by_id(payment.appointment_id)
        if appointment:
            Appointment.update_status(appointment.id, appointment.status, status)
        
        flash('Payment status updated successfully.', 'success')
        
        # Track this interaction if payment completed
        if status == 'completed':
            patient = Patient.get_by_id(appointment.patient_id) if appointment else None
            if patient:
                UserInteraction.create(
                    patient.id,
                    'payment',
                    f'Payment completed for appointment on {appointment.date}',
                    {
                        'payment_id': payment.id,
                        'amount': payment.amount,
                        'method': payment.payment_method
                    }
                )
    else:
        flash('Failed to update payment status.', 'danger')
    
    return redirect(url_for('payments'))


# ============== PRESCRIPTION MANAGEMENT ==============

@app.route('/prescriptions')
@login_required
def prescriptions():
    """List all prescriptions"""
    provider = Provider.get_by_user_id(current_user.id)
    prescription_list = Prescription.get_by_provider(provider.id)
    return render_template('prescriptions.html', provider=provider, prescriptions=prescription_list)

@app.route('/prescriptions/create', methods=['GET', 'POST'])
@login_required
def create_prescription():
    """Create a new prescription"""
    provider = Provider.get_by_user_id(current_user.id)
    form = PrescriptionForm()
    
    # Get patients and appointments for dropdown
    patients = Patient.get_all()
    appointments = Appointment.get_by_provider(provider.id)
    
    form.patient_id.choices = [(str(p.id), f"{p.name} ({p.phone_number})") for p in patients]
    form.appointment_id.choices = [('', 'No Associated Appointment')] + [(str(a.id), f"Appointment on {a.date} at {a.time}") for a in appointments]
    
    if form.validate_on_submit():
        # Create medication list
        medications = [{
            'name': form.medication_name.data,
            'dosage': form.dosage.data,
            'frequency': form.frequency.data,
            'duration': form.duration.data
        }]
        
        # Calculate delivery fee based on method
        delivery_fee = 0.0
        if form.delivery_method.data == 'bike':
            delivery_fee = 100.0  # KSh 100 for bike delivery
        elif form.delivery_method.data == 'drone':
            delivery_fee = 200.0  # KSh 200 for drone delivery
        
        appointment_id = int(form.appointment_id.data) if form.appointment_id.data else None
        
        prescription = Prescription.create(
            int(form.patient_id.data),
            provider.id,
            appointment_id,
            medications,
            form.instructions.data,
            form.delivery_method.data,
            form.delivery_address.data,
            delivery_fee
        )
        
        # Create bill for prescription
        patient = Patient.get_by_id(int(form.patient_id.data))
        if patient:
            bill = Bill.create(patient.id, provider.id, appointment_id)
            bill.add_item('prescription', f'Prescription: {form.medication_name.data}', 50.0)  # Base prescription fee
            if delivery_fee > 0:
                bill.add_item('delivery', f'{form.delivery_method.data.title()} Delivery', delivery_fee)
        
        flash('Prescription created successfully.', 'success')
        return redirect(url_for('prescriptions'))
    
    return render_template('create_prescription.html', provider=provider, form=form)

@app.route('/prescriptions/<int:prescription_id>/update', methods=['POST'])
@login_required
def update_prescription_status(prescription_id):
    """Update prescription status"""
    status = request.form.get('status')
    
    if Prescription.update_status(prescription_id, status):
        flash('Prescription status updated successfully.', 'success')
    else:
        flash('Failed to update prescription status.', 'danger')
    
    return redirect(url_for('prescriptions'))


# ============== WALK-IN PATIENT MANAGEMENT ==============

@app.route('/walk-in')
@login_required
def walk_in_patients():
    """Manage walk-in patients"""
    provider = Provider.get_by_user_id(current_user.id)
    waiting_patients = WalkInPatient.get_by_provider(provider.id, 'waiting')
    in_consultation = WalkInPatient.get_by_provider(provider.id, 'in_consultation')
    completed_today = WalkInPatient.get_by_provider(provider.id, 'completed')
    
    return render_template('walk_in.html', 
                          provider=provider,
                          waiting_patients=waiting_patients,
                          in_consultation=in_consultation,
                          completed_today=completed_today)

@app.route('/walk-in/register', methods=['GET', 'POST'])
@login_required
def register_walk_in():
    """Register a walk-in patient"""
    provider = Provider.get_by_user_id(current_user.id)
    walk_in_form = WalkInForm()
    quick_patient_form = QuickPatientForm()
    
    # Get patients for dropdown
    patients = Patient.get_all()
    walk_in_form.patient_id.choices = [(str(p.id), f"{p.name} ({p.phone_number})") for p in patients]
    
    if 'register_walk_in' in request.form and walk_in_form.validate_on_submit():
        walkin = WalkInPatient.create(
            int(walk_in_form.patient_id.data),
            provider.id,
            walk_in_form.priority.data,
            walk_in_form.notes.data
        )
        
        # Track interaction
        track_interaction(
            int(walk_in_form.patient_id.data),
            'walk_in',
            'Registered as walk-in patient',
            {'priority': walk_in_form.priority.data, 'walkin_id': walkin.id}
        )
        
        flash('Walk-in patient registered successfully.', 'success')
        return redirect(url_for('walk_in_patients'))
    
    elif 'add_patient' in request.form and quick_patient_form.validate_on_submit():
        # Quick add new patient
        patient = Patient.create(
            quick_patient_form.phone_number.data,
            quick_patient_form.name.data,
            quick_patient_form.age.data,
            quick_patient_form.gender.data,
            quick_patient_form.location.data,
            quick_patient_form.language.data
        )
        
        # Immediately register as walk-in
        walkin = WalkInPatient.create(patient.id, provider.id)
        
        flash(f'New patient {patient.name} added and registered for walk-in.', 'success')
        return redirect(url_for('walk_in_patients'))
    
    return render_template('register_walk_in.html', 
                          provider=provider, 
                          walk_in_form=walk_in_form,
                          quick_patient_form=quick_patient_form)

@app.route('/walk-in/update', methods=['POST'])
@login_required
def update_walk_in_status():
    """Update walk-in patient status"""
    walkin_id = request.form.get('walkin_id', type=int)
    status = request.form.get('status')
    
    provider = Provider.get_by_user_id(current_user.id)
    walkin = WalkInPatient.get_by_id(walkin_id)
    
    if WalkInPatient.update_status(walkin_id, status):
        # When completing a consultation, automatically create bill
        if status == 'completed' and walkin and provider:
            # Check if bill already exists for this walk-in
            existing_bills = Bill.get_by_patient(walkin.patient_id)
            consultation_bill_exists = any(
                any(item['type'] == 'consultation' for item in bill.items)
                for bill in existing_bills
                if (datetime.now() - bill.created_at).days == 0  # Same day
            )
            
            if not consultation_bill_exists:
                bill = Bill.create(walkin.patient_id, provider.id)
                consultation_fee = 300.0  # Standard consultation fee
                if walkin.priority == 'urgent':
                    consultation_fee = 500.0  # Urgent consultation fee
                
                bill.add_item(
                    'consultation', 
                    f'{walkin.priority.title()} consultation (Walk-in)',
                    consultation_fee
                )
        
        flash('Walk-in status updated successfully.', 'success')
    else:
        flash('Failed to update walk-in status.', 'danger')
    
    return redirect(url_for('walk_in_patients'))


# ============== LAB TEST MANAGEMENT ==============

@app.route('/lab-tests')
@login_required
def lab_tests():
    """List all lab tests"""
    provider = Provider.get_by_user_id(current_user.id)
    test_list = LabTest.get_by_provider(provider.id)
    return render_template('lab_tests.html', provider=provider, lab_tests=test_list)

@app.route('/lab-tests/order', methods=['GET', 'POST'])
@login_required
def order_lab_test():
    """Order a new lab test"""
    provider = Provider.get_by_user_id(current_user.id)
    form = LabTestForm()
    
    # Get patients and appointments for dropdown
    patients = Patient.get_all()
    appointments = Appointment.get_by_provider(provider.id)
    
    form.patient_id.choices = [(str(p.id), f"{p.name} ({p.phone_number})") for p in patients]
    form.appointment_id.choices = [('', 'No Associated Appointment')] + [(str(a.id), f"Appointment on {a.date} at {a.time}") for a in appointments]
    
    if form.validate_on_submit():
        appointment_id = int(form.appointment_id.data) if form.appointment_id.data else None
        
        lab_test = LabTest.create(
            int(form.patient_id.data),
            provider.id,
            appointment_id,
            form.test_name.data,
            form.test_type.data,
            float(form.cost.data),
            form.instructions.data
        )
        
        # Create bill for lab test
        patient = Patient.get_by_id(int(form.patient_id.data))
        if patient:
            bill = Bill.create(patient.id, provider.id, appointment_id)
            bill.add_item('lab_test', f'Lab Test: {form.test_name.data}', float(form.cost.data))
        
        flash('Lab test ordered successfully.', 'success')
        return redirect(url_for('lab_tests'))
    
    return render_template('order_lab_test.html', provider=provider, form=form)

@app.route('/lab-tests/<int:test_id>/results', methods=['GET', 'POST'])
@login_required
def lab_test_results(test_id):
    """View or record lab test results"""
    provider = Provider.get_by_user_id(current_user.id)
    lab_test = LabTest.get_by_id(test_id)
    
    if not lab_test:
        flash('Lab test not found.', 'danger')
        return redirect(url_for('lab_tests'))
    
    existing_result = LabResult.get_by_lab_test(test_id)
    form = LabResultForm()
    form.lab_test_id.data = test_id
    
    if form.validate_on_submit() and not existing_result:
        # Parse results from form data
        results = {}
        normal_ranges = {}
        
        # Get all form fields that start with 'result_'
        for key, value in request.form.items():
            if key.startswith('result_') and value:
                param_name = key.replace('result_', '')
                results[param_name] = value
                
                # Check for corresponding normal range
                normal_key = f'normal_{param_name}'
                if normal_key in request.form and request.form[normal_key]:
                    normal_ranges[param_name] = request.form[normal_key]
        
        LabResult.create(
            test_id,
            results,
            normal_ranges,
            form.notes.data,
            form.technician_name.data
        )
        
        flash('Lab results recorded successfully.', 'success')
        return redirect(url_for('lab_tests'))
    
    return render_template('lab_test_results.html', 
                          provider=provider, 
                          lab_test=lab_test,
                          existing_result=existing_result,
                          form=form)


# ============== COMPREHENSIVE BILLING ==============

@app.route('/finance')
@login_required
def finance():
    """Unified financial management dashboard"""
    provider = Provider.get_by_user_id(current_user.id)
    
    # Get bills and payments
    bills = Bill.get_by_provider(provider.id)
    payments = Payment.get_by_provider(provider.id)
    
    # Calculate financial statistics
    total_billed = sum(bill.total_amount for bill in bills)
    total_received = sum(payment.amount for payment in payments if payment.status == 'completed')
    outstanding_amount = total_billed - total_received
    
    # Categorize bills and payments
    pending_bills = [bill for bill in bills if bill.status == 'pending']
    paid_bills = [bill for bill in bills if bill.status == 'paid']
    pending_payments = [payment for payment in payments if payment.status == 'pending']
    completed_payments = [payment for payment in payments if payment.status == 'completed']
    
    # Recent financial activity
    recent_bills = sorted(bills, key=lambda x: x.created_at, reverse=True)[:5]
    recent_payments = sorted(payments, key=lambda x: x.created_at, reverse=True)[:5]
    
    return render_template('finance.html', 
                          provider=provider,
                          bills=bills,
                          payments=payments,
                          total_billed=total_billed,
                          total_received=total_received,
                          outstanding_amount=outstanding_amount,
                          pending_bills=pending_bills,
                          paid_bills=paid_bills,
                          pending_payments=pending_payments,
                          completed_payments=completed_payments,
                          recent_bills=recent_bills,
                          recent_payments=recent_payments)

# Redirect old billing route to new finance route
@app.route('/billing')
@login_required
def billing():
    """Redirect to unified finance dashboard"""
    return redirect(url_for('finance'))

# Redirect old payments route to new finance route
@app.route('/payments')
@login_required
def payments():
    """Redirect to unified finance dashboard"""
    return redirect(url_for('finance'))

@app.route('/billing/create', methods=['GET', 'POST'])
@login_required
def create_bill():
    """Create a new bill"""
    provider = Provider.get_by_user_id(current_user.id)
    patients = Patient.get_all()
    appointments = Appointment.get_by_provider(provider.id)
    
    if request.method == 'POST':
        patient_id = int(request.form.get('patient_id'))
        appointment_id = int(request.form.get('appointment_id')) if request.form.get('appointment_id') else None
        
        bill = Bill.create(patient_id, provider.id, appointment_id)
        flash('New bill created successfully.', 'success')
        return redirect(url_for('edit_bill', bill_id=bill.id))
    
    return render_template('create_bill.html', 
                          provider=provider,
                          patients=patients,
                          appointments=appointments)

@app.route('/billing/<int:bill_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bill(bill_id):
    """Edit bill and add items"""
    provider = Provider.get_by_user_id(current_user.id)
    bill = Bill.get_by_id(bill_id)
    
    if not bill:
        flash('Bill not found.', 'danger')
        return redirect(url_for('billing'))
    
    form = BillItemForm()
    
    if form.validate_on_submit():
        bill.add_item(
            form.item_type.data,
            form.description.data,
            float(form.amount.data),
            form.quantity.data
        )
        flash('Item added to bill successfully.', 'success')
        return redirect(url_for('edit_bill', bill_id=bill.id))
    
    return render_template('edit_bill.html', 
                          provider=provider,
                          bill=bill,
                          form=form)

@app.route('/billing/record-payment', methods=['GET', 'POST'])
@login_required
def record_payment():
    """Record a payment against a bill"""
    provider = Provider.get_by_user_id(current_user.id)
    form = PaymentRecordForm()
    
    # Get unpaid/partially paid bills
    bills = Bill.get_by_provider(provider.id)
    unpaid_bills = [b for b in bills if b.status in ['pending', 'partially_paid']]
    
    form.bill_id.choices = [(str(b.id), f"Bill #{b.id} - {b.patient.name} (KSh {b.total_amount})") for b in unpaid_bills]
    
    if form.validate_on_submit():
        bill = Bill.get_by_id(int(form.bill_id.data))
        if bill:
            # Create payment record
            payment = Payment.create(
                None,  # No appointment_id for direct bill payments
                float(form.amount.data),
                bill.patient.phone_number,
                form.payment_method.data
            )
            
            if form.reference.data:
                payment.mpesa_reference = form.reference.data
            
            # Update payment status to completed
            Payment.update_status(payment.id, 'completed', form.reference.data)
            
            # Update bill status based on payment
            total_paid = float(form.amount.data)  # In real system, sum all payments for this bill
            if total_paid >= bill.total_amount:
                bill.status = 'paid'
                bill.paid_at = datetime.now()
            else:
                bill.status = 'partially_paid'
            
            flash('Payment recorded successfully.', 'success')
            return redirect(url_for('finance'))
    
    return render_template('record_payment.html', 
                          provider=provider,
                          form=form)

@app.route('/update_bill_status', methods=['POST'])
@login_required
def update_bill_status():
    """Update bill status"""
    bill_id = request.form.get('bill_id')
    status = request.form.get('status')
    
    if not bill_id or not status:
        flash('Bill ID and status are required.', 'danger')
        return redirect(url_for('finance'))
    
    try:
        bill = Bill.get_by_id(int(bill_id))
        if not bill:
            flash('Bill not found.', 'danger')
            return redirect(url_for('finance'))
        
        bill.status = status
        if status == 'paid':
            bill.paid_at = datetime.now()
        
        flash(f'Bill #{bill_id} status updated to {status}.', 'success')
    except ValueError:
        flash('Invalid bill ID.', 'danger')
    except Exception as e:
        flash(f'Error updating bill status: {str(e)}', 'danger')
    
    return redirect(url_for('finance'))

# ===== SUPER ADMIN INTERFACE =====

@app.route('/admin_dashboard')
@login_required
@requires_permission('user_management')
def admin_dashboard():
    """Super Admin Dashboard - Only accessible by super_admin"""
    if not hasattr(current_user, 'role') or current_user.role != 'super_admin':
        flash('Access denied. Super admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get system statistics
    total_users = len(db['users'])
    total_patients = len(db['patients'])
    total_appointments = len(db['appointments'])
    total_bills = len(db['bills'])
    
    # Get department statistics
    department_stats = {}
    for user in db['users']:
        dept = user.department
        if dept not in department_stats:
            department_stats[dept] = 0
        department_stats[dept] += 1
    
    # Recent activities
    recent_users = sorted(db['users'], key=lambda x: x.created_at, reverse=True)[:5]
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         total_bills=total_bills,
                         department_stats=department_stats,
                         recent_users=recent_users)

@app.route('/manage_users')
@login_required
@requires_permission('user_management')
def manage_users():
    """Manage system users"""
    if not hasattr(current_user, 'role') or current_user.role != 'super_admin':
        flash('Access denied. Super admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = db['users']
    return render_template('manage_users.html', users=users)

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
@requires_permission('user_management')
def create_user():
    """Create new system user"""
    if not hasattr(current_user, 'role') or current_user.role != 'super_admin':
        flash('Access denied. Super admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = UserManagementForm()
    
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = next((u for u in db['users'] if u.username == form.username.data), None)
        if existing_user:
            flash('Username already exists.', 'danger')
            return render_template('create_user.html', form=form)
        
        # Create new user
        new_id = max([u.id for u in db['users']], default=0) + 1
        password_hash = f"hashed_{form.password.data}"
        
        new_user = User(
            id=new_id,
            username=form.username.data,
            email=form.email.data,
            password_hash=password_hash,
            role=form.role.data,
            department=form.department.data,
            permissions=form.permissions.data
        )
        
        db['users'].append(new_user)
        flash(f'User {form.username.data} created successfully.', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('create_user.html', form=form)

@app.route('/manage_departments')
@login_required
@requires_permission('user_management')
def manage_departments():
    """Manage departments and permissions"""
    if not hasattr(current_user, 'role') or current_user.role != 'super_admin':
        flash('Access denied. Super admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Group users by department
    departments = {}
    for user in db['users']:
        dept = user.department
        if dept not in departments:
            departments[dept] = []
        departments[dept].append(user)
    
    return render_template('manage_departments.html', departments=departments)

# ===== DEPARTMENT-SPECIFIC DASHBOARDS =====

@app.route('/finance_dashboard')
@login_required
@requires_department('finance')
def finance_dashboard():
    """Finance Department Dashboard"""
    if not hasattr(current_user, 'can_access_department') or not current_user.can_access_department('finance'):
        flash('Access denied. Finance department access required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Finance-specific statistics with safe handling
    total_bills = len(db.get('bills', []))
    total_payments = len(db.get('payments', []))
    pending_bills = len([b for b in db.get('bills', []) if hasattr(b, 'status') and b.status == 'pending'])
    paid_bills = len([b for b in db.get('bills', []) if hasattr(b, 'status') and b.status == 'paid'])
    
    # Calculate total revenue
    total_revenue = sum([p.amount for p in db.get('payments', []) if hasattr(p, 'amount') and hasattr(p, 'status') and p.status == 'completed'])
    pending_revenue = sum([b.total_amount for b in db.get('bills', []) if hasattr(b, 'total_amount') and hasattr(b, 'status') and b.status == 'pending'])
    
    # Recent financial activities with safe sorting
    recent_bills = sorted([b for b in db.get('bills', []) if hasattr(b, 'created_at')], 
                         key=lambda x: x.created_at if hasattr(x.created_at, 'date') else datetime.now(), 
                         reverse=True)[:5]
    recent_payments = sorted([p for p in db.get('payments', []) if hasattr(p, 'created_at')], 
                            key=lambda x: x.created_at if hasattr(x.created_at, 'date') else datetime.now(), 
                            reverse=True)[:5]
    
    return render_template('finance_dashboard.html',
                         total_bills=total_bills,
                         total_payments=total_payments,
                         pending_bills=pending_bills,
                         paid_bills=paid_bills,
                         total_revenue=total_revenue,
                         pending_revenue=pending_revenue,
                         recent_bills=recent_bills,
                         recent_payments=recent_payments)

@app.route('/lab_dashboard')
@login_required
@requires_department('laboratory')
def lab_dashboard():
    """Laboratory Department Dashboard"""
    if not hasattr(current_user, 'can_access_department') or not current_user.can_access_department('laboratory'):
        flash('Access denied. Laboratory department access required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Enhanced lab statistics with USSD data integration
    total_tests = len(db.get('lab_tests', []))
    pending_tests = len([t for t in db.get('lab_tests', []) if hasattr(t, 'status') and t.status == 'ordered'])
    completed_tests = len([t for t in db.get('lab_tests', []) if hasattr(t, 'status') and t.status == 'completed'])
    
    # Tests ordered via USSD today
    today = datetime.now().date()
    ussd_tests_today = len([t for t in db.get('lab_tests', []) 
                           if hasattr(t, 'ordered_at') and hasattr(t, 'source') and 
                           t.source == 'ussd' and t.ordered_at.date() == today])
    
    # Recent lab activities from USSD
    recent_tests = sorted([t for t in db.get('lab_tests', []) if hasattr(t, 'ordered_at')], 
                         key=lambda x: x.ordered_at, reverse=True)[:5]
    
    # Sample collection queue
    collection_queue = [t for t in db.get('lab_tests', []) 
                       if hasattr(t, 'status') and t.status == 'ordered'][:10]
    
    return render_template('lab_dashboard.html',
                         total_tests=total_tests,
                         pending_tests=pending_tests,
                         completed_tests=completed_tests,
                         ussd_tests_today=ussd_tests_today,
                         recent_tests=recent_tests,
                         collection_queue=collection_queue)

@app.route('/pharmacy_dashboard')
@login_required
@requires_department('pharmacy')
def pharmacy_dashboard():
    """Pharmacy Department Dashboard"""
    if not hasattr(current_user, 'can_access_department') or not current_user.can_access_department('pharmacy'):
        flash('Access denied. Pharmacy department access required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Pharmacy statistics with USSD integration
    pending_prescriptions = len([p for p in db.get('prescriptions', []) if hasattr(p, 'status') and p.status == 'pending'])
    
    # Prescriptions dispensed today
    today = datetime.now().date()
    dispensed_today = len([p for p in db.get('prescriptions', []) 
                          if hasattr(p, 'dispensed_at') and hasattr(p, 'status') and 
                          p.status == 'dispensed' and p.dispensed_at.date() == today])
    
    # Mock inventory data for low stock alerts
    low_stock_items = 5  # Would come from inventory system
    delivery_requests = len([p for p in db.get('prescriptions', []) 
                           if hasattr(p, 'delivery_method') and p.delivery_method == 'delivery'])
    
    # Recent prescriptions from USSD consultations
    recent_prescriptions = sorted([p for p in db.get('prescriptions', []) if hasattr(p, 'created_at')], 
                                 key=lambda x: x.created_at, reverse=True)[:5]
    
    # Sample drug interaction alerts
    drug_interactions = [
        {'patient_id': 1, 'warning': 'Warfarin and Aspirin interaction - bleeding risk'},
        {'patient_id': 3, 'warning': 'ACE inhibitor and Potassium supplement - hyperkalemia risk'}
    ]
    
    # Sample inventory items
    inventory_items = [
        {'id': 1, 'drug_name': 'Paracetamol 500mg', 'current_stock': 50, 'minimum_stock': 100, 'unit': 'tablets', 'last_restocked': '2025-06-20'},
        {'id': 2, 'drug_name': 'Amoxicillin 250mg', 'current_stock': 200, 'minimum_stock': 150, 'unit': 'capsules', 'last_restocked': '2025-06-18'},
        {'id': 3, 'drug_name': 'ORS Sachets', 'current_stock': 25, 'minimum_stock': 50, 'unit': 'sachets', 'last_restocked': '2025-06-15'},
        {'id': 4, 'drug_name': 'Insulin (Human)', 'current_stock': 0, 'minimum_stock': 10, 'unit': 'vials', 'last_restocked': None}
    ]
    
    return render_template('pharmacy_dashboard.html',
                         pending_prescriptions=pending_prescriptions,
                         dispensed_today=dispensed_today,
                         low_stock_items=low_stock_items,
                         delivery_requests=delivery_requests,
                         recent_prescriptions=recent_prescriptions,
                         drug_interactions=drug_interactions,
                         inventory_items=inventory_items)
    
    # Lab-specific statistics with safe handling
    total_tests = len(db.get('lab_tests', []))
    pending_tests = len([t for t in db.get('lab_tests', []) if hasattr(t, 'status') and t.status == 'pending'])
    completed_tests = len([t for t in db.get('lab_tests', []) if hasattr(t, 'status') and t.status == 'completed'])
    in_progress_tests = len([t for t in db.get('lab_tests', []) if hasattr(t, 'status') and t.status == 'in_progress'])
    
    # Recent lab activities with safe sorting
    recent_tests = sorted([t for t in db.get('lab_tests', []) if hasattr(t, 'created_at')], 
                         key=lambda x: x.created_at if hasattr(x.created_at, 'date') else datetime.now(), 
                         reverse=True)[:10]
    
    # Get lab results that need processing
    pending_results = len([r for r in db.get('lab_results', []) if hasattr(r, 'status') and r.status == 'pending'])
    
    return render_template('lab_dashboard.html',
                         total_tests=total_tests,
                         pending_tests=pending_tests,
                         completed_tests=completed_tests,
                         in_progress_tests=in_progress_tests,
                         pending_results=pending_results,
                         recent_tests=recent_tests)

@app.route('/clinical_dashboard')
@login_required
@requires_department('clinical')
def clinical_dashboard():
    """Clinical Department Dashboard"""
    if not hasattr(current_user, 'can_access_department') or not current_user.can_access_department('clinical'):
        flash('Access denied. Clinical department access required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Enhanced clinical statistics with USSD integration
    total_patients = len(db['patients'])
    total_appointments = len(db['appointments'])
    
    # USSD-originated consultations today
    today = datetime.now().date()
    today_appointments = 0
    ussd_consultations_today = 0
    try:
        today_appointments = len([a for a in db['appointments'] if hasattr(a, 'date') and 
                                 (a.date.date() == today if hasattr(a.date, 'date') else 
                                  datetime.strptime(str(a.date), '%Y-%m-%d').date() == today)])
        # Track USSD-originated consultations
        ussd_consultations_today = len([a for a in db['appointments'] if hasattr(a, 'source') and 
                                       a.source == 'ussd' and hasattr(a, 'date') and 
                                       a.date.date() == today])
    except:
        today_appointments = 0
        ussd_consultations_today = 0
    
    # Prescription management from USSD
    pending_prescriptions = len([p for p in db.get('prescriptions', []) if hasattr(p, 'status') and p.status == 'pending'])
    ussd_prescriptions = len([p for p in db.get('prescriptions', []) if hasattr(p, 'source') and p.source == 'ussd'])
    
    # Active USSD patient symptoms tracking
    active_symptoms = len([p for p in db['patients'] if hasattr(p, 'symptoms') and p.symptoms])
    
    # Emergency alerts from USSD
    emergency_alerts = len([p for p in db['patients'] if hasattr(p, 'symptoms') and 
                           any('severe' in str(symptom).lower() or 'emergency' in str(symptom).lower() 
                               for symptom in p.symptoms)])
    
    # Recent clinical activities with safe sorting
    recent_appointments = sorted([a for a in db['appointments'] if hasattr(a, 'created_at')], 
                                key=lambda x: x.created_at if hasattr(x.created_at, 'date') else datetime.now(), 
                                reverse=True)[:5]
    recent_prescriptions = sorted([p for p in db.get('prescriptions', []) if hasattr(p, 'created_at')], 
                                 key=lambda x: x.created_at if hasattr(x.created_at, 'date') else datetime.now(), 
                                 reverse=True)[:5]
    
    return render_template('clinical_dashboard.html',
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         today_appointments=today_appointments,
                         ussd_consultations_today=ussd_consultations_today,
                         pending_prescriptions=pending_prescriptions,
                         ussd_prescriptions=ussd_prescriptions,
                         active_symptoms=active_symptoms,
                         emergency_alerts=emergency_alerts,
                         recent_appointments=recent_appointments,
                         recent_prescriptions=recent_prescriptions)

# ===== ROLE-BASED ACCESS CONTROL =====

@app.route('/user_profile')
@login_required
def user_profile():
    """Display current user's profile and permissions"""
    user_permissions = getattr(current_user, 'permissions', [])
    user_department = getattr(current_user, 'department', 'None')
    user_role = getattr(current_user, 'role', 'user')
    
    accessible_routes = utils.get_user_accessible_routes()
    
    return render_template('user_profile.html',
                         user=current_user,
                         user_permissions=user_permissions,
                         user_department=user_department,
                         user_role=user_role,
                         accessible_routes=accessible_routes)

@app.route('/system_status')
@login_required
@requires_permission('reports')
def system_status():
    """System status and health check"""
    if not hasattr(current_user, 'role') or current_user.role != 'super_admin':
        flash('Access denied. Super admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # System health metrics
    system_stats = {
        'total_users': len(db['users']),
        'total_patients': len(db['patients']),
        'total_providers': len(db['providers']),
        'total_appointments': len(db['appointments']),
        'total_messages': len(db['messages']),
        'total_bills': len(db['bills']),
        'total_payments': len(db['payments']),
        'total_prescriptions': len(db['prescriptions']),
        'total_lab_tests': len(db['lab_tests']),
        'active_walk_ins': len([w for w in db['walk_in_patients'] if w.status == 'waiting'])
    }
    
    return render_template('system_status.html', system_stats=system_stats)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

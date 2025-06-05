import os
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Provider, Patient, Appointment, Message, HealthInfo, UserInteraction, Payment, db, init_db
from forms import LoginForm, MessageForm, HealthInfoForm, HealthTipsForm, HealthEducationForm
from ussd_handler import ussd_callback
import utils
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

# Payment routes
@app.route('/payments')
@login_required
def payments():
    """Payment dashboard for managing appointment payments"""
    provider = Provider.get_by_user_id(current_user.id)
    
    # Get all payment records
    all_payments = Payment.get_all()
    
    # Enhance payment data with patient and appointment info
    for payment in all_payments:
        appointment = Appointment.get_by_id(payment.appointment_id)
        if appointment:
            payment.appointment = appointment
            payment.patient = Patient.get_by_id(appointment.patient_id)
    
    # Get pending appointments (for creating new payments)
    pending_appointments = []
    all_appointments = Appointment.get_by_provider(provider.id)
    for appointment in all_appointments:
        if appointment.payment_status == 'pending' and appointment.price:
            appointment.patient = Patient.get_by_id(appointment.patient_id)
            pending_appointments.append(appointment)
    
    # Get payment summary statistics
    payment_summary = Payment.generate_payment_summary()
    
    return render_template('payments.html', 
                          provider=provider,
                          payments=all_payments,
                          pending_appointments=pending_appointments,
                          payment_summary=payment_summary)

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
import logging
from datetime import datetime
from urllib.parse import urlparse

import click
from dotenv import load_dotenv
from flask import (Flask, render_template, redirect, url_for, request, flash, session, jsonify,
                   abort, send_from_directory)
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

from models import (User, Provider, Patient, Appointment, Message, HealthInfo, UserInteraction, Payment,
                    Prescription, WalkInPatient, LabTest, LabResult, Bill, db)
from forms import (LoginForm, RegistrationForm, MessageForm, HealthInfoForm, HealthTipsForm, HealthEducationForm,
                   PrescriptionForm, WalkInForm, QuickPatientForm, LabTestForm, LabResultForm,
                   BillItemForm, PaymentRecordForm, UserManagementForm, DepartmentForm)
from ussd_handler import ussd_callback
import utils
from utils import requires_permission, requires_department, get_navigation_items


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


# ---------------------------------------------------------------------------
# Configuration (everything comes from environment variables; see .env.example)
# ---------------------------------------------------------------------------
APP_ENV = os.environ.get('APP_ENV', 'development').lower()
IS_PRODUCTION = APP_ENV == 'production'

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO' if IS_PRODUCTION else 'DEBUG').upper(),
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

# AI content generation: the offline mock is the default; set USE_MOCK_AI=false
# (plus OPENAI_API_KEY / ANTHROPIC_API_KEY) to use the real providers.
if _env_bool('USE_MOCK_AI', True):
    import mock_ai_service as ai_service
else:
    import ai_service

app = Flask(__name__)

secret_key = os.environ.get('SECRET_KEY') or os.environ.get('SESSION_SECRET')
if not secret_key:
    if IS_PRODUCTION:
        raise RuntimeError('SECRET_KEY must be set when APP_ENV=production')
    secret_key = 'dev-only-insecure-secret-key'
    logger.warning('SECRET_KEY is not set; using an insecure development key')

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    if IS_PRODUCTION:
        raise RuntimeError('DATABASE_URL must be set when APP_ENV=production')
    database_url = 'sqlite:///' + os.path.join(app.instance_path, 'tujali.db')
    os.makedirs(app.instance_path, exist_ok=True)
# Some hosts (Heroku, Render, older Neon snippets) hand out postgres:// URLs.
if database_url.startswith('postgres://'):
    database_url = 'postgresql://' + database_url[len('postgres://'):]

app.config.update(
    SECRET_KEY=secret_key,
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True},
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=_env_bool('SESSION_COOKIE_SECURE', IS_PRODUCTION),
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SECURE=_env_bool('SESSION_COOKIE_SECURE', IS_PRODUCTION),
    WTF_CSRF_TIME_LIMIT=None,
    ALLOW_REGISTRATION=_env_bool('ALLOW_REGISTRATION', not IS_PRODUCTION),
    ENABLE_USSD_SIMULATOR=_env_bool('ENABLE_USSD_SIMULATOR', not IS_PRODUCTION),
)

if _env_bool('BEHIND_PROXY', IS_PRODUCTION):
    # Trust X-Forwarded-* from one reverse proxy (load balancer / nginx / Passenger).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

from filters import register_filters
register_filters(app)


@app.template_filter('now')
def _jinja2_filter_now():
    """Return current datetime for templates"""
    return datetime.now()


@app.context_processor
def inject_settings():
    return {'allow_registration': app.config['ALLOW_REGISTRATION']}


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


@app.after_request
def set_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    if IS_PRODUCTION:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


@app.errorhandler(403)
def forbidden(error):
    message = getattr(error, 'description', None)
    if not message or message.startswith("You don't have the permission"):
        message = 'You do not have permission to view this page.'
    return render_template('error.html', code=403, message=message), 403


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', code=404, message='Page not found.'), 404


@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    logger.exception('Unhandled server error')
    return render_template('error.html', code=500,
                           message='Something went wrong. Please try again.'), 500


def _safe_next_url(target):
    """Only allow relative redirects after login (prevents open redirects)."""
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith('/'):
        return None
    return target


def _require_provider():
    """Provider profile of the logged-in user, or a 403 page if the account has none
    (e.g. finance or lab staff opening a provider-only page)."""
    provider = Provider.get_by_user_id(current_user.id)
    if provider is None:
        abort(403, description='This page is only available to accounts linked to a provider profile.')
    return provider


# ---------------------------------------------------------------------------
# CLI commands: flask create-admin / flask seed-demo
# ---------------------------------------------------------------------------

@app.cli.command('create-admin')
@click.option('--username', default=lambda: os.environ.get('ADMIN_USERNAME', 'admin'))
@click.option('--email', default=lambda: os.environ.get('ADMIN_EMAIL', 'admin@example.com'))
@click.option('--password', default=lambda: os.environ.get('ADMIN_PASSWORD'),
              help='Defaults to $ADMIN_PASSWORD; prompted for if unset.')
def create_admin_command(username, email, password):
    """Create the super-admin account (or reset its password)."""
    from seed import create_admin
    if not password:
        password = click.prompt('Admin password', hide_input=True, confirmation_prompt=True)
    if len(password) < 12:
        raise click.BadParameter('use at least 12 characters', param_hint='password')
    _, created = create_admin(username, password, email)
    click.echo(f"Super admin '{username}' {'created' if created else 'updated'}.")


@app.cli.command('seed-demo')
@click.option('--admin-password', default='admin123', show_default=True)
def seed_demo_command(admin_password):
    """Load demo data into an empty database (development/staging only)."""
    if IS_PRODUCTION:
        raise click.ClickException('Refusing to load demo data when APP_ENV=production.')
    from seed import seed_demo_data
    if seed_demo_data(admin_password):
        click.echo('Demo data loaded.')
    else:
        click.echo('Database already has patients; demo data not loaded.')


# ---------------------------------------------------------------------------
# Health check and USSD
# ---------------------------------------------------------------------------

@app.route('/healthz')
def healthz():
    """Liveness/readiness probe for the host: checks the database connection."""
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify(status='ok'), 200
    except Exception:
        logger.exception('Health check failed')
        return jsonify(status='error'), 503


@app.route('/ussd_simulator.html')
def ussd_simulator():
    """Serve the browser USSD simulator (disabled in production by default)."""
    if not app.config['ENABLE_USSD_SIMULATOR']:
        abort(404)
    return send_from_directory(app.root_path, 'ussd_simulator.html')

USSD_ALLOWED_IPS = {ip.strip() for ip in os.environ.get('USSD_ALLOWED_IPS', '').split(',') if ip.strip()}


@app.route('/ussd', methods=['POST'])
@csrf.exempt
def ussd():
    """Handle USSD requests from Africa's Talking (form-encoded POST)."""
    if USSD_ALLOWED_IPS and request.remote_addr not in USSD_ALLOWED_IPS:
        logger.warning('Rejected USSD request from %s', request.remote_addr)
        abort(403)

    session_id = request.form.get('sessionId', '').strip()
    service_code = request.form.get('serviceCode', '')
    phone_number = request.form.get('phoneNumber', '').strip()
    ussd_text = request.form.get('text', '')
    if not session_id or not phone_number:
        return 'END Invalid request', 400, {'Content-Type': 'text/plain; charset=utf-8'}

    logger.info('USSD request session=%s step=%d', session_id, len(ussd_text.split('*')) if ussd_text else 0)
    response = ussd_callback(session_id, service_code, phone_number, ussd_text)
    return response, 200, {'Content-Type': 'text/plain; charset=utf-8'}

# Web routes for provider dashboard
@app.route('/')
def index():
    """Landing page with login option"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for staff"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data.strip())
        if user and user.is_active and user.check_password(form.password.data):
            session.clear()
            login_user(user, remember=bool(getattr(form, 'remember', None) and form.remember.data))
            logger.info('User %s logged in', user.id)
            return redirect(_safe_next_url(request.args.get('next')) or url_for('dashboard'))
        logger.info('Failed login attempt')
        flash('Invalid username or password.', 'danger')

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Self-service provider registration (off by default in production)."""
    if not app.config['ALLOW_REGISTRATION']:
        abort(404)
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.username_exists(form.username.data):
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form)
        
        if User.email_exists(form.email.data):
            flash('Email already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form)
        
        user = User.create(form.username.data, form.email.data, form.password.data, role='provider')
        
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
            elif current_user.department == 'pharmacy':
                return redirect(url_for('pharmacy_dashboard'))

    # Default provider dashboard
    provider = Provider.get_by_user_id(current_user.id)

    total_patients = Patient.get_count()
    recent_patients = Patient.get_recent(5)

    if provider:
        recent_appointments = Appointment.get_recent_by_provider(provider.id, 5)
        recent_messages = Message.get_recent_by_provider(provider.id, 5)
        recent_prescriptions = sorted(Prescription.get_by_provider(provider.id),
                                      key=lambda p: p.created_at, reverse=True)[:5]
        pending_appointments = Appointment.get_count_by_status(provider.id, 'pending')
        unread_messages = Message.get_unread_count(provider.id)
        provider_payments = Payment.get_by_provider(provider.id)
    else:
        recent_appointments, recent_messages, recent_prescriptions = [], [], []
        pending_appointments = unread_messages = 0
        provider_payments = []

    payment_summary = Payment.generate_payment_summary(provider_payments)

    return render_template('dashboard.html',
                           provider=provider,
                           total_patients=total_patients,
                           recent_patients=recent_patients,
                           recent_appointments=recent_appointments,
                           recent_messages=recent_messages,
                           recent_prescriptions=recent_prescriptions,
                           pending_appointments=pending_appointments,
                           unread_messages=unread_messages,
                           payment_summary=payment_summary,
                           nav_items=get_navigation_items())

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
    provider = _require_provider()
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
    provider = _require_provider()
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
    
    success = Appointment.update_status(appointment_id, status)
    
    if success:
        flash('Appointment updated successfully.', 'success')
    else:
        flash('Failed to update appointment.', 'danger')
    
    return redirect(url_for('appointments'))

@app.route('/messages')
@login_required
def messages():
    """Message center for provider"""
    provider = _require_provider()
    conversations = Message.get_conversations(provider.id)
    return render_template('messages.html', provider=provider, conversations=conversations)

@app.route('/messages/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def patient_messages(patient_id):
    """Messages with a specific patient"""
    provider = _require_provider()
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
            
            generated_tips = ai_service.generate_health_tips(patient_data, symptoms, language)

            # Store in session for sharing with the patient
            session['last_generated_tips'] = generated_tips
            session['last_tips_patient_id'] = patient.id

            flash('Health tips generated successfully.', 'success')
        except Exception as e:
            logger.exception("Error generating health tips")
            flash('Could not generate health tips. Please try again.', 'danger')
    
    return render_template('health_tips.html', 
                          provider=provider,
                          form=form,
                          generated_tips=generated_tips,
                          selected_patient=selected_patient)

@app.route('/health-tips/share/<int:patient_id>', methods=['POST'])
@login_required
def share_health_tips(patient_id):
    """Share generated health tips with a patient via SMS"""
    provider = _require_provider()
    
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
            
            generated_content = ai_service.generate_health_education(topic, language)

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
                
        except Exception:
            logger.exception("Error generating health education content")
            flash('Could not generate health education content. Please try again.', 'danger')
    
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
    
    counts = UserInteraction.count_by_patient()
    for patient in patients:
        patient.interaction_count = counts.get(patient.id, 0)
    
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
    if journey_data is None:
        abort(404)
    return jsonify(journey_data)


# Add interaction tracking hooks to existing functions

def track_interaction(patient_id, interaction_type, description, metadata=None):
    """Helper function to track user interactions"""
    try:
        UserInteraction.create(patient_id, interaction_type, description, metadata)
    except Exception:
        db.session.rollback()
        logger.exception("Error tracking interaction")


# Hook into patient message route to track interactions
old_patient_messages = app.view_functions['patient_messages']

def patient_messages_with_tracking(patient_id):
    """Wrap patient_messages to track interactions"""
    patient = Patient.get_by_id(patient_id)

    if request.method == 'POST' and patient:
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
    patient = Patient.get_by_id(patient_id)
    if request.method == 'POST' and patient and session.get('last_tips_patient_id') == patient_id:
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
    try:
        amount = float(amount)
    except ValueError:
        flash('Amount must be a number.', 'danger')
        return redirect(url_for('payments'))

    appointment = Appointment.get_by_id(appointment_id)
    if not appointment:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('payments'))
    
    patient = Patient.get_by_id(appointment.patient_id)
    if not patient:
        flash('Patient not found.', 'danger')
        return redirect(url_for('payments'))
    
    # Create payment record
    payment = Payment.create(
        appointment.id,
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
    
    payment = Payment.get_by_id(payment_id)
    if not payment:
        flash('Payment not found.', 'danger')
        return redirect(url_for('payments'))
    
    # Update payment status
    success = Payment.update_status(payment_id, status)
    
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
    provider = _require_provider()
    prescription_list = Prescription.get_by_provider(provider.id)
    return render_template('prescriptions.html', provider=provider, prescriptions=prescription_list)

@app.route('/prescriptions/create', methods=['GET', 'POST'])
@login_required
def create_prescription():
    """Create a new prescription"""
    provider = _require_provider()
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
        patient = Patient.get_by_id(form.patient_id.data)
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
    provider = _require_provider()
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
    provider = _require_provider()
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
    
    provider = _require_provider()
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
    provider = _require_provider()
    test_list = LabTest.get_by_provider(provider.id)
    return render_template('lab_tests.html', provider=provider, lab_tests=test_list)

@app.route('/lab-tests/order', methods=['GET', 'POST'])
@login_required
def order_lab_test():
    """Order a new lab test"""
    provider = _require_provider()
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
        patient = Patient.get_by_id(form.patient_id.data)
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
    provider = _require_provider()
    
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
    provider = _require_provider()
    patients = Patient.get_all()
    appointments = Appointment.get_by_provider(provider.id)
    
    if request.method == 'POST':
        patient = Patient.get_by_id(request.form.get('patient_id'))
        if not patient:
            flash('Please choose a valid patient.', 'danger')
            return redirect(url_for('create_bill'))
        appointment = Appointment.get_by_id(request.form.get('appointment_id'))

        bill = Bill.create(patient.id, provider.id, appointment.id if appointment else None)
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
    provider = _require_provider()
    form = PaymentRecordForm()
    
    # Get unpaid/partially paid bills
    bills = Bill.get_by_provider(provider.id)
    unpaid_bills = [b for b in bills if b.status in ['pending', 'partially_paid']]
    
    form.bill_id.choices = [(str(b.id), f"Bill #{b.id} - {b.patient.name} (KSh {b.total_amount})") for b in unpaid_bills]
    
    if form.validate_on_submit():
        bill = Bill.get_by_id(form.bill_id.data)
        if bill:
            payment = Payment.create(
                None,  # No appointment_id for direct bill payments
                float(form.amount.data),
                bill.patient.phone_number,
                form.payment_method.data,
                bill_id=bill.id,
            )
            Payment.update_status(payment.id, 'completed', form.reference.data or None)

            # Bill status reflects everything paid against it so far
            if bill.amount_paid >= bill.total_amount:
                bill.status = 'paid'
                bill.paid_at = datetime.now()
            else:
                bill.status = 'partially_paid'
            db.session.commit()

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
        bill = Bill.get_by_id(bill_id)
        if not bill:
            flash('Bill not found.', 'danger')
            return redirect(url_for('finance'))
        
        if status not in ('pending', 'partially_paid', 'paid', 'cancelled'):
            flash('Invalid bill status.', 'danger')
            return redirect(url_for('finance'))

        bill.status = status
        if status == 'paid':
            bill.paid_at = datetime.now()
        db.session.commit()

        flash(f'Bill #{bill_id} status updated to {status}.', 'success')
    except ValueError:
        flash('Invalid bill ID.', 'danger')
    except Exception:
        db.session.rollback()
        logger.exception('Error updating bill status')
        flash('Error updating bill status.', 'danger')
    
    return redirect(url_for('finance'))

# ===== SUPER ADMIN INTERFACE =====

def _require_super_admin():
    if current_user.role != 'super_admin':
        abort(403, description='Super admin privileges required.')


@app.route('/admin_dashboard')
@login_required
@requires_permission('user_management')
def admin_dashboard():
    """Super Admin Dashboard - Only accessible by super_admin"""
    _require_super_admin()

    users = User.get_all()
    department_stats = {}
    for user in users:
        department_stats[user.department] = department_stats.get(user.department, 0) + 1

    return render_template('admin_dashboard.html',
                           total_users=len(users),
                           total_patients=Patient.get_count(),
                           total_appointments=Appointment.query.count(),
                           total_bills=Bill.query.count(),
                           department_stats=department_stats,
                           recent_users=sorted(users, key=lambda u: u.created_at, reverse=True)[:5])


@app.route('/manage_users')
@login_required
@requires_permission('user_management')
def manage_users():
    """Manage system users"""
    _require_super_admin()
    return render_template('manage_users.html', users=User.get_all())


@app.route('/create_user', methods=['GET', 'POST'])
@login_required
@requires_permission('user_management')
def create_user():
    """Create new system user"""
    _require_super_admin()
    form = UserManagementForm()

    if form.validate_on_submit():
        if User.username_exists(form.username.data):
            flash('Username already exists.', 'danger')
            return render_template('create_user.html', form=form)
        if User.email_exists(form.email.data):
            flash('Email already exists.', 'danger')
            return render_template('create_user.html', form=form)

        User.create(form.username.data, form.email.data, form.password.data,
                    role=form.role.data, department=form.department.data,
                    permissions=form.permissions.data)
        flash(f'User {form.username.data} created successfully.', 'success')
        return redirect(url_for('manage_users'))

    return render_template('create_user.html', form=form)


@app.route('/manage_departments')
@login_required
@requires_permission('user_management')
def manage_departments():
    """Manage departments and permissions"""
    _require_super_admin()
    departments = {}
    for user in User.get_all():
        departments.setdefault(user.department or 'unassigned', []).append(user)
    return render_template('manage_departments.html', departments=departments)


# ===== DEPARTMENT-SPECIFIC DASHBOARDS =====

@app.route('/finance_dashboard')
@login_required
@requires_department('finance')
def finance_dashboard():
    """Finance Department Dashboard"""
    bills = Bill.get_all()
    payments = Payment.get_all()

    return render_template('finance_dashboard.html',
                           total_bills=len(bills),
                           total_payments=len(payments),
                           pending_bills=len([b for b in bills if b.status == 'pending']),
                           paid_bills=len([b for b in bills if b.status == 'paid']),
                           total_revenue=sum(p.amount for p in payments if p.status == 'completed'),
                           pending_revenue=sum(b.total_amount for b in bills if b.status == 'pending'),
                           recent_bills=bills[:5],
                           recent_payments=payments[:5])


@app.route('/lab_dashboard')
@login_required
@requires_department('laboratory')
def lab_dashboard():
    """Laboratory Department Dashboard"""
    tests = LabTest.get_all()  # newest first
    today = datetime.now().date()

    return render_template('lab_dashboard.html',
                           total_tests=len(tests),
                           pending_tests=len([t for t in tests if t.status == 'ordered']),
                           completed_tests=len([t for t in tests if t.status == 'completed']),
                           ussd_tests_today=len([t for t in tests
                                                 if t.source == 'ussd' and t.ordered_at.date() == today]),
                           recent_tests=tests[:5],
                           collection_queue=[t for t in reversed(tests) if t.status == 'ordered'][:10])


@app.route('/pharmacy_dashboard')
@login_required
@requires_department('pharmacy')
def pharmacy_dashboard():
    """Pharmacy Department Dashboard"""
    prescriptions = Prescription.get_all()  # newest first
    today = datetime.now().date()

    # Inventory and interaction alerts are placeholders until an inventory
    # system is integrated.
    drug_interactions = [
        {'patient_id': 1, 'warning': 'Warfarin and Aspirin interaction - bleeding risk'},
        {'patient_id': 3, 'warning': 'ACE inhibitor and Potassium supplement - hyperkalemia risk'}
    ]
    inventory_items = [
        {'id': 1, 'drug_name': 'Paracetamol 500mg', 'current_stock': 50, 'minimum_stock': 100, 'unit': 'tablets', 'last_restocked': '2025-06-20'},
        {'id': 2, 'drug_name': 'Amoxicillin 250mg', 'current_stock': 200, 'minimum_stock': 150, 'unit': 'capsules', 'last_restocked': '2025-06-18'},
        {'id': 3, 'drug_name': 'ORS Sachets', 'current_stock': 25, 'minimum_stock': 50, 'unit': 'sachets', 'last_restocked': '2025-06-15'},
        {'id': 4, 'drug_name': 'Insulin (Human)', 'current_stock': 0, 'minimum_stock': 10, 'unit': 'vials', 'last_restocked': None}
    ]

    return render_template('pharmacy_dashboard.html',
                           pending_prescriptions=len([p for p in prescriptions if p.status == 'pending']),
                           dispensed_today=len([p for p in prescriptions
                                                if p.status == 'dispensed' and p.dispensed_at
                                                and p.dispensed_at.date() == today]),
                           low_stock_items=len([i for i in inventory_items
                                                if i['current_stock'] < i['minimum_stock']]),
                           delivery_requests=len([p for p in prescriptions
                                                  if p.delivery_method in ('bike', 'drone')]),
                           recent_prescriptions=prescriptions[:5],
                           drug_interactions=drug_interactions,
                           inventory_items=inventory_items)


def _is_today(date_str, today):
    """Appointment dates are stored as 'DD-MM-YYYY' strings (USSD input)."""
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(str(date_str), fmt).date() == today
        except (TypeError, ValueError):
            continue
    return False


@app.route('/clinical_dashboard')
@login_required
@requires_department('clinical')
def clinical_dashboard():
    """Clinical Department Dashboard"""
    today = datetime.now().date()
    appointments = Appointment.get_all()  # newest first
    prescriptions = Prescription.get_all()
    patients = Patient.get_all()

    todays = [a for a in appointments if _is_today(a.date, today)]
    emergency_alerts = len([p for p in patients
                            if any(s.severity == 'Severe' or 'emergency' in s.text.lower()
                                   for s in p.symptoms)])

    return render_template('clinical_dashboard.html',
                           total_patients=len(patients),
                           total_appointments=len(appointments),
                           today_appointments=len(todays),
                           ussd_consultations_today=len([a for a in todays if a.source == 'ussd']),
                           pending_prescriptions=len([p for p in prescriptions if p.status == 'pending']),
                           ussd_prescriptions=len([p for p in prescriptions if p.source == 'ussd']),
                           active_symptoms=len([p for p in patients if p.symptoms]),
                           emergency_alerts=emergency_alerts,
                           recent_appointments=appointments[:5],
                           recent_prescriptions=prescriptions[:5])


# ===== ROLE-BASED ACCESS CONTROL =====

@app.route('/user_profile')
@login_required
def user_profile():
    """Display current user's profile and permissions"""
    return render_template('user_profile.html',
                           user=current_user,
                           user_permissions=current_user.permissions or [],
                           user_department=current_user.department or 'None',
                           user_role=current_user.role,
                           accessible_routes=utils.get_user_accessible_routes())


@app.route('/system_status')
@login_required
@requires_permission('reports')
def system_status():
    """System status and health check"""
    _require_super_admin()

    try:
        db.session.execute(text('SELECT 1'))
        database_ok = True
    except Exception:
        logger.exception('Database check failed')
        database_ok = False

    system_stats = {
        'total_users': User.count(),
        'total_patients': Patient.get_count(),
        'total_providers': Provider.query.count(),
        'total_appointments': Appointment.query.count(),
        'total_messages': Message.count(),
        'total_bills': Bill.query.count(),
        'total_payments': Payment.query.count(),
        'total_prescriptions': Prescription.query.count(),
        'total_lab_tests': LabTest.query.count(),
        'active_walk_ins': WalkInPatient.count_by_status('waiting'),
    }

    return render_template('system_status.html', system_stats=system_stats,
                           database_ok=database_ok, app_env=APP_ENV)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=not IS_PRODUCTION)

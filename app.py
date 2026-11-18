"""Tujali: specialist care and outbreak early warning over USSD.

Configuration comes from environment variables (see .env.example).
"""
import logging
import os
from datetime import timedelta

import click
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

from models import db, now, Consultation  # noqa: E402
from reference import SPECIALTY_NAMES, SYNDROME_LABELS  # noqa: E402


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


APP_ENV = os.environ.get('APP_ENV', 'development').lower()
IS_PRODUCTION = APP_ENV == 'production'

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO' if IS_PRODUCTION else 'DEBUG').upper(),
    format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

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
    os.makedirs(app.instance_path, exist_ok=True)
    database_url = 'sqlite:///' + os.path.join(app.instance_path, 'tujali.db')
if database_url.startswith('postgres://'):
    database_url = 'postgresql://' + database_url[len('postgres://'):]

sms_backend = os.environ.get('SMS_BACKEND', 'console').lower()
if sms_backend == 'africastalking' and not (os.environ.get('AT_USERNAME') and os.environ.get('AT_API_KEY')):
    raise RuntimeError('SMS_BACKEND=africastalking needs AT_USERNAME and AT_API_KEY')

app.config.update(
    SECRET_KEY=secret_key,
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True},
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=_env_bool('SESSION_COOKIE_SECURE', IS_PRODUCTION),
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SECURE=_env_bool('SESSION_COOKIE_SECURE', IS_PRODUCTION),
    REMEMBER_COOKIE_DURATION=timedelta(days=14),
    WTF_CSRF_TIME_LIMIT=None,
    ENABLE_USSD_SIMULATOR=_env_bool('ENABLE_USSD_SIMULATOR', not IS_PRODUCTION),
    USSD_CODE=os.environ.get('USSD_CODE', '*384*4040#'),
    SMS_BACKEND=sms_backend,
    AT_USERNAME=os.environ.get('AT_USERNAME'),
    AT_API_KEY=os.environ.get('AT_API_KEY'),
    AT_SENDER_ID=os.environ.get('AT_SENDER_ID'),
    ALERT_SMS_LIMIT=int(os.environ.get('ALERT_SMS_LIMIT', '5000')),
)

if _env_bool('BEHIND_PROXY', IS_PRODUCTION):
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

import admin  # noqa: E402
import auth  # noqa: E402
import health  # noqa: E402
import portal  # noqa: E402
import public  # noqa: E402
from ussd import ussd_callback  # noqa: E402

auth.login_manager.init_app(app)
for blueprint in (public.bp, auth.bp, portal.bp, health.bp, admin.bp):
    app.register_blueprint(blueprint)


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

@app.context_processor
def template_globals():
    return {'ussd_code': app.config['USSD_CODE'], 'app_env': APP_ENV,
            'simulator_enabled': app.config['ENABLE_USSD_SIMULATOR'], 'now_hour': now().hour,
            'specialty_names': SPECIALTY_NAMES, 'syndrome_labels': SYNDROME_LABELS}


@app.template_filter('when')
def format_datetime(value, fmt='%a %d %b, %H:%M'):
    return value.strftime(fmt) if value else '—'


@app.template_filter('ago')
def time_ago(value):
    if not value:
        return '—'
    seconds = (now() - value).total_seconds()
    if seconds < 60:
        return 'just now'
    for unit, size in (('day', 86400), ('hour', 3600), ('minute', 60)):
        if seconds >= size:
            n = int(seconds // size)
            return f'{n} {unit}{"s" if n != 1 else ""} ago'
    return value.strftime('%d %b')


@app.template_filter('kes')
def kes(value):
    return f'KES {int(value or 0):,}'


@app.after_request
def security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    if IS_PRODUCTION:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


@app.errorhandler(403)
def forbidden(error):
    message = getattr(error, 'description', '') or ''
    if message.startswith("You don't have the permission"):
        message = 'You do not have access to this page.'
    return render_template('error.html', code=403, title='No access', message=message), 403


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', code=404, title='Page not found',
                           message="We couldn't find that page."), 404


@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    logger.exception('Unhandled server error')
    return render_template('error.html', code=500, title='Something went wrong',
                           message='Please try again in a moment.'), 500


# ---------------------------------------------------------------------------
# USSD gateway and health check
# ---------------------------------------------------------------------------

USSD_ALLOWED_IPS = {ip.strip() for ip in os.environ.get('USSD_ALLOWED_IPS', '').split(',') if ip.strip()}


@app.route('/ussd', methods=['POST'])
@csrf.exempt
def ussd():
    """Africa's Talking USSD callback (form-encoded POST)."""
    if USSD_ALLOWED_IPS and request.remote_addr not in USSD_ALLOWED_IPS:
        logger.warning('Rejected USSD request from %s', request.remote_addr)
        abort(403)
    session_id = request.form.get('sessionId', '').strip()
    phone = request.form.get('phoneNumber', '').strip()
    if not session_id or not phone:
        return 'END Invalid request', 400, {'Content-Type': 'text/plain; charset=utf-8'}
    response = ussd_callback(session_id, phone, request.form.get('text', ''))
    return response, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/healthz')
def healthz():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify(status='ok')
    except Exception:
        logger.exception('Health check failed')
        return jsonify(status='error'), 503


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@app.cli.command('create-admin')
@click.option('--name', default=lambda: os.environ.get('ADMIN_NAME', 'Tujali Admin'))
@click.option('--email', default=lambda: os.environ.get('ADMIN_EMAIL'))
@click.option('--password', default=lambda: os.environ.get('ADMIN_PASSWORD'),
              help='Defaults to $ADMIN_PASSWORD; prompted for if unset.')
def create_admin_command(name, email, password):
    """Create an administrator account (or reset its password)."""
    from seed import create_admin
    email = email or click.prompt('Admin email')
    if not password:
        password = click.prompt('Admin password', hide_input=True, confirmation_prompt=True)
    if len(password) < 12:
        raise click.BadParameter('use at least 12 characters', param_hint='password')
    _, created = create_admin(name, email, password)
    click.echo(f"Administrator {email} {'created' if created else 'updated'}.")


@app.cli.command('seed-demo')
def seed_demo_command():
    """Load demo data into an empty database (development/staging only)."""
    if IS_PRODUCTION:
        raise click.ClickException('Refusing to load demo data when APP_ENV=production.')
    from seed import seed_demo_data
    click.echo('Demo data loaded.' if seed_demo_data() else 'Database already has data; skipped.')


@app.cli.command('send-reminders')
@click.option('--hours', default=2, show_default=True, help='Remind about calls starting within this many hours.')
def send_reminders_command(hours):
    """SMS patients whose phone consultation starts soon. Run every 15-30 minutes from cron."""
    from i18n import t
    from sms import send_sms
    due = Consultation.query.filter(Consultation.status == 'booked',
                                    Consultation.mode == 'phone',
                                    Consultation.notified_at.is_(None),
                                    Consultation.scheduled_at > now(),
                                    Consultation.scheduled_at <= now() + timedelta(hours=hours)).all()
    for c in due:
        send_sms(c.patient.phone,
                 t('sms_reminder', c.patient.language, doctor=c.specialist.short_name,
                   time=c.scheduled_at.strftime('%H:%M'), ref=c.reference),
                 purpose='reminder', commit=False)
        c.notified_at = now()
    db.session.commit()
    click.echo(f'Sent {len(due)} reminder(s).')

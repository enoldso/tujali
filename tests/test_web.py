import os
import subprocess
import sys

import pytest

from conftest import ACCOUNTS, login
from models import Consultation, HealthAlert, SmsMessage, Specialist, User, db

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_pages(app):
    return [r.rule for r in app.url_map.iter_rules()
            if 'GET' in r.methods and not r.arguments and r.rule not in ('/logout',)]


def test_public_pages(client):
    for path in ('/', '/join', '/login', '/simulator', '/healthz'):
        assert client.get(path).status_code == 200, path
    assert b'*384*4040#' in client.get('/').data


@pytest.mark.parametrize('who', sorted(ACCOUNTS))
def test_no_page_errors_for_any_role(app, client, who):
    response = login(client, who)
    assert response.status_code == 302
    failures = {p: s for p in get_pages(app) if (s := client.get(p).status_code) >= 500}
    assert failures == {}


@pytest.mark.parametrize('who,home', [('admin', '/admin/'), ('health_officer', '/surveillance/'),
                                      ('specialist', '/portal/')])
def test_login_lands_on_role_home(client, who, home):
    assert login(client, who).headers['Location'].endswith(home)


def test_wrong_password(client):
    response = client.post('/login', data={'email': 'admin@tujali.example', 'password': 'nope'})
    assert b'Incorrect email or password' in response.data


def test_role_isolation(client):
    login(client, 'specialist')
    assert client.get('/surveillance/').status_code == 403
    assert client.get('/admin/').status_code == 403
    client.post('/logout')
    login(client, 'health_officer')
    assert client.get('/portal/').status_code == 403
    assert client.get('/admin/').status_code == 403
    assert client.get('/surveillance/').status_code == 200


def test_specialist_cannot_open_another_specialists_consultation(client):
    other = Consultation.query.join(Specialist).filter(Specialist.county != 'Kisumu',
                                                       Consultation.status == 'booked').first()
    login(client, 'specialist')
    assert client.get(f'/portal/consultations/{other.id}').status_code == 404


def test_specialist_application_starts_unverified(client):
    response = client.post('/join', data={
        'name': 'Dr. Kevin Odhiambo', 'email': 'kevin@example.com', 'phone': '0712 345 678',
        'specialty': 'endocrinology', 'license_number': 'KMPDC/9999', 'facility': 'Kisumu Clinic',
        'county': 'Kisumu', 'fee_kes': 400, 'offers_phone': 'y', 'password': 'a-long-password',
        'confirm': 'a-long-password', 'attest': 'y'})
    assert response.status_code == 302
    user = User.query.filter_by(email='kevin@example.com').one()
    assert user.phone == '+254712345678'
    assert user.specialist.verified is False
    assert client.get('/portal/').status_code == 200


def test_verifying_specialist_notifies_waitlist(client):
    pending = Specialist(user=User(name='Dr. New Endo', email='endo@example.com', role='specialist'),
                         specialty='endocrinology', license_number='X1', county='Kisumu')
    pending.user.set_password('whatever-123')
    db.session.add(pending)
    db.session.commit()
    waiting = Consultation.query.filter_by(status='waitlist', specialty='endocrinology').count()
    assert waiting > 0

    login(client, 'admin')
    client.post(f'/admin/specialists/{pending.id}/verify')
    db.session.expire_all()
    assert db.session.get(Specialist, pending.id).verified
    assert SmsMessage.query.filter_by(purpose='waitlist_match').count() == waiting


def test_complete_consultation_sends_advice(client):
    me = User.query.filter_by(email=ACCOUNTS['specialist']).one().specialist
    c = Consultation.query.filter_by(specialist_id=me.id, status='booked').first()
    login(client, 'specialist')
    response = client.post(f'/portal/consultations/{c.id}', data={
        'action': 'complete', 'clinical_notes': 'Tinea corporis', 'advice': 'Apply cream twice daily.',
        'payment_status': 'paid', 'payment_ref': 'SAB12CD34'})
    assert response.status_code == 302
    db.session.expire_all()
    c = db.session.get(Consultation, c.id)
    assert c.status == 'completed' and c.completed_at is not None
    sms = SmsMessage.query.filter_by(phone=c.patient.phone, purpose='advice').one()
    assert 'Apply cream twice daily.' in sms.body


def test_specialist_cancel_notifies_patient(client):
    me = User.query.filter_by(email=ACCOUNTS['specialist']).one().specialist
    c = Consultation.query.filter_by(specialist_id=me.id, status='booked').first()
    login(client, 'specialist')
    client.post(f'/portal/consultations/{c.id}', data={'action': 'cancel', 'payment_status': 'unpaid'})
    db.session.expire_all()
    assert db.session.get(Consultation, c.id).status == 'cancelled'
    assert SmsMessage.query.filter_by(phone=c.patient.phone, purpose='cancellation').count() == 1


def test_availability_add_and_overlap(client):
    login(client, 'specialist')
    ok = client.post('/portal/availability', data={'weekday': 6, 'start_time': '10:00',
                                                   'end_time': '12:00', 'slot_minutes': 30})
    assert ok.status_code == 302
    clash = client.post('/portal/availability', data={'weekday': 6, 'start_time': '11:00',
                                                      'end_time': '13:00', 'slot_minutes': 30})
    assert b'overlaps' in clash.data


def test_surveillance_flags_seeded_outbreaks(client):
    login(client, 'health_officer')
    body = client.get('/surveillance/').get_data(as_text=True)
    assert 'Diarrhoea / vomiting · Kisumu' in body
    assert 'Rash with fever · Turkana' in body
    assert 'Unusual bleeding · Mandera' in body


def test_publish_alert_with_sms(client):
    login(client, 'health_officer')
    response = client.post('/surveillance/alerts', data={
        'title': 'Cholera risk in Kisumu', 'message_en': 'Boil drinking water and wash hands.',
        'message_sw': 'Chemsha maji ya kunywa.', 'county': 'Kisumu', 'syndrome': 'diarrhoea',
        'level': 'warning', 'expires_in_days': 14, 'send_sms': 'y'})
    assert response.status_code == 302
    alert = HealthAlert.query.filter_by(title='Cholera risk in Kisumu').one()
    assert alert.sms_recipients > 0
    assert SmsMessage.query.filter_by(purpose='alert').count() == alert.sms_recipients


def test_csv_export_has_no_personal_data(client):
    login(client, 'health_officer')
    response = client.get('/surveillance/export.csv?days=30')
    text = response.get_data(as_text=True)
    assert response.mimetype == 'text/csv'
    assert text.splitlines()[0] == 'reported_at,county,syndrome,people_affected,danger_signs'
    assert '+2547' not in text


def test_admin_creates_health_officer(client):
    login(client, 'admin')
    client.post('/admin/users', data={'name': 'Musa Kip', 'email': 'musa@example.com', 'phone': '',
                                      'role': 'health_officer', 'organisation': 'Turkana DoH',
                                      'password': 'temporary-pass-1'})
    assert User.query.filter_by(email='musa@example.com', role='health_officer').count() == 1


def test_csrf_enforced(app, client):
    app.config['WTF_CSRF_ENABLED'] = True
    try:
        assert client.post('/login', data={'email': 'a@b.c', 'password': 'x'}).status_code == 400
        assert client.post('/ussd', data={'sessionId': 's', 'phoneNumber': '+254700000000',
                                          'text': ''}).status_code == 200
    finally:
        app.config['WTF_CSRF_ENABLED'] = False


def test_security_headers_and_404(client):
    response = client.get('/nope')
    assert response.status_code == 404
    assert response.headers['X-Content-Type-Options'] == 'nosniff'


def test_send_reminders_command(app):
    from datetime import timedelta
    from models import now
    c = Consultation.query.filter_by(status='booked', mode='phone').first()
    c.scheduled_at = now() + timedelta(minutes=45)
    c.notified_at = None
    db.session.commit()
    result = app.test_cli_runner().invoke(args=['send-reminders'])
    assert 'reminder' in result.output
    assert SmsMessage.query.filter_by(purpose='reminder').count() >= 1


def _import_app(env):
    full_env = {k: v for k, v in os.environ.items()
                if k not in ('SECRET_KEY', 'SESSION_SECRET', 'DATABASE_URL', 'APP_ENV', 'SMS_BACKEND')}
    full_env.update(env)
    code = f'import sys; sys.path.insert(0, {ROOT!r}); import app'
    return subprocess.run([sys.executable, '-c', code], cwd=os.path.join(ROOT, 'tests'), env=full_env,
                          capture_output=True, text=True, timeout=120)


def test_production_requires_secret_and_database():
    assert 'SECRET_KEY must be set' in _import_app(
        {'APP_ENV': 'production', 'DATABASE_URL': 'sqlite://', 'SECRET_KEY': '', 'SESSION_SECRET': ''}).stderr
    assert 'DATABASE_URL must be set' in _import_app({'APP_ENV': 'production', 'SECRET_KEY': 'x' * 32}).stderr
    assert _import_app({'APP_ENV': 'production', 'SECRET_KEY': 'x' * 32,
                        'DATABASE_URL': 'sqlite://'}).returncode == 0


def test_africastalking_needs_credentials():
    result = _import_app({'SECRET_KEY': 'x', 'DATABASE_URL': 'sqlite://', 'SMS_BACKEND': 'africastalking'})
    assert 'AT_USERNAME' in result.stderr

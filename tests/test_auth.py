from conftest import login, DEMO_PASSWORDS
from models import User


def test_passwords_are_hashed(app):
    for user in User.get_all():
        assert user.password_hash != DEMO_PASSWORDS.get(user.username)
        assert not user.password_hash.startswith('hashed_')
        assert user.password_hash.startswith(('scrypt:', 'pbkdf2:'))


def test_login_success_redirects_to_dashboard(client):
    response = login(client, 'admin')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/dashboard')


def test_login_wrong_password_rejected(client):
    response = login(client, 'admin', 'wrong-password')
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data
    assert client.get('/dashboard').status_code == 302  # still logged out


def test_unknown_user_gets_same_message(client):
    response = login(client, 'nobody', 'whatever')
    assert b'Invalid username or password' in response.data


def test_login_does_not_follow_external_next(client):
    response = client.post('/login?next=https://evil.example/', data={
        'username': 'admin', 'password': 'admin123'})
    assert response.headers['Location'].endswith('/dashboard')


def test_login_follows_local_next(client):
    response = client.post('/login?next=/patients', data={
        'username': 'admin', 'password': 'admin123'})
    assert response.headers['Location'].endswith('/patients')


def test_protected_page_requires_login(client):
    response = client.get('/patients')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_inactive_user_cannot_log_in(app, client):
    user = User.get_by_username('charge_nurse')
    user.is_active_account = False
    from models import db
    db.session.commit()
    assert login(client, 'charge_nurse').status_code == 200


def test_registration_creates_working_account(client):
    response = client.post('/register', data={
        'username': 'drnew', 'email': 'drnew@example.com', 'password': 'a-long-password',
        'confirm_password': 'a-long-password', 'full_name': 'Dr New',
        'specialization': 'general', 'license_number': 'KMPDC-1',
        'phone_number': '+254700000001', 'location': 'Nairobi', 'years_experience': 3,
    })
    assert response.status_code == 302, response.data[:500]
    assert login(client, 'drnew', 'a-long-password').status_code == 302
    assert client.get('/dashboard').status_code == 200


def test_registration_can_be_disabled(app, client):
    app.config['ALLOW_REGISTRATION'] = False
    try:
        assert client.get('/register').status_code == 404
        assert b'Register here' not in client.get('/login').data
    finally:
        app.config['ALLOW_REGISTRATION'] = True

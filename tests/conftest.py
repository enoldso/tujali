import os
import sys

# Configure before the app module is imported.
os.environ['APP_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['USE_MOCK_AI'] = 'true'
os.environ['LOG_LEVEL'] = 'WARNING'
os.environ.pop('USSD_ALLOWED_IPS', None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app import app as flask_app
from models import db
from seed import seed_demo_data

DEMO_PASSWORDS = {
    'admin': 'admin123',
    'finance_manager': 'finance123',
    'lab_supervisor': 'lab123',
    'chief_medical': 'clinical123',
    'charge_nurse': 'nurse123',
    'pharmacy_head': 'pharmacy123',
}


@pytest.fixture
def app():
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        seed_demo_data()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, password=None):
    return client.post('/login', data={'username': username,
                                       'password': password or DEMO_PASSWORDS[username]})

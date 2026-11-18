import os
import sys

os.environ['APP_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['SMS_BACKEND'] = 'console'
os.environ['LOG_LEVEL'] = 'WARNING'
os.environ.pop('USSD_ALLOWED_IPS', None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from app import app as flask_app  # noqa: E402
from models import db  # noqa: E402
from seed import DEMO_PASSWORD, seed_demo_data  # noqa: E402

DEMO_PATIENT = '+254712000001'
ACCOUNTS = {
    'admin': 'admin@tujali.example',
    'health_officer': 'health@tujali.example',
    'specialist': 'achieng@tujali.example',
    'pending_specialist': 'aisha@tujali.example',
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


def login(client, who):
    return client.post('/login', data={'email': ACCOUNTS.get(who, who), 'password': DEMO_PASSWORD})


class Phone:
    """Drives one USSD session the way Africa's Talking does (text accumulates with '*')."""

    def __init__(self, client, number=DEMO_PATIENT, session_id='sess-1'):
        self.client, self.number, self.session_id = client, number, session_id
        self.inputs = []
        self.screens = []

    def dial(self):
        self.inputs = []
        return self._send('')

    def press(self, value):
        self.inputs.append(str(value))
        return self._send('*'.join(self.inputs))

    def _send(self, text):
        response = self.client.post('/ussd', data={'sessionId': self.session_id, 'phoneNumber': self.number,
                                                   'serviceCode': '*384*4040#', 'text': text})
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert body.startswith(('CON ', 'END ')), body
        db.session.remove()  # next hop may hit another worker
        self.screens.append(body)
        return body

    def choose(self, body, words):
        """Press the option whose line contains `words`, paging with 9 if needed."""
        for _ in range(5):
            for line in body.split('\n'):
                number, _, label = line.partition('. ')
                if number.isdigit() and words.lower() in label.lower():
                    return self.press(number)
            assert '9. ' in body, f'{words!r} not found in:\n{body}'
            body = self.press('9')
        raise AssertionError(f'{words!r} not found')

import pytest

from conftest import login, DEMO_PASSWORDS

DETAIL_PAGES = ['/patients/1', '/messages/1', '/user-journey/1', '/api/user-journey/1']


def _get_pages(app):
    pages = [rule.rule for rule in app.url_map.iter_rules()
             if 'GET' in rule.methods and not rule.arguments and rule.rule != '/logout']
    return pages + DETAIL_PAGES


@pytest.mark.parametrize('username', sorted(DEMO_PASSWORDS))
def test_no_page_errors_for_any_role(app, client, username):
    assert login(client, username).status_code == 302
    failures = {}
    for path in _get_pages(app):
        status = client.get(path).status_code
        if status >= 500:
            failures[path] = status
    assert failures == {}


def test_admin_sees_all_dashboards(client):
    login(client, 'admin')
    for path in ['/admin_dashboard', '/finance_dashboard', '/lab_dashboard',
                 '/pharmacy_dashboard', '/clinical_dashboard', '/system_status',
                 '/manage_departments', '/user_profile']:
        assert client.get(path).status_code == 200, path


def test_department_isolation(client):
    login(client, 'finance_manager')
    assert client.get('/finance_dashboard').status_code == 200
    assert client.get('/lab_dashboard').status_code == 403
    assert client.get('/admin_dashboard').status_code == 403


def test_non_provider_gets_403_not_500_on_provider_pages(client):
    login(client, 'finance_manager')
    assert client.get('/appointments').status_code == 403


def test_healthz(client):
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}


def test_security_headers(client):
    response = client.get('/login')
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'


def test_unknown_page_returns_404_page(client):
    response = client.get('/no-such-page')
    assert response.status_code == 404
    assert b'Page not found' in response.data


def test_csrf_enforced_when_enabled(app, client):
    app.config['WTF_CSRF_ENABLED'] = True
    try:
        response = client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        assert response.status_code == 400
    finally:
        app.config['WTF_CSRF_ENABLED'] = False


def test_ussd_endpoint_is_csrf_exempt(app, client):
    app.config['WTF_CSRF_ENABLED'] = True
    try:
        response = client.post('/ussd', data={'sessionId': 's', 'phoneNumber': '+254700000099',
                                               'serviceCode': '*384#', 'text': ''})
        assert response.status_code == 200
    finally:
        app.config['WTF_CSRF_ENABLED'] = False

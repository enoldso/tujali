import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _import_app(env):
    full_env = {k: v for k, v in os.environ.items()
                if k not in ('SECRET_KEY', 'SESSION_SECRET', 'DATABASE_URL', 'APP_ENV')}
    full_env.update(env)
    # Run from an empty dir so a developer's .env file can't fill in the blanks.
    code = f'import sys; sys.path.insert(0, {ROOT!r}); import app'
    return subprocess.run([sys.executable, '-c', code], cwd=os.path.join(ROOT, 'tests'),
                          env=full_env, capture_output=True, text=True, timeout=120)


def test_production_requires_secret_key():
    # Empty values also stop a local .env file from supplying a key.
    result = _import_app({'APP_ENV': 'production', 'DATABASE_URL': 'sqlite://',
                          'SECRET_KEY': '', 'SESSION_SECRET': ''})
    assert result.returncode != 0
    assert 'SECRET_KEY must be set' in result.stderr


def test_production_requires_database_url():
    result = _import_app({'APP_ENV': 'production', 'SECRET_KEY': 'x' * 32})
    assert result.returncode != 0
    assert 'DATABASE_URL must be set' in result.stderr


def test_production_starts_with_required_settings():
    result = _import_app({'APP_ENV': 'production', 'SECRET_KEY': 'x' * 32,
                          'DATABASE_URL': 'sqlite://'})
    assert result.returncode == 0, result.stderr


def test_simulator_can_be_disabled(app, client):
    app.config['ENABLE_USSD_SIMULATOR'] = False
    try:
        assert client.get('/ussd_simulator.html').status_code == 404
    finally:
        app.config['ENABLE_USSD_SIMULATOR'] = True

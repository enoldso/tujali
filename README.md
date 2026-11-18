# Tujali

Tujali is a telehealth platform for rural Kenya. Patients use **USSD** (`*384*4040#`,
any phone, no internet needed) to register, report symptoms, book appointments,
message a provider and read health information in English, Swahili, French,
Oromo, Somali or Amharic. Clinic staff use a **web dashboard** with
department-specific views: clinical, finance, laboratory, pharmacy and administration.

## Stack

- Python 3.11+ and Flask, server-rendered Jinja templates with Bootstrap 5
- PostgreSQL through SQLAlchemy, with Alembic migrations (Flask-Migrate). SQLite is used for local development and tests.
- Flask-Login for sessions, Flask-WTF for forms and CSRF protection, Werkzeug (scrypt) for password hashing
- Gunicorn in production
- Africa's Talking USSD gateway, which POSTs to `/ussd`

## Quick start (local development)

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                 # defaults work for local dev (SQLite)

flask --app main db upgrade          # create the tables
flask --app main seed-demo           # optional: demo users, patients, appointments
flask --app main run --debug         # http://127.0.0.1:5000
```

`seed-demo` creates these demo logins. **Never load demo data into production.**

| Username | Password | Lands on |
|---|---|---|
| admin | admin123 | Super admin dashboard |
| finance_manager | finance123 | Finance dashboard |
| lab_supervisor | lab123 | Laboratory dashboard |
| chief_medical | clinical123 | Clinical dashboard |
| charge_nurse | nurse123 | Clinical dashboard |
| pharmacy_head | pharmacy123 | Pharmacy dashboard |

To try the USSD flow locally, open `http://127.0.0.1:5000/ussd_simulator.html`, or
POST to `/ussd` with `sessionId`, `phoneNumber`, `serviceCode` and `text`.

## Tests

```bash
pytest
```

The suite runs against an in-memory SQLite database. It covers login and password
hashing, every page for every role, CSRF, USSD registration and booking across
requests, billing and payments, and the production configuration checks.

## Configuration

All settings come from environment variables. See [.env.example](.env.example).

| Variable | Required in production | Purpose |
|---|---|---|
| `APP_ENV` | yes (`production`) | Turns on production behaviour, listed below |
| `SECRET_KEY` | **yes** | Signs sessions. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | **yes** | `postgresql://user:pass@host:5432/db?sslmode=require`. `postgres://` URLs are also accepted |
| `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` | for first setup | Used by `flask --app main create-admin` |
| `LOG_LEVEL` | no | Defaults to `INFO` in production and `DEBUG` otherwise |
| `ALLOW_REGISTRATION` | no | Public provider sign-up page. Off in production by default |
| `ENABLE_USSD_SIMULATOR` | no | `/ussd_simulator.html`. Off in production by default |
| `BEHIND_PROXY` | no | Trust `X-Forwarded-*` headers from one proxy. On in production by default |
| `SESSION_COOKIE_SECURE` | no | HTTPS-only cookies. On in production by default |
| `USSD_ALLOWED_IPS` | recommended | Comma-separated gateway IPs allowed to call `/ussd` |
| `USE_MOCK_AI` | no | `true` (default) uses the offline health-content generator. `false` uses OpenAI or Anthropic and needs `pip install -r requirements-ai.txt` plus API keys |
| `WEB_CONCURRENCY`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT`, `PORT` | no | Gunicorn tuning |

With `APP_ENV=production` the app refuses to start without `SECRET_KEY` and
`DATABASE_URL`. It also sends HSTS and secure cookies, and disables self-registration,
the USSD simulator and demo seeding.

## Deploying

Every target follows the same three steps:

1. Provision PostgreSQL (Neon, Render, Railway, RDS, or self-hosted) and set the environment variables above.
2. Run the migrations: `flask --app main db upgrade`. Run this on every deploy.
3. Create the first admin, once: `ADMIN_PASSWORD=... flask --app main create-admin`. After that, add staff from **Admin → Manage Users**.

Then serve the app with one of these options:

- **Docker:** `docker build -t tujali . && docker run -p 8000:8000 --env-file prod.env tujali`. The container runs migrations on start and has a `/healthz` health check.
- **Heroku-style platforms** (Render, Railway, Heroku, Dokku): the [Procfile](Procfile) runs migrations in the release phase and starts Gunicorn.
- **VPS:** run `gunicorn -c gunicorn.conf.py main:app` behind nginx with TLS, managed by systemd.
- **cPanel or DirectAdmin Python app (Passenger):** set the startup file to `passenger_wsgi.py` and the entry point to `application`.

Point the Africa's Talking USSD callback at `https://<your-domain>/ussd`.

Use `GET /healthz` for uptime checks. It returns `{"status": "ok"}` when the database is reachable.

### Database changes

After you change `models.py`:

```bash
flask --app main db migrate -m "describe the change"
flask --app main db upgrade
```

Review the generated file in `migrations/versions/` and commit it with the code.

## Project layout

```
app.py            Flask app, configuration, routes, CLI commands
models.py         SQLAlchemy models
ussd_handler.py   USSD menu state machine (state stored in the ussd_sessions table)
forms.py          WTForms
utils.py          Role and department access control, helpers
seed.py           create_admin() and demo data
templates/        Jinja templates
static/           CSS and JS
migrations/       Alembic migrations
tests/            pytest suite
ussd-geo/         Separate Node.js geo-location USSD prototype, not used by the Flask app
```

## Notes and limits

- The pharmacy inventory and drug-interaction panels show placeholder data until an inventory system is connected.
- SMS delivery and M-Pesa payment collection are not integrated yet. Payments are recorded manually.
- `ussd-geo/` is an earlier Node.js experiment with its own `package.json`. It isn't deployed by anything in this repository.

# Tujali

**Specialist care on any phone, and early warning for outbreaks.**

Most specialists in Kenya work in a few big towns. Tujali lets people in rural and low-income
communities reach dermatologists, gynaecologists, neurologists, paediatricians and other specialists
using **USSD** (`*384*4040#`), which works on every mobile phone without internet or data. The same
menu lets anyone report illness at home, so county health teams can spot outbreaks early.

## Who uses what

| Who | Where | What they do |
|---|---|---|
| **Patients** | USSD menu, in English or Kiswahili | Register once. Book a specialist by need ("Skin", "Women's health"...) for a phone call-back or an in-person visit. View or cancel appointments, read the doctor's advice and book follow-ups. Report illness at home, read health alerts for their county, get emergency numbers, and change language, county or delete their data. |
| **Specialists** | Web portal (`/portal`) | Apply at `/join` and get verified. See today's call queue (tap to call), write private notes and advice (sent to the patient by SMS), track payments, set weekly hours and fee, and pause bookings. |
| **Health officers** | Surveillance dashboard (`/surveillance`) | See automatic outbreak signals by county and illness type, trend charts and a county heat table. Publish alerts that show on USSD and can be sent by SMS. Export reports as CSV. |
| **Administrators** | Admin (`/admin`) | Verify specialist licences, manage staff accounts and read the SMS log. See **unmet demand**: requests where no specialist was available, by specialty and county. |

### What happens automatically

- **SMS:** booking confirmations go to the patient and the specialist, cancellations to the other side, advice to the patient when a consultation is completed, and a call reminder before each phone consultation (run `flask send-reminders` from cron).
- **Waiting list:** when nobody offers a specialty, the request goes on a waiting list. When a matching specialist is verified, waiting patients get an SMS.
- **Outbreak signals:** each county and illness type is compared with that county's own previous 3 weeks. Red-flag signs (unusual bleeding, stiff neck or confusion) are flagged on their first report. The rules are in [surveillance.py](surveillance.py) and are deliberately simple enough to check by hand.
- **Privacy:** illness reports don't store a phone number. A salted hash only limits repeat reports (3 per person per illness per day). Patients can delete their own data from the USSD menu.

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env

flask --app main db upgrade
flask --app main seed-demo           # demo data, including two simulated outbreaks
flask --app main run --debug         # http://127.0.0.1:5000
```

Open **http://127.0.0.1:5000/simulator** to use Tujali as a patient on a simulated phone. The number
`+254712000001` is a registered demo patient; any other number walks you through registration.

Demo staff logins (password `tujali-demo-2026`; **never load demo data in production**):

| Email | Role |
|---|---|
| admin@tujali.example | Administrator |
| health@tujali.example | Health officer (Kisumu) |
| achieng@tujali.example | Dermatologist, Kisumu |
| aisha@tujali.example | Psychiatrist awaiting verification |

## Tests

```bash
pytest
```

The tests drive the full USSD journeys hop by hop, exactly as Africa's Talking sends them: registration,
booking, double-booking protection, the waiting list, cancelling, advice and follow-ups, illness reporting
and its rate limit, alerts, Kiswahili, account deletion, and a check that every screen fits in 182
characters. They also cover each web role, access control, verification, SMS side effects, CSV export,
CSRF and the production configuration checks.

## Configuration

Everything comes from environment variables. See [.env.example](.env.example).

| Variable | Notes |
|---|---|
| `APP_ENV` | Set to `production` in production. The app then refuses to start without `SECRET_KEY` and `DATABASE_URL`, and it sends HSTS headers, uses secure cookies and hides the simulator. |
| `SECRET_KEY` | Long random string. |
| `DATABASE_URL` | PostgreSQL, e.g. `postgresql://user:pass@host/db?sslmode=require`. |
| `USSD_CODE` | The code shown to patients, `*384*4040#` by default. |
| `SMS_BACKEND` | `console` (default) only records messages in the SMS log. `africastalking` sends them and needs `AT_USERNAME` and `AT_API_KEY` (optionally `AT_SENDER_ID`; use `AT_USERNAME=sandbox` to test). |
| `USSD_ALLOWED_IPS` | Recommended: comma-separated gateway IPs allowed to call `/ussd`. |
| `ALERT_SMS_LIMIT` | Maximum SMS per alert broadcast (default 5000). |
| `BEHIND_PROXY`, `SESSION_COOKIE_SECURE`, `ENABLE_USSD_SIMULATOR`, `LOG_LEVEL` | Defaults depend on `APP_ENV`. |

## Deploying

1. Provision PostgreSQL and set the variables above.
2. Run `flask --app main db upgrade` on every deploy.
3. Create the first administrator once: `ADMIN_EMAIL=... ADMIN_PASSWORD=... flask --app main create-admin`.
4. Serve with `gunicorn -c gunicorn.conf.py main:app`. The [Procfile](Procfile), [Dockerfile](Dockerfile) and [passenger_wsgi.py](passenger_wsgi.py) (cPanel or DirectAdmin) are all ready to use.
5. In Africa's Talking, point the USSD callback to `https://<your-domain>/ussd`.
6. Schedule `flask --app main send-reminders` every 15 minutes for call reminders.

`GET /healthz` returns `{"status": "ok"}` when the database is reachable.

After you change [models.py](models.py), run `flask --app main db migrate -m "..."`, review the new
file in `migrations/versions/`, and commit it.

## Code map

```
app.py            configuration, /ussd, /healthz, error pages, CLI commands
ussd.py           USSD screens (render + handle per screen, paging, session state in the DB)
i18n.py           all USSD and SMS text in English and Kiswahili
reference.py      counties by region, specialties, illness groups, emergency numbers
scheduling.py     matching specialists and generating free slots from weekly hours
surveillance.py   outbreak signal rules and dashboard aggregates
sms.py            SMS sending (Africa's Talking or console) with a log
public.py         landing page, specialist sign-up, simulator
auth.py           sign in and out, role checks
portal.py         specialist portal
health.py         surveillance dashboard, alerts, CSV export
admin.py          overview, verification, staff, SMS log
models.py         database models
seed.py           create_admin() and demo data
templates/        Jinja templates (Bootstrap 5 and a custom design system in static/css/app.css)
```

## Ideas for next steps

- **M-Pesa STK push:** charge the consultation fee when booking, so specialists don't have to chase payment.
- **Sponsored consultations:** NGO or county voucher codes entered on USSD to waive the fee.
- **Community health promoters (CHPs):** let a CHP report and book on behalf of households, with their own login and metrics.
- **Specialist referrals:** let a specialist refer a patient to another specialty with one tap.
- **Voice callbacks:** use Africa's Talking Voice to connect patient and specialist through a masked number.
- **Map view:** a county choropleth for the surveillance dashboard.

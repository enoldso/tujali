"""
Database bootstrap helpers.

- create_admin(): create (or reset) the super-admin account. Used by
  `flask create-admin` and, on startup, by ADMIN_USERNAME/ADMIN_PASSWORD.
- seed_demo_data(): load the demo dataset (department users, providers,
  patients, appointments, ...). Only for development/staging; never run it
  against a production database. Used by `flask seed-demo`.
"""
from datetime import datetime, timedelta

from models import (db, User, Provider, Patient, Appointment, Message, HealthInfo,
                    UserInteraction, Payment)

ALL_DEPARTMENTS = ['clinical', 'finance', 'laboratory', 'pharmacy', 'administration']

# (username, email, password, role, department, permissions)
DEMO_USERS = [
    ('finance_manager', 'finance@tujali.example', 'finance123', 'finance_manager', 'finance',
     ['billing', 'payments', 'revenue_analytics', 'insurance_claims', 'cost_analysis']),
    ('lab_supervisor', 'lab@tujali.example', 'lab123', 'lab_supervisor', 'laboratory',
     ['lab_tests', 'results', 'quality_control', 'equipment_management', 'test_scheduling']),
    ('chief_medical', 'clinical@tujali.example', 'clinical123', 'chief_medical_officer', 'clinical',
     ['patient_care', 'appointments', 'medical_records', 'treatment_protocols', 'emergency_response']),
    ('charge_nurse', 'nurse@tujali.example', 'nurse123', 'charge_nurse', 'clinical',
     ['patient_monitoring', 'medication_admin', 'vital_signs', 'care_coordination']),
    ('pharmacy_head', 'pharmacy@tujali.example', 'pharmacy123', 'pharmacy_manager', 'pharmacy',
     ['prescription_management', 'drug_inventory', 'dispensing', 'drug_interactions']),
]


def create_admin(username, password, email):
    """Create the super admin, or reset its password if it already exists."""
    user = User.get_by_username(username)
    if user:
        user.set_password(password)
        user.role = 'super_admin'
        user.department = 'administration'
        user.permissions = list(ALL_DEPARTMENTS)
        db.session.commit()
        return user, False
    user = User.create(username, email, password, 'super_admin', 'administration', ALL_DEPARTMENTS)
    return user, True


def seed_demo_data(admin_password='admin123'):
    """Populate an empty database with demo data. Returns False if data already exists."""
    if Patient.query.first() is not None:
        return False

    admin, _ = create_admin('admin', admin_password, 'admin@tujali.example')
    for username, email, password, role, department, permissions in DEMO_USERS:
        if not User.username_exists(username):
            User.create(username, email, password, role, department, permissions)

    providers = [
        ('Dr. John Doe', 'General Medicine', 'English, Swahili', 'Nairobi, Kenya', (-1.2921, 36.8219)),
        ('Dr. Sarah Kimani', 'Pediatrics', 'English, Swahili', 'Mombasa, Kenya', (-4.0435, 39.6682)),
        ('Dr. Mohammed Ali', 'Cardiology', 'English, Swahili, Arabic', 'Kisumu, Kenya', (-0.1022, 34.7617)),
        ('Dr. Elizabeth Ochieng', 'Obstetrics & Gynecology', 'English, Swahili, Luo', 'Nakuru, Kenya', (-0.3031, 36.0800)),
        ('Dr. Thomas Mutua', 'General Medicine', 'English, Swahili, Kamba', 'Eldoret, Kenya', (0.5143, 35.2698)),
    ]
    provider_objs = [
        Provider.create(admin.id, name, spec, None, None, loc, None, languages=langs, coordinates=coords)
        for name, spec, langs, loc, coords in providers
    ]
    p1 = provider_objs[0]

    HealthInfo.create('COVID-19 Prevention',
                      'Wash hands regularly, wear masks in public, maintain social distance.', 'en')
    HealthInfo.create('Kuzuia COVID-19',
                      'Osha mikono mara kwa mara, vaa mask kwa umma, dumisha umbali wa kijamii.', 'sw')
    HealthInfo.create('Maternal Health Tips',
                      'Regular check-ups, balanced diet, and adequate rest are essential during pregnancy.', 'en')
    HealthInfo.create('Ushauri wa Afya ya Uzazi',
                      'Uchunguzi wa mara kwa mara, lishe bora, na kupumzika kwa kutosha ni muhimu wakati wa ujauzito.', 'sw')

    patients = [
        ('+254711001122', 'Jane Wanjiku', 32, 'Female', 'Nairobi', 'en', (-1.2864, 36.8172)),
        ('+254722334455', 'John Otieno', 45, 'Male', 'Kisumu', 'sw', (-0.1050, 34.7550)),
        ('+254733667788', 'Mary Akinyi', 28, 'Female', 'Mombasa', 'en', (-4.0500, 39.6700)),
        ('+254744990011', 'James Maina', 52, 'Male', 'Nakuru', 'sw', (-0.3100, 36.0750)),
        ('+254755223344', 'Grace Njeri', 19, 'Female', 'Eldoret', 'en', (0.5200, 35.2650)),
    ]
    pts = [Patient.create(*p) for p in patients]

    symptoms = {
        0: ['Persistent headache and fever for 3 days', 'Severe cough and difficulty breathing',
            'Pain in joints and muscles, mild fever'],
        1: ['Kikohozi na maumivu ya kifua kwa wiki moja', 'Stomach pain and vomiting, moderate severity',
            'High fever with chills and sweating'],
        2: ['Skin rash and itching on arms', 'Mild digestive issues with nausea',
            'Persistent headache, unbearable at times'],
        3: ['Chronic cough with chest pain, moderate severity', 'Skin lesions with slight itching on legs'],
        4: ['Severe abdominal pain with vomiting', 'Mild fever and body aches',
            'Respiratory difficulty when exercising'],
    }
    for idx, texts in symptoms.items():
        for text in texts:
            pts[idx].add_symptom(text)

    appts = [
        Appointment.create(pts[0].id, p1.id, '25-03-2025', '10:00 AM', 500.00),
        Appointment.create(pts[1].id, p1.id, '26-03-2025', '2:30 PM', 500.00),
        Appointment.create(pts[2].id, p1.id, '24-03-2025', '11:15 AM', 750.00),
        Appointment.create(pts[3].id, p1.id, '27-03-2025', '9:00 AM', 350.00),
        Appointment.create(pts[4].id, p1.id, '23-03-2025', '3:45 PM', 400.00),
    ]
    for appt, (status, pay) in zip(appts, [('confirmed', 'completed'), ('pending', 'pending'),
                                           ('completed', 'pending'), ('pending', 'completed'),
                                           ('cancelled', 'pending')]):
        Appointment.update_status(appt.id, status, pay)

    Message.create(p1.id, pts[0].id, 'Hello Dr. Doe, I have been experiencing severe headaches.', 'patient')
    Message.create(p1.id, pts[0].id, 'Hi Jane, I recommend you come in for a check-up. When are you available?', 'provider')
    Message.create(p1.id, pts[0].id, 'I can come tomorrow morning if that works.', 'patient')
    Message.create(p1.id, pts[0].id, 'Perfect. I have scheduled you for 10 AM tomorrow.', 'provider')
    Message.mark_as_read(pts[0].id, p1.id)
    Message.create(p1.id, pts[1].id, 'Habari daktari, nina maumivu ya kifua.', 'patient')
    Message.create(p1.id, pts[2].id, 'Doctor, the rash on my arms is getting worse.', 'patient')

    interactions = [
        (0, 'ussd', 'Started USSD session', {'session_id': 'ATI123456789'}, datetime(2025, 2, 1, 9, 30)),
        (0, 'ussd', 'Checked available appointments', {'session_id': 'ATI123456789'}, datetime(2025, 2, 1, 9, 33)),
        (0, 'ussd', 'Requested health information', {'session_id': 'ATI123456790'}, datetime(2025, 2, 5, 14, 15)),
        (0, 'symptom', 'Reported persistent headache', {'severity': 'Moderate'}, datetime(2025, 2, 10, 8, 45)),
        (0, 'symptom', 'Reported fever', {'severity': 'Mild'}, datetime(2025, 2, 10, 8, 47)),
        (0, 'appointment', 'Scheduled appointment with Dr. John Doe', {'date': '25-03-2025', 'time': '10:00 AM'}, datetime(2025, 2, 12, 11, 20)),
        (0, 'message', 'Sent message about headaches', {'message_id': 1}, datetime(2025, 3, 1, 10, 5)),
        (0, 'message', 'Received response from Dr. Doe', {'message_id': 2}, datetime(2025, 3, 1, 10, 30)),
        (0, 'message', 'Confirmed appointment availability', {'message_id': 3}, datetime(2025, 3, 1, 10, 35)),
        (0, 'health_tip', 'Received tips for headache management', {'tip_type': 'symptom_specific'}, datetime(2025, 3, 5, 9, 0)),
        (1, 'ussd', 'Started USSD session in Swahili', {'session_id': 'ATI987654321', 'language': 'sw'}, datetime(2025, 2, 3, 12, 15)),
        (1, 'symptom', 'Reported chest pain and cough', {'severity': 'Severe'}, datetime(2025, 2, 3, 12, 20)),
        (1, 'appointment', 'Requested urgent consultation', {'provider': 'Any available'}, datetime(2025, 2, 3, 12, 25)),
        (1, 'message', 'Sent message about chest pain', {'message_id': 5}, datetime(2025, 2, 4, 9, 10)),
        (2, 'ussd', 'Accessed health information', {'topic': 'skin care'}, datetime(2025, 2, 8, 16, 30)),
        (2, 'symptom', 'Reported skin rash', {'severity': 'Moderate', 'location': 'arms'}, datetime(2025, 2, 8, 16, 35)),
        (2, 'message', 'Sent message about worsening rash', {'message_id': 6}, datetime(2025, 3, 2, 15, 40)),
        (2, 'health_tip', 'Received skin care recommendations', {'tip_type': 'condition_specific'}, datetime(2025, 3, 3, 10, 0)),
    ]
    for idx, kind, desc, meta, when in interactions:
        UserInteraction.create(pts[idx].id, kind, desc, meta, created_at=when)

    now = datetime.now()
    pay1 = Payment.create(appts[0].id, 500.00, pts[0].phone_number)
    Payment.update_status(pay1.id, 'completed', 'MPESA123456')
    pay1.created_at = pay1.paid_at = now - timedelta(days=3)
    pay2 = Payment.create(appts[2].id, 750.00, pts[2].phone_number)
    pay2.created_at = now - timedelta(days=1)
    pay3 = Payment.create(appts[3].id, 350.00, pts[1].phone_number)
    Payment.update_status(pay3.id, 'completed', 'MPESA789012')
    pay3.created_at = pay3.paid_at = now - timedelta(days=7)
    db.session.commit()
    return True

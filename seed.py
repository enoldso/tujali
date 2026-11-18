"""Bootstrap helpers: create_admin() and a realistic demo dataset.

The demo data includes two simulated outbreaks so the surveillance dashboard
has something to show: diarrhoea rising in Kisumu and rash-with-fever in
Turkana over the last week.
"""
import random
from datetime import time, timedelta

from models import (db, now, Availability, Consultation, HealthAlert, Patient, SmsMessage,
                    Specialist, SymptomReport, User)

DEMO_PASSWORD = 'tujali-demo-2026'


def create_admin(name, email, password):
    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()
    created = user is None
    if created:
        user = User(name=name, email=email, role='admin')
        db.session.add(user)
    user.role = 'admin'
    user.is_active_account = True
    user.set_password(password)
    db.session.commit()
    return user, created


SPECIALISTS = [
    # name, specialty, county, facility, fee, phone, in_person, verified
    ('Achieng Otieno', 'dermatology', 'Kisumu', 'Jaramogi Oginga Odinga TRH', 600, True, True, True),
    ('Wanjiru Kamau', 'dermatology', 'Nairobi', 'Kenyatta National Hospital', 1000, True, False, True),
    ('Halima Abdi', 'gynaecology', 'Garissa', 'Garissa County Referral Hospital', 500, True, True, True),
    ('Grace Mwende', 'gynaecology', 'Machakos', 'Machakos Level 5 Hospital', 700, True, True, True),
    ('Peter Kiprono', 'neurology', 'Uasin Gishu', 'Moi Teaching & Referral Hospital', 1200, True, False, True),
    ('Faith Njeri', 'paediatrics', 'Nakuru', 'Nakuru Level 5 Hospital', 400, True, True, True),
    ('Omar Said', 'paediatrics', 'Mombasa', 'Coast General Hospital', 500, True, True, True),
    ('Daniel Mutua', 'cardiology', 'Nairobi', 'Aga Khan University Hospital', 1500, True, False, True),
    ('Esther Chebet', 'psychiatry', 'Nairobi', 'Mathari National Teaching & Referral', 800, True, False, True),
    ('Samuel Ekal', 'ophthalmology', 'Turkana', 'Lodwar County Referral Hospital', 300, False, True, True),
    ('Mary Wafula', 'ent', 'Bungoma', 'Bungoma County Referral Hospital', 500, True, True, True),
    ('John Kariuki', 'orthopaedics', 'Nyeri', 'Nyeri County Referral Hospital', 900, True, True, True),
    ('Aisha Hassan', 'psychiatry', 'Mombasa', None, 600, True, False, False),  # pending verification
]

FIRST_NAMES = ['Akinyi', 'Wanjiku', 'Chebet', 'Nasimiyu', 'Atieno', 'Mumbua', 'Fatuma', 'Nekesa',
               'Kendi', 'Lokwang', 'Otieno', 'Kiprop', 'Mwangi', 'Barasa', 'Ekiru', 'Hassan',
               'Kamau', 'Onyango', 'Mutiso', 'Wekesa', 'Amina', 'Naliaka', 'Jepkemboi', 'Adhiambo']
LAST_NAMES = ['Ouma', 'Njoroge', 'Kirui', 'Wanyama', 'Ochieng', 'Mutua', 'Ali', 'Simiyu', 'Gitonga',
              'Lokol', 'Odhiambo', 'Kiptoo', 'Maina', 'Juma', 'Ekai', 'Omar', 'Kariuki', 'Owino']
PATIENT_COUNTIES = ['Kisumu', 'Turkana', 'Garissa', 'Kakamega', 'Kilifi', 'Nairobi', 'Machakos',
                    'Bungoma', 'Homa Bay', 'Marsabit', 'Kitui', 'Nakuru', 'Mandera', 'Siaya']

COMPLAINTS = {
    'dermatology': ['Itchy rash on arms for 3 weeks', 'Dark patches on face', 'Wound not healing'],
    'gynaecology': ['Pregnant 6 months, swollen feet', 'Painful periods', 'Bleeding after delivery'],
    'neurology': ['Headaches every day for a month', 'Fits since childhood', 'Numb hands and feet'],
    'paediatrics': ['Child 2 yrs not gaining weight', 'Baby coughing at night', 'Child has fits with fever'],
    'cardiology': ['High blood pressure, dizziness', 'Chest pain when walking', 'Swollen legs'],
    'psychiatry': ['Cannot sleep, always worried', 'Feeling hopeless since job loss', 'Hearing voices'],
    'ophthalmology': ['Cannot see clearly far away', 'Red painful eye', 'White spot on child eye'],
    'ent': ['Ear discharge for 2 weeks', 'Hearing loss left ear', 'Sore throat keeps returning'],
    'orthopaedics': ['Knee pain when walking', 'Back pain after fall', 'Child legs bending'],
    'endocrinology': ['Sugar is high, need diabetes advice', 'Swelling in neck'],
}
ADVICE = {
    'dermatology': 'Likely fungal infection. Use clotrimazole cream twice daily for 4 weeks, keep skin dry. '
                   'Return if not better in 2 weeks.',
    'gynaecology': 'Rest with legs raised and reduce salt. Go to the clinic this week to check blood pressure '
                   'and urine. Go immediately if you get headache or blurred vision.',
    'neurology': 'Keep a headache diary, drink water and limit painkillers to 3 days a week. '
                 'Get blood pressure checked at your nearest dispensary.',
    'paediatrics': 'Continue breastfeeding and add eggs, beans and green vegetables. '
                   'Weigh the child monthly at the clinic.',
    'cardiology': 'Take your BP medicine every morning, reduce salt and walk 30 minutes daily. '
                  'Check BP every 2 weeks.',
    'psychiatry': 'We agreed on a sleep routine and breathing exercises. Talk to someone you trust daily. '
                  'Call 1199 if you feel unsafe.',
    'ent': 'Keep the ear dry and do not insert objects. Ciprofloxacin ear drops 3 times daily for 7 days.',
    'orthopaedics': 'Rest the knee, use a cold compress and do the leg exercises daily. '
                    'Paracetamol for pain. Review in 2 weeks.',
}

# Weekly report rates per county (rough: bigger / more remote counties report more).
BASE_RATES = {'Kisumu': 6, 'Nairobi': 7, 'Turkana': 4, 'Garissa': 4, 'Kakamega': 5, 'Kilifi': 5,
              'Machakos': 3, 'Bungoma': 4, 'Homa Bay': 4, 'Marsabit': 2, 'Kitui': 3, 'Nakuru': 4,
              'Mandera': 2, 'Siaya': 3, 'Mombasa': 4, 'Kiambu': 3}
SYNDROME_MIX = [('fever', 40), ('respiratory', 30), ('diarrhoea', 15), ('other', 10), ('rash', 3),
                ('jaundice', 2)]


def _phone(rng):
    return '+2547' + ''.join(rng.choice('0123456789') for _ in range(8))


def seed_demo_data():
    if User.query.first() is not None or Patient.query.first() is not None:
        return False
    rng = random.Random(2026)
    today = now().replace(minute=0, second=0, microsecond=0)

    create_admin('Tujali Admin', 'admin@tujali.example', DEMO_PASSWORD)
    officer = User(name='Rose Akoth', email='health@tujali.example', role='health_officer',
                   organisation='Kisumu County Department of Health', phone='+254700000101')
    officer.set_password(DEMO_PASSWORD)
    db.session.add(officer)

    specialists = []
    for i, (name, specialty, county, facility, fee, phone_ok, visit_ok, verified) in enumerate(SPECIALISTS):
        email = name.split()[0].lower() + '@tujali.example'
        user = User(name=f'Dr. {name}', email=email, role='specialist', phone=f'+25471100{i:04d}')
        user.set_password(DEMO_PASSWORD)
        sp = Specialist(user=user, specialty=specialty, license_number=f'KMPDC/{1000 + i * 37}',
                        facility=facility, county=county, fee_kes=fee, offers_phone=phone_ok,
                        offers_in_person=visit_ok, verified=verified,
                        verified_at=today - timedelta(days=90) if verified else None,
                        created_at=today - timedelta(days=100 if verified else 2),
                        bio=f'{specialty.title()} specialist based in {county}.')
        for weekday in range(5):
            if (i + weekday) % 3 != 2:  # each specialist works most weekdays
                start = time(9, 0) if i % 2 else time(14, 0)
                end = time(12, 0) if i % 2 else time(17, 0)
                sp.availability.append(Availability(weekday=weekday, start_time=start,
                                                    end_time=end, slot_minutes=20))
        if i % 4 == 0:
            sp.availability.append(Availability(weekday=5, start_time=time(9, 0),
                                                end_time=time(11, 0), slot_minutes=30))
        db.session.add(sp)
        specialists.append(sp)
    db.session.commit()
    verified_specialists = [s for s in specialists if s.verified]

    patients = []
    used_phones = set()
    for i in range(48):
        phone = _phone(rng)
        while phone in used_phones:
            phone = _phone(rng)
        used_phones.add(phone)
        patients.append(Patient(
            phone=phone, name=f'{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}',
            age=rng.randint(4, 78), gender=rng.choice(['female', 'female', 'male', 'other']),
            county=rng.choice(PATIENT_COUNTIES), language=rng.choice(['sw', 'sw', 'en']),
            created_at=today - timedelta(days=rng.randint(1, 80))))
    # A stable demo patient for the simulator.
    patients.append(Patient(phone='+254712000001', name='Akinyi Ouma', age=31, gender='female',
                            county='Kisumu', language='en', created_at=today - timedelta(days=40)))
    db.session.add_all(patients)
    db.session.commit()

    def add_consultation(patient, sp, when, status, **extra):
        c = Consultation(patient=patient, specialist=sp, specialty=sp.specialty,
                         mode='phone' if sp.offers_phone else 'in_person', scheduled_at=when,
                         status=status, county=patient.county, fee_kes=sp.fee_kes,
                         complaint=rng.choice(COMPLAINTS[sp.specialty]),
                         created_at=when - timedelta(days=rng.randint(1, 4)), **extra)
        db.session.add(c)
        return c

    # Past consultations (last 30 days)
    for _ in range(70):
        sp = rng.choice(verified_specialists)
        when = (today - timedelta(days=rng.randint(1, 30))).replace(hour=rng.choice([9, 10, 11, 14, 15, 16]))
        status = rng.choices(['completed', 'no_show', 'cancelled'], [80, 12, 8])[0]
        extra = {}
        if status == 'completed':
            extra = {'advice': ADVICE.get(sp.specialty), 'completed_at': when + timedelta(minutes=20),
                     'payment_status': rng.choice(['paid', 'paid', 'paid', 'waived']),
                     'clinical_notes': 'Assessed by phone. Plan discussed with patient.'}
            if extra['payment_status'] == 'paid':
                extra['payment_ref'] = 'S' + ''.join(rng.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(9))
        elif status == 'cancelled':
            extra = {'cancelled_by': 'patient'}
        add_consultation(rng.choice(patients), sp, when, status, **extra)

    # Upcoming bookings, including today for the specialist queue
    for day_offset in range(0, 7):
        for _ in range(3 if day_offset else 4):
            sp = rng.choice(verified_specialists)
            hour = rng.choice([9, 10, 11, 14, 15, 16])
            when = (today + timedelta(days=day_offset)).replace(hour=hour, minute=rng.choice([0, 20, 40]))
            if day_offset == 0 and when < today:
                when = today + timedelta(hours=rng.randint(1, 4))
            add_consultation(rng.choice(patients), sp, when, 'booked')
    # Make sure Dr. Achieng Otieno (the demo specialist login) has patients today.
    for hour in (2, 3, 5):
        add_consultation(rng.choice(patients), specialists[0], today + timedelta(hours=hour), 'booked')

    # Unmet demand: nobody offers endocrinology yet; few in-person eye doctors in the north.
    for county, count in (('Kisumu', 5), ('Kakamega', 3), ('Turkana', 2), ('Nairobi', 2)):
        for _ in range(count):
            patient = rng.choice(patients)
            db.session.add(Consultation(patient=patient, specialty='endocrinology', mode='phone',
                                        status='waitlist', county=county,
                                        complaint=rng.choice(COMPLAINTS['endocrinology']),
                                        created_at=today - timedelta(days=rng.randint(1, 40))))
    for _ in range(4):
        db.session.add(Consultation(patient=rng.choice(patients), specialty='ophthalmology',
                                    mode='in_person', status='waitlist', county='Marsabit',
                                    complaint=rng.choice(COMPLAINTS['ophthalmology']),
                                    created_at=today - timedelta(days=rng.randint(1, 30))))
    db.session.commit()

    # Community illness reports: 60 days of background...
    syndromes, weights = zip(*SYNDROME_MIX)
    for day in range(60, 0, -1):
        for county, weekly_rate in BASE_RATES.items():
            for _ in range(rng.choices([0, 1, 2], [1 - weekly_rate / 10, weekly_rate / 14, weekly_rate / 35])[0]):
                db.session.add(SymptomReport(
                    county=county, syndrome=rng.choices(syndromes, weights)[0],
                    people_affected=rng.choices([1, 2, 4], [70, 22, 8])[0],
                    danger_signs=rng.random() < 0.06,
                    created_at=today - timedelta(days=day, hours=rng.randint(0, 12))))
    # ...plus two outbreaks in the last week.
    for _ in range(26):
        db.session.add(SymptomReport(county='Kisumu', syndrome='diarrhoea',
                                     people_affected=rng.choices([1, 2, 4], [40, 40, 20])[0],
                                     danger_signs=rng.random() < 0.25,
                                     created_at=today - timedelta(days=rng.randint(0, 5), hours=rng.randint(0, 10))))
    for _ in range(9):
        db.session.add(SymptomReport(county='Turkana', syndrome='rash',
                                     people_affected=rng.choice([1, 2, 4]), danger_signs=False,
                                     created_at=today - timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 10))))
    db.session.add(SymptomReport(county='Mandera', syndrome='bleeding', people_affected=1,
                                 danger_signs=True, created_at=today - timedelta(days=1)))

    db.session.add_all([
        HealthAlert(title='Malaria season: sleep under a net', level='advisory', created_by=officer,
                    message_en='Rains increase malaria. Sleep under a treated net every night and get '
                               'tested within 24 hours of any fever. Testing is free at public facilities.',
                    message_sw='Mvua huongeza malaria. Lala kwenye chandarua kilichotibiwa kila usiku na '
                               'upime ndani ya saa 24 ukipata homa. Kipimo ni bure vituo vya umma.',
                    created_at=today - timedelta(days=10), expires_at=today + timedelta(days=20)),
        HealthAlert(title='Measles vaccination drive', county='Turkana', syndrome='rash', level='warning',
                    created_by=officer,
                    message_en='Free measles vaccination for children 9 months to 5 years at all '
                               'Turkana health facilities this month. Keep children with rash and fever at home.',
                    message_sw='Chanjo ya surua bure kwa watoto miezi 9 hadi miaka 5 vituo vyote vya afya '
                               'Turkana mwezi huu. Watoto wenye upele na homa wakae nyumbani.',
                    created_at=today - timedelta(days=2), expires_at=today + timedelta(days=28)),
    ])
    db.session.add_all([
        SmsMessage(phone=patients[i].phone, purpose='booking', status='logged',
                   body='Tujali: Booked TJ-DEMO. Your specialist will call you at the booked time.',
                   created_at=today - timedelta(hours=i)) for i in range(5)
    ])
    db.session.commit()
    return True

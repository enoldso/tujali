from conftest import DEMO_PATIENT, Phone
from models import Consultation, HealthAlert, Patient, SmsMessage, Specialist, SymptomReport, db
from ussd import MAX_SCREEN


def assert_screens_fit(phone):
    for screen in phone.screens:
        if screen.startswith('CON '):
            assert len(screen) - 4 <= MAX_SCREEN, f'{len(screen)} chars:\n{screen}'


def test_new_user_sees_language_menu(client):
    body = Phone(client, '+254799000001').dial()
    assert body.startswith('CON ')
    assert '1. English' in body and '2. Kiswahili' in body


def test_registered_user_goes_straight_to_main_menu(client):
    body = Phone(client).dial()
    assert 'Akinyi' in body and '1. See a specialist' in body


def test_registration_then_booking_flow(client):
    phone = Phone(client, '+254799000002')
    phone.dial()
    phone.press('1')                        # English
    body = phone.press('1')                 # See a specialist -> must register
    assert 'register' in body.lower()
    phone.press('Wanjiru Kamau')
    phone.press('34')
    body = phone.press('1')                 # Female
    assert 'region' in body.lower()
    body = phone.choose(body, 'Nyanza')
    body = phone.choose(body, 'Kisumu')
    assert 'What do you need help with?' in body

    patient = Patient.query.filter_by(phone='+254799000002').one()
    assert (patient.name, patient.age, patient.gender, patient.county) == ('Wanjiru Kamau', 34, 'female', 'Kisumu')
    patient_id = patient.id

    body = phone.choose(body, 'Skin')
    body = phone.press('Itchy rash on arms for 2 weeks')
    body = phone.press('1')                 # phone consultation
    assert 'Choose a specialist' in body
    body = phone.press('1')                 # first specialist
    assert 'Choose a time' in body
    body = phone.press('1')                 # first slot
    assert body.startswith('CON Confirm') and 'KES' in body
    body = phone.press('1')                 # confirm
    assert body.startswith('END Booked!'), body

    consultation = Consultation.query.filter_by(patient_id=patient_id).one()
    assert consultation.status == 'booked'
    assert consultation.specialty == 'dermatology'
    assert consultation.complaint == 'Itchy rash on arms for 2 weeks'
    assert consultation.reference in body
    sms = SmsMessage.query.filter_by(phone='+254799000002', purpose='booking').one()
    assert consultation.reference in sms.body
    assert SmsMessage.query.filter_by(purpose='booking_specialist').count() >= 1
    assert_screens_fit(phone)


def _to_confirm_screen(phone):
    """Registered patient: book a phone consultation with the first skin specialist and slot."""
    phone.dial()
    phone.press('1')            # See a specialist
    phone.press('1')            # Skin
    phone.press('Rash')
    phone.press('1')            # Phone call
    phone.press('1')            # first specialist
    body = phone.press('1')     # first slot
    assert body.startswith('CON Confirm'), body
    return body


def test_slot_cannot_be_double_booked(client):
    other = Patient.query.filter(Patient.phone != DEMO_PATIENT,
                                 ~Patient.phone.like('deleted-%')).first().phone
    first, second = Phone(client, session_id='a'), Phone(client, other, session_id='b')
    assert _to_confirm_screen(first) == _to_confirm_screen(second)  # same doctor and slot
    assert first.press('1').startswith('END Booked!')
    # The second phone was shown the same slot; confirming must fail gracefully.
    body = second.press('1')
    assert body.startswith('CON ') and 'taken' in body.lower(), body


def test_waitlist_when_no_specialist_available(client):
    patient_id = Patient.query.filter_by(phone=DEMO_PATIENT).one().id

    def waiting():
        return Consultation.query.filter_by(patient_id=patient_id, status='waitlist',
                                            specialty='endocrinology').count()

    before = waiting()
    phone = Phone(client)
    phone.dial()
    body = phone.press('1')
    body = phone.choose(body, 'Diabetes')
    phone.press('Sugar very high')
    body = phone.press('1')
    assert body.startswith('END ') and 'We will SMS you' in body
    assert waiting() == before + 1
    assert SmsMessage.query.filter_by(phone=DEMO_PATIENT, purpose='waitlist').count() == 1


def test_view_and_cancel_appointment(client):
    phone = Phone(client)
    phone.dial()
    phone.press('1')
    phone.press('1')            # Skin (first option)
    phone.press('Dark patches')
    phone.press('1')
    phone.press('1')
    phone.press('1')
    phone.press('1')            # booked

    phone.dial()
    body = phone.press('2')     # My appointments
    assert 'Your appointments' in body
    body = phone.press('1')
    assert '1. Cancel appointment' in body
    phone.press('1')
    body = phone.press('1')     # Yes, cancel
    assert body.startswith('END ') and 'cancelled' in body
    patient = Patient.query.filter_by(phone=DEMO_PATIENT).one()
    assert Consultation.query.filter_by(patient_id=patient.id, status='cancelled',
                                        cancelled_by='patient').count() >= 1


def test_completed_consultation_advice_and_follow_up(app, client):
    patient = Patient.query.filter_by(phone=DEMO_PATIENT).one()
    specialist = Specialist.query.filter_by(specialty='dermatology', county='Kisumu').one()
    db.session.add(Consultation(patient=patient, specialist=specialist, specialty='dermatology',
                                status='completed', advice='Use the cream twice a day for four weeks.',
                                scheduled_at=specialist.created_at, county='Kisumu'))
    db.session.commit()

    phone = Phone(client)
    phone.dial()
    body = phone.press('2')
    body = phone.choose(body, 'Advice')
    assert 'cream twice a day' in body
    body = phone.press('2')     # Book follow-up
    assert 'Choose a time' in body


def test_report_illness_urgent_and_routine(client):
    phone = Phone(client)
    phone.dial()
    body = phone.press('3')
    body = phone.choose(body, 'Diarrhoea')
    phone.press('2')            # 2-3 people
    body = phone.press('2')     # no danger signs
    assert body.startswith('END ') and 'ORS' in body

    phone.dial()
    body = phone.press('3')
    body = phone.choose(body, 'bleeding')
    phone.press('1')
    body = phone.press('2')
    assert 'NOW' in body and '1199' in body

    reports = SymptomReport.query.filter(SymptomReport.reporter_hash.isnot(None)).all()
    assert {r.syndrome for r in reports} == {'diarrhoea', 'bleeding'}
    assert all(r.county == 'Kisumu' for r in reports)
    diarrhoea = next(r for r in reports if r.syndrome == 'diarrhoea')
    assert diarrhoea.people_affected == 2


def test_unregistered_report_asks_location_and_stores_no_phone(client):
    phone = Phone(client, '+254799000009')
    phone.dial()
    phone.press('1')
    body = phone.press('3')
    body = phone.choose(body, 'Fever')
    phone.press('1')
    body = phone.press('2')
    assert 'region' in body.lower()
    body = phone.choose(body, 'Rift Valley')
    body = phone.choose(body, 'Turkana')   # second page of Rift Valley counties
    assert body.startswith('END ') and 'malaria' in body.lower()
    report = SymptomReport.query.filter_by(county='Turkana', syndrome='fever').order_by(
        SymptomReport.id.desc()).first()
    assert report.patient_id is None
    assert '+254799000009' not in (report.reporter_hash or '')


def test_repeat_reports_are_rate_limited(client):
    before = SymptomReport.query.count()
    for i in range(5):
        phone = Phone(client, session_id=f'r{i}')
        phone.dial()
        phone.press('3')
        phone.press('1')        # Fever
        phone.press('1')
        phone.press('2')
    assert SymptomReport.query.count() == before + 3


def test_health_alerts_for_county(client):
    phone = Phone(client, '+254799000010')
    phone.dial()
    phone.press('1')
    body = phone.press('4')
    body = phone.choose(body, 'Rift Valley')
    body = phone.choose(body, 'Turkana')
    assert 'Measles' in body and 'Malaria' in body
    body = phone.choose(body, 'Measles')
    assert 'vaccination' in body.lower()
    assert_screens_fit(phone)


def test_expired_alerts_are_hidden(app, client):
    for alert in HealthAlert.query:
        alert.active = False
    db.session.commit()
    phone = Phone(client)
    phone.dial()
    body = phone.press('4')
    assert 'No alerts for Kisumu' in body


def test_emergency_numbers(client):
    phone = Phone(client)
    phone.dial()
    body = phone.press('5')
    assert body.startswith('END ') and '999' in body and '1199' in body


def test_kiswahili_flow(client):
    phone = Phone(client, '+254799000011')
    phone.dial()
    body = phone.press('2')
    assert 'Ona daktari bingwa' in body
    body = phone.press('5')
    assert 'DHARURA' in body


def test_account_language_and_delete(client):
    phone = Phone(client)
    phone.dial()
    phone.press('6')
    phone.press('1')
    body = phone.press('2')     # Kiswahili
    assert 'Imehifadhiwa' in body
    assert Patient.query.filter_by(phone=DEMO_PATIENT).one().language == 'sw'

    phone.dial()
    phone.press('6')
    phone.press('4')
    body = phone.press('1')
    assert body.startswith('END ')
    assert Patient.query.filter_by(phone=DEMO_PATIENT).first() is None
    assert Patient.query.filter_by(name='Deleted user').count() == 1


def test_navigation_back_and_main_menu(client):
    phone = Phone(client)
    phone.dial()
    phone.press('1')
    body = phone.press('0')
    assert '1. See a specialist' in body
    phone.press('3')
    body = phone.press('00')
    assert '1. See a specialist' in body
    body = phone.press('42')
    assert 'Invalid choice' in body


def test_session_survives_between_requests(client):
    """State is in the database, not process memory."""
    phone = Phone(client)
    phone.dial()
    phone.press('3')
    from models import UssdSession
    assert db.session.get(UssdSession, 'sess-1').state == 'sx_group'


def test_bad_request_rejected(client):
    assert client.post('/ussd', data={'text': ''}).status_code == 400


def test_every_screen_fits_on_a_phone(client):
    phone = Phone(client)
    phone.dial()
    for key in ['1', '0', '2', '0', '3', '0', '4', '0', '6', '3', '0', '0']:
        phone.press(key)
    phone.dial()
    body = phone.press('1')
    while '9. ' in body:
        body = phone.press('9')
    assert_screens_fit(phone)

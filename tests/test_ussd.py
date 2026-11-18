from models import db, Patient, Appointment, UssdSession

PHONE = '+254799000111'


def ussd(client, text, session_id='ATUid_test', phone=PHONE):
    response = client.post('/ussd', data={'sessionId': session_id, 'phoneNumber': phone,
                                          'serviceCode': '*384*4040#', 'text': text})
    assert response.status_code == 200
    assert response.content_type.startswith('text/plain')
    body = response.get_data(as_text=True)
    assert body.startswith(('CON ', 'END ')), body
    # Each USSD hop may land on a different worker: drop all in-process state.
    db.session.remove()
    return body


def test_first_screen_is_language_menu(client):
    body = ussd(client, '')
    assert body.startswith('CON ')
    assert '1. English' in body


def test_registration_flow_persists_patient(client):
    steps = ['', '1', '1*1', '1*1*Wanjiru Kamau', '1*1*Wanjiru Kamau*34',
             '1*1*Wanjiru Kamau*34*2', '1*1*Wanjiru Kamau*34*2*Nyeri']
    for text in steps:
        ussd(client, text)
    body = ussd(client, steps[-1] + '*2')  # skip GPS coordinates
    assert 'successful' in body.lower(), body

    patient = Patient.get_by_phone(PHONE)
    assert patient is not None
    assert patient.name == 'Wanjiru Kamau'
    assert patient.age == 34
    assert patient.location == 'Nyeri'


def test_session_state_is_stored_in_database(client):
    ussd(client, '')
    ussd(client, '1')
    record = db.session.get(UssdSession, 'ATUid_test')
    assert record is not None
    assert record.language == 'en'
    assert record.state == 'main_menu'


def test_registered_patient_can_book_appointment(client):
    phone = '+254711001122'  # demo patient Jane Wanjiku (has coordinates)
    before = Appointment.query.count()
    ussd(client, '', 'book1', phone)
    ussd(client, '1', 'book1', phone)            # English
    ussd(client, '1*2', 'book1', phone)          # Schedule appointment
    ussd(client, '1*2*1', 'book1', phone)        # first date
    ussd(client, '1*2*1*1', 'book1', phone)      # first time slot
    body = ussd(client, '1*2*1*1*1', 'book1', phone)  # first provider
    assert 'scheduled successfully' in body.lower(), body
    assert Appointment.query.count() == before + 1
    newest = Appointment.query.order_by(Appointment.id.desc()).first()
    assert newest.source == 'ussd'


def test_missing_fields_rejected(client):
    response = client.post('/ussd', data={'text': ''})
    assert response.status_code == 400

from conftest import login
from models import db, Bill, Message, Appointment, Patient


def test_data_survives_session_reset(app, client):
    """Writes go to the database, not process memory."""
    login(client, 'admin')
    client.post('/messages/1', data={'message': 'Please come in tomorrow.'})
    db.session.expire_all()
    contents = [m.content for m in Message.get_conversation(1, 1)]
    assert 'Please come in tomorrow.' in contents


def test_appointment_status_update_persists(app, client):
    login(client, 'admin')
    client.post('/appointment/update', data={'appointment_id': '2', 'status': 'confirmed'})
    db.session.expire_all()
    assert Appointment.get_by_id(2).status == 'confirmed'


def test_bill_lifecycle(app, client):
    login(client, 'admin')
    response = client.post('/billing/create', data={'patient_id': '1', 'appointment_id': ''})
    assert response.status_code == 302
    bill = Bill.query.order_by(Bill.id.desc()).first()

    client.post(f'/billing/{bill.id}/edit', data={
        'item_type': 'consultation', 'description': 'Consultation', 'amount': '300', 'quantity': '1'})
    db.session.expire_all()
    bill = db.session.get(Bill, bill.id)
    assert bill.total_amount == 300
    assert bill.items[0]['description'] == 'Consultation'

    client.post('/billing/record-payment', data={
        'bill_id': str(bill.id), 'amount': '100', 'payment_method': 'cash', 'reference': ''})
    db.session.expire_all()
    bill = db.session.get(Bill, bill.id)
    assert bill.status == 'partially_paid'

    client.post('/billing/record-payment', data={
        'bill_id': str(bill.id), 'amount': '200', 'payment_method': 'mpesa', 'reference': 'QAB123'})
    db.session.expire_all()
    bill = db.session.get(Bill, bill.id)
    assert bill.status == 'paid'
    assert bill.amount_paid == 300


def test_invalid_form_ids_do_not_500(client):
    login(client, 'admin')
    assert client.post('/billing/create', data={'patient_id': 'abc'}).status_code == 302
    assert client.post('/appointment/update',
                       data={'appointment_id': 'x', 'status': 'confirmed'}).status_code == 302
    assert client.post('/update_bill_status',
                       data={'bill_id': 'x', 'status': 'paid'}).status_code == 302


def test_symptoms_are_categorised(app):
    patient = Patient.get_by_id(1)
    symptom = patient.add_symptom('Severe chest pain and cough')
    assert symptom.severity == 'Severe'
    assert symptom.category == 'respiratory'
    assert symptom['text'] == 'Severe chest pain and cough'

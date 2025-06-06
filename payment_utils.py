from datetime import datetime, timedelta
from flask import render_template
from weasyprint import HTML
import os
from models_sqlalchemy import db, Payment, Appointment, Patient

def generate_payment_receipt(payment_id):
    """Generate a PDF receipt for a payment"""
    payment = Payment.query.get(payment_id)
    if not payment:
        return None
        
    appointment = Appointment.query.get(payment.appointment_id)
    patient = Patient.query.get(appointment.patient_id) if appointment else None
    
    # Render HTML template with payment details
    html = render_template('receipt.html', 
                         payment=payment,
                         appointment=appointment,
                         patient=patient)
    
    # Generate PDF
    receipt_dir = os.path.join('static', 'receipts')
    os.makedirs(receipt_dir, exist_ok=True)
    
    receipt_path = os.path.join(receipt_dir, f'receipt_{payment_id}.pdf')
    HTML(string=html).write_pdf(receipt_path)
    
    return receipt_path

def send_payment_reminder(appointment_id):
    """Send payment reminder for an appointment"""
    from app import send_sms  # Import here to avoid circular imports
    
    appointment = Appointment.query.get(appointment_id)
    if not appointment or not appointment.patient:
        return False
    
    patient = appointment.patient
    amount_due = appointment.price
    
    message = f"""
    Dear {patient.name},
    
    This is a reminder for your pending payment of KES {amount_due:.2f} for your appointment on {appointment.date.strftime('%Y-%m-%d')}.
    
    Please make the payment at your earliest convenience.
    
    Thank you,
    {appointment.provider.name}
    """
    
    # Send SMS
    if patient.phone_number:
        return send_sms(patient.phone_number, message)
    return False

def process_refund(payment_id, amount=None, reason=None):
    """Process a refund for a payment"""
    payment = Payment.query.get(payment_id)
    if not payment or payment.status != 'completed':
        return False, "Invalid payment or payment not completed"
    
    refund_amount = amount or payment.amount
    if refund_amount > payment.amount:
        return False, "Refund amount cannot exceed original payment"
    
    # In a real implementation, this would integrate with payment gateway
    try:
        # Create refund record
        refund = Payment(
            appointment_id=payment.appointment_id,
            amount=-refund_amount,  # Negative amount for refund
            payment_method=payment.payment_method,
            status='completed',
            mpesa_reference=f"REFUND_{payment.mpesa_reference or ''}",
            created_at=datetime.utcnow()
        )
        db.session.add(refund)
        db.session.commit()
        
        # Send confirmation
        send_refund_confirmation(payment_id, refund_amount, reason)
        
        return True, "Refund processed successfully"
    except Exception as e:
        db.session.rollback()
        return False, f"Error processing refund: {str(e)}"

def send_refund_confirmation(payment_id, amount, reason=None):
    """Send refund confirmation to patient"""
    from app import send_sms  # Import here to avoid circular imports
    
    payment = Payment.query.get(payment_id)
    if not payment or not payment.appointment or not payment.appointment.patient:
        return False
    
    patient = payment.appointment.patient
    
    message = f"""
    Dear {patient.name},
    
    A refund of KES {amount:.2f} has been processed for your payment.
    """
    
    if reason:
        message += f"\nReason: {reason}\n"
    
    message += "\nThank you,\nYour Healthcare Provider"
    
    if patient.phone_number:
        return send_sms(patient.phone_number, message)
    return False

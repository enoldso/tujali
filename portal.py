"""Specialist portal: consultation queue, notes and advice, hours, profile."""
from datetime import timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from auth import roles_required
from forms import AvailabilityForm, ConsultationForm, ProfileForm
from i18n import format_when, t
from models import db, now, Availability, Consultation
from scheduling import available_slots
from sms import send_sms

bp = Blueprint('portal', __name__, url_prefix='/portal')


def _me():
    specialist = current_user.specialist
    if specialist is None:
        abort(403, description='This area is for specialists.')
    return specialist


@bp.route('/')
@roles_required('specialist')
def dashboard():
    me = _me()
    today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)
    mine = Consultation.query.filter_by(specialist_id=me.id)

    today = (mine.filter(Consultation.status == 'booked',
                         Consultation.scheduled_at >= today_start,
                         Consultation.scheduled_at < today_start + timedelta(days=1))
             .order_by(Consultation.scheduled_at).all())
    upcoming = (mine.filter(Consultation.status == 'booked',
                            Consultation.scheduled_at >= today_start + timedelta(days=1))
                .order_by(Consultation.scheduled_at).limit(8).all())
    overdue = (mine.filter(Consultation.status == 'booked',
                           Consultation.scheduled_at < now() - timedelta(minutes=30))
               .order_by(Consultation.scheduled_at).all())
    month = mine.filter(Consultation.scheduled_at >= month_start).all()
    stats = {
        'completed': sum(1 for c in month if c.status == 'completed'),
        'upcoming': mine.filter(Consultation.status == 'booked',
                                Consultation.scheduled_at >= now()).count(),
        'no_shows': sum(1 for c in month if c.status == 'no_show'),
        'earned': sum(c.fee_kes for c in month if c.payment_status == 'paid'),
    }
    slots = available_slots(me, limit=1)
    return render_template('specialist/dashboard.html', me=me, today=today, upcoming=upcoming,
                           overdue=overdue, stats=stats, next_slot=slots[0] if slots else None)


@bp.route('/consultations')
@roles_required('specialist')
def consultations():
    me = _me()
    view = request.args.get('view', 'upcoming')
    query = Consultation.query.filter_by(specialist_id=me.id)
    if view == 'upcoming':
        query = query.filter_by(status='booked').order_by(Consultation.scheduled_at)
    elif view == 'completed':
        query = query.filter_by(status='completed').order_by(Consultation.scheduled_at.desc())
    elif view == 'missed':
        query = query.filter(Consultation.status.in_(('cancelled', 'no_show'))).order_by(
            Consultation.scheduled_at.desc())
    else:
        view = 'all'
        query = query.order_by(Consultation.scheduled_at.desc())
    return render_template('specialist/consultations.html', me=me, view=view,
                           consultations=query.limit(200).all())


def _own_consultation(consultation_id):
    consultation = db.session.get(Consultation, consultation_id)
    if consultation is None or consultation.specialist_id != _me().id:
        abort(404)
    return consultation


@bp.route('/consultations/<int:consultation_id>', methods=['GET', 'POST'])
@roles_required('specialist')
def consultation(consultation_id):
    c = _own_consultation(consultation_id)
    form = ConsultationForm(obj=c)

    if form.validate_on_submit():
        action = request.form.get('action', 'save')
        c.clinical_notes = form.clinical_notes.data or None
        c.payment_status = form.payment_status.data
        c.payment_ref = form.payment_ref.data or None
        new_advice = (form.advice.data or '').strip() or None
        advice_changed = new_advice and new_advice != c.advice
        c.advice = new_advice

        if action == 'complete' and c.status == 'booked':
            c.status = 'completed'
            c.completed_at = now()
            flash('Consultation completed.', 'success')
        elif action == 'no_show' and c.status == 'booked':
            c.status = 'no_show'
            flash('Marked as no-show.', 'info')
        elif action == 'cancel' and c.status == 'booked':
            c.status = 'cancelled'
            c.cancelled_by = 'specialist'
            send_sms(c.patient.phone,
                     t('sms_cancelled_by_doctor', c.patient.language, doctor=c.specialist.short_name,
                       ref=c.reference, code=_ussd_code()),
                     purpose='cancellation', commit=False)
            flash('Consultation cancelled and the patient was told by SMS.', 'info')
        else:
            flash('Saved.', 'success')

        if advice_changed and c.status == 'completed':
            send_sms(c.patient.phone,
                     t('sms_advice', c.patient.language, doctor=c.specialist.short_name,
                       ref=c.reference, advice=c.advice),
                     purpose='advice', commit=False)
            flash('Advice sent to the patient by SMS.', 'success')
        db.session.commit()
        return redirect(url_for('portal.consultation', consultation_id=c.id))

    history = (Consultation.query.filter(Consultation.patient_id == c.patient_id,
                                         Consultation.specialist_id == c.specialist_id,
                                         Consultation.id != c.id)
               .order_by(Consultation.created_at.desc()).limit(10).all())
    return render_template('specialist/consultation.html', c=c, form=form, history=history)


def _ussd_code():
    from flask import current_app
    return current_app.config['USSD_CODE']


@bp.route('/availability', methods=['GET', 'POST'])
@roles_required('specialist')
def availability():
    me = _me()
    form = AvailabilityForm()
    if form.validate_on_submit():
        clash = [b for b in me.availability if b.weekday == form.weekday.data
                 and b.start_time < form.end_time.data and form.start_time.data < b.end_time]
        if clash:
            flash('That overlaps hours you already have on that day.', 'warning')
        else:
            db.session.add(Availability(specialist=me, weekday=form.weekday.data,
                                        start_time=form.start_time.data,
                                        end_time=form.end_time.data,
                                        slot_minutes=form.slot_minutes.data))
            db.session.commit()
            flash('Hours added.', 'success')
            return redirect(url_for('portal.availability'))
    preview = available_slots(me, limit=8)
    return render_template('specialist/availability.html', me=me, form=form, preview=preview,
                           format_when=format_when)


@bp.route('/availability/<int:block_id>/delete', methods=['POST'])
@roles_required('specialist')
def delete_availability(block_id):
    block = db.session.get(Availability, block_id)
    if block is None or block.specialist_id != _me().id:
        abort(404)
    db.session.delete(block)
    db.session.commit()
    flash('Hours removed. Existing bookings are not affected.', 'info')
    return redirect(url_for('portal.availability'))


@bp.route('/profile', methods=['GET', 'POST'])
@roles_required('specialist')
def profile():
    me = _me()
    form = ProfileForm(obj=me)
    if request.method == 'GET':
        form.phone.data = current_user.phone
    if form.validate_on_submit():
        if not (form.offers_phone.data or form.offers_in_person.data):
            form.offers_phone.errors.append('Offer at least one type of consultation.')
        else:
            current_user.phone = form.phone.data
            form.populate_obj(me)
            me.facility = me.facility or None
            db.session.commit()
            flash('Profile updated.', 'success')
            return redirect(url_for('portal.profile'))
    return render_template('specialist/profile.html', me=me, form=form)

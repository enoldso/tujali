"""Administration: specialist verification, staff accounts, service overview."""
from collections import Counter
from datetime import timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from auth import roles_required
from forms import StaffForm
from models import (db, now, Consultation, Patient, SmsMessage, Specialist, SymptomReport, User)
from reference import SPECIALTIES, SPECIALTY_LABELS, SPECIALTY_NAMES

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@roles_required('admin')
def dashboard():
    week_ago = now() - timedelta(days=7)
    month_ago = now() - timedelta(days=30)

    recent = Consultation.query.filter(Consultation.created_at >= month_ago).all()
    finished = [c for c in recent if c.status in ('completed', 'no_show')]
    stats = {
        'patients': Patient.query.filter(~Patient.phone.like('deleted-%')).count(),
        'new_patients': Patient.query.filter(Patient.created_at >= week_ago).count(),
        'bookings_week': sum(1 for c in recent if c.created_at >= week_ago and c.status != 'waitlist'),
        'completion_rate': (round(100 * sum(c.status == 'completed' for c in finished) / len(finished))
                            if finished else None),
        'verified': Specialist.query.filter_by(verified=True).count(),
        'pending': Specialist.query.filter_by(verified=False).count(),
        'waitlist': Consultation.query.filter_by(status='waitlist').count(),
        'reports_week': SymptomReport.query.filter(SymptomReport.created_at >= week_ago).count(),
    }

    by_specialty = Counter(c.specialty for c in recent if c.status != 'waitlist')
    specialty_chart = [(SPECIALTY_NAMES[code], by_specialty.get(code, 0)) for code, _, _ in SPECIALTIES]

    days = [(now() - timedelta(days=i)).date() for i in range(29, -1, -1)]
    per_day = Counter(c.created_at.date() for c in recent if c.status != 'waitlist')
    bookings_chart = {'labels': [d.strftime('%d %b') for d in days],
                      'values': [per_day.get(d, 0) for d in days]}

    pending = (Specialist.query.filter_by(verified=False)
               .order_by(Specialist.created_at).limit(6).all())
    sms = SmsMessage.query.order_by(SmsMessage.created_at.desc()).limit(8).all()
    return render_template('admin/dashboard.html', stats=stats, unmet=unmet_demand(),
                           specialty_chart=specialty_chart, bookings_chart=bookings_chart,
                           pending=pending, sms=sms)


def unmet_demand(days=90):
    """Waitlisted requests (no specialist was available), grouped for recruitment."""
    rows = (Consultation.query.filter(Consultation.status == 'waitlist',
                                      Consultation.created_at >= now() - timedelta(days=days)).all())
    groups = Counter((c.specialty, c.county or 'Unknown', c.mode) for c in rows)
    return [{'specialty': SPECIALTY_NAMES.get(s, s), 'county': county,
             'mode': 'Phone' if mode == 'phone' else 'In person', 'requests': n}
            for (s, county, mode), n in groups.most_common(12)]


@bp.route('/specialists')
@roles_required('admin')
def specialists():
    view = request.args.get('view', 'pending')
    query = Specialist.query.join(User)
    if view == 'pending':
        query = query.filter(Specialist.verified.is_(False))
    elif view == 'verified':
        query = query.filter(Specialist.verified.is_(True))
    else:
        view = 'all'
    return render_template('admin/specialists.html', view=view,
                           specialists=query.order_by(Specialist.created_at.desc()).all(),
                           counts={'pending': Specialist.query.filter_by(verified=False).count(),
                                   'verified': Specialist.query.filter_by(verified=True).count()})


@bp.route('/specialists/<int:specialist_id>/<action>', methods=['POST'])
@roles_required('admin')
def specialist_action(specialist_id, action):
    specialist = db.get_or_404(Specialist, specialist_id)
    if action == 'verify':
        specialist.verified = True
        specialist.verified_at = now()
        db.session.commit()
        notified = notify_waitlist(specialist)
        flash(f'{specialist.display_name} is verified and now bookable on USSD.'
              + (f' {notified} waiting patients were told by SMS.' if notified else ''), 'success')
    elif action == 'unverify':
        specialist.verified = False
        db.session.commit()
        flash(f'{specialist.display_name} is hidden from patients.', 'info')
    elif action in ('suspend', 'reactivate'):
        specialist.user.is_active_account = action == 'reactivate'
        db.session.commit()
        flash(f'Account {"reactivated" if action == "reactivate" else "suspended"}.', 'info')
    return redirect(request.referrer or url_for('admin.specialists'))


def notify_waitlist(specialist):
    """Tell patients waiting for this specialty that someone is now available."""
    from sms import send_sms
    waiting = Consultation.query.filter(Consultation.status == 'waitlist',
                                        Consultation.specialty == specialist.specialty,
                                        Consultation.notified_at.is_(None)).all()
    code = current_app.config['USSD_CODE']
    for c in waiting:
        if c.mode == 'in_person' and not specialist.offers_in_person:
            continue
        if c.mode == 'phone' and not specialist.offers_phone:
            continue
        lang = c.patient.language
        label = SPECIALTY_LABELS.get(c.specialty, {}).get(lang, c.specialty)
        body = (f'Tujali: a {label} specialist is now available for your request {c.reference}. '
                f'Dial {code} > 1 to book.') if lang != 'sw' else (
                f'Tujali: daktari wa {label} sasa anapatikana kwa ombi lako {c.reference}. '
                f'Piga {code} > 1 kupanga miadi.')
        send_sms(c.patient.phone, body, purpose='waitlist_match', commit=False)
        c.notified_at = now()
    db.session.commit()
    return sum(1 for c in waiting if c.notified_at)


@bp.route('/users', methods=['GET', 'POST'])
@roles_required('admin')
def users():
    form = StaffForm()
    if form.validate_on_submit():
        user = User(name=form.name.data.strip(), email=form.email.data.strip().lower(),
                    phone=form.phone.data or None, role=form.role.data,
                    organisation=form.organisation.data or None)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'{user.role_label} account created for {user.name}. Share the temporary '
              f'password with them securely.', 'success')
        return redirect(url_for('admin.users'))
    staff = User.query.order_by(User.role, User.name).all()
    return render_template('admin/users.html', form=form, staff=staff)


@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@roles_required('admin')
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
    else:
        user.is_active_account = not user.is_active_account
        db.session.commit()
        flash(f'{user.name} {"reactivated" if user.is_active_account else "deactivated"}.', 'info')
    return redirect(url_for('admin.users'))


@bp.route('/sms')
@roles_required('admin')
def sms_log():
    messages = SmsMessage.query.order_by(SmsMessage.created_at.desc()).limit(200).all()
    return render_template('admin/sms.html', messages=messages,
                           backend=current_app.config['SMS_BACKEND'])

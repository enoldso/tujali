"""Public pages: landing page, specialist sign-up, USSD simulator."""
from flask import (Blueprint, abort, current_app, flash, redirect, render_template, url_for)
from flask_login import login_user

from forms import JoinForm
from models import db, Consultation, Patient, Specialist, SymptomReport, User
from reference import SPECIALTIES, SYNDROMES

bp = Blueprint('public', __name__)


@bp.route('/')
def index():
    stats = {
        'patients': Patient.query.count(),
        'consultations': Consultation.query.filter(
            Consultation.status.in_(('booked', 'completed'))).count(),
        'specialists': Specialist.query.filter_by(verified=True).count(),
        'reports': SymptomReport.query.count(),
    }
    return render_template('landing.html', stats=stats, specialties=SPECIALTIES,
                           syndromes=SYNDROMES)


@bp.route('/join', methods=['GET', 'POST'])
def join():
    form = JoinForm()
    if form.validate_on_submit():
        user = User(name=form.name.data.strip(), email=form.email.data.strip().lower(),
                    phone=form.phone.data, role='specialist')
        user.set_password(form.password.data)
        user.specialist = Specialist(
            specialty=form.specialty.data, license_number=form.license_number.data.strip(),
            facility=(form.facility.data or '').strip() or None, county=form.county.data,
            fee_kes=form.fee_kes.data, offers_phone=form.offers_phone.data,
            offers_in_person=form.offers_in_person.data, verified=False)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Application received. Add your weekly hours while we verify your licence; '
              'patients will see you once you are verified.', 'success')
        return redirect(url_for('portal.availability'))
    return render_template('join.html', form=form)


@bp.route('/simulator')
def simulator():
    """Phone simulator for demos and testing (off in production by default)."""
    if not current_app.config['ENABLE_USSD_SIMULATOR']:
        abort(404)
    return render_template('simulator.html', ussd_code=current_app.config['USSD_CODE'])

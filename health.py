"""Outbreak surveillance for health officers: signals, trends, alerts."""
import csv
import io
from datetime import timedelta

from flask import (Blueprint, Response, current_app, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user

from auth import roles_required
from forms import AlertForm
from models import db, now, HealthAlert, Patient, SymptomReport
from reference import COUNTIES, SYNDROMES, SYNDROME_LABELS, SYNDROME_WATCH
from sms import send_sms
import surveillance

bp = Blueprint('health', __name__, url_prefix='/surveillance')


def _filters():
    days = request.args.get('days', 30, type=int)
    days = days if days in (7, 30, 90) else 30
    county = request.args.get('county') or None
    syndrome = request.args.get('syndrome') or None
    return days, (county if county in COUNTIES else None), \
        (syndrome if syndrome in SYNDROME_LABELS else None)


@bp.route('/')
@roles_required('health_officer')
def dashboard():
    days, county, syndrome = _filters()
    data = surveillance.overview(days=days, county=county, syndrome=syndrome)
    signals = surveillance.detect_signals()
    if county:
        signals = [s for s in signals if s['county'] == county]
    if syndrome:
        signals = [s for s in signals if s['syndrome'] == syndrome]
    live_alerts = [a for a in HealthAlert.query.filter_by(active=True).all() if a.is_live]
    alerted = {(a.county, a.syndrome) for a in live_alerts}
    return render_template('surveillance/dashboard.html', data=data, signals=signals,
                           alerted=alerted, live_alerts=live_alerts, days=days, county=county,
                           syndrome=syndrome, counties=COUNTIES, syndromes=SYNDROMES,
                           syndrome_labels=SYNDROME_LABELS, watch=SYNDROME_WATCH)


@bp.route('/alerts', methods=['GET', 'POST'])
@roles_required('health_officer')
def alerts():
    form = AlertForm()
    if request.method == 'GET':
        form.county.data = request.args.get('county', '')
        form.syndrome.data = request.args.get('syndrome', '')
        if request.args.get('syndrome') in SYNDROME_LABELS and request.args.get('county'):
            label = SYNDROME_LABELS[request.args['syndrome']]['en']
            form.title.data = f'{label} rising in {request.args["county"]}'[:60]
            form.level.data = 'warning'

    if form.validate_on_submit():
        alert = HealthAlert(title=form.title.data.strip(), message_en=form.message_en.data.strip(),
                            message_sw=(form.message_sw.data or '').strip() or None,
                            county=form.county.data or None, syndrome=form.syndrome.data or None,
                            level=form.level.data, created_by=current_user,
                            expires_at=(now() + timedelta(days=form.expires_in_days.data)
                                        if form.expires_in_days.data else None))
        db.session.add(alert)
        db.session.commit()
        if form.send_sms.data:
            alert.sms_recipients = _broadcast(alert)
            db.session.commit()
            flash(f'Alert published and sent by SMS to {alert.sms_recipients} people.', 'success')
        else:
            flash('Alert published. Patients will see it under "Health alerts" on USSD.', 'success')
        return redirect(url_for('health.alerts'))

    alerts_list = HealthAlert.query.order_by(HealthAlert.created_at.desc()).limit(100).all()
    return render_template('surveillance/alerts.html', form=form, alerts=alerts_list)


def _broadcast(alert):
    limit = current_app.config['ALERT_SMS_LIMIT']
    query = Patient.query.filter(~Patient.phone.like('deleted-%'))
    if alert.county:
        query = query.filter(Patient.county == alert.county)
    sent = 0
    for patient in query.limit(limit):
        send_sms(patient.phone, f'Tujali health alert: {alert.title}. {alert.message(patient.language)}',
                 purpose='alert', commit=False)
        sent += 1
    db.session.commit()
    return sent


@bp.route('/alerts/<int:alert_id>/end', methods=['POST'])
@roles_required('health_officer')
def end_alert(alert_id):
    alert = db.get_or_404(HealthAlert, alert_id)
    alert.active = False
    db.session.commit()
    flash('Alert removed from USSD.', 'info')
    return redirect(url_for('health.alerts'))


@bp.route('/export.csv')
@roles_required('health_officer')
def export():
    days, county, syndrome = _filters()
    query = SymptomReport.query.filter(SymptomReport.created_at >= now() - timedelta(days=days))
    if county:
        query = query.filter_by(county=county)
    if syndrome:
        query = query.filter_by(syndrome=syndrome)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['reported_at', 'county', 'syndrome', 'people_affected', 'danger_signs'])
    for r in query.order_by(SymptomReport.created_at):
        writer.writerow([r.created_at.strftime('%Y-%m-%d %H:%M'), r.county, r.syndrome,
                         r.people_affected, 'yes' if r.danger_signs else 'no'])
    filename = f"tujali-reports-{now().strftime('%Y%m%d')}.csv"
    return Response(buffer.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})

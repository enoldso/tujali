"""USSD patient journey (Africa's Talking).

Each screen has a renderer (builds the menu text) and a handler (acts on the
user's input). Session state is stored in the ussd_sessions table so any
worker can serve the next step of a session.

Navigation conventions on every screen:  0 = back,  00 = main menu,
9 = more (on long lists).
"""
import hashlib
import logging
import random
from datetime import datetime, timedelta

from flask import current_app

from i18n import t, format_when, SYNDROME_ADVICE
from models import (db, now, Patient, Consultation, Specialist, SymptomReport, HealthAlert,
                    UssdSession)
from reference import (REGIONS, region_counties, SPECIALTIES, SPECIALTY_LABELS, SYNDROMES,
                       URGENT_SYNDROMES, HOUSEHOLD_SIZES, EMERGENCY_NUMBERS)
from scheduling import bookable_specialists, available_slots, is_slot_free
from sms import send_sms

logger = logging.getLogger(__name__)

MAX_SCREEN = 182          # characters most networks display
LIST_BUDGET = 150         # room left for a one-line notice above a list
MAX_ITEMS_PER_PAGE = 8    # options 1-8, 9 = more
SESSION_MAX_AGE = timedelta(hours=6)
MAX_REPORTS_PER_DAY = 3   # per reporter and illness type

RENDER = {}
HANDLE = {}


def screen(name):
    def register(cls):
        RENDER[name] = cls.render
        HANDLE[name] = cls.handle
        return cls
    return register


# ---------------------------------------------------------------------------
# Session plumbing
# ---------------------------------------------------------------------------

class Ctx:
    def __init__(self, session, patient):
        self.session = session
        self.patient = patient
        self.notice = None

    @property
    def lang(self):
        return self.session['language']

    @lang.setter
    def lang(self, value):
        self.session['language'] = value

    @property
    def data(self):
        return self.session['data']

    @property
    def phone(self):
        return self.session['phone']

    def t(self, key, **values):
        return t(key, self.lang, **values)

    def con(self, body):
        # A notice ("Saved.", "Invalid choice") is only shown if the screen still fits.
        if self.notice and len(self.notice) + 1 + len(body) <= MAX_SCREEN:
            body = f'{self.notice}\n{body}'
        return 'CON ' + body

    def end(self, body):
        return 'END ' + body

    def goto(self, state, notice=None):
        self.session['state'] = state
        if notice:
            self.notice = notice
        return RENDER[state](self)

    def invalid(self):
        return self.goto(self.session['state'], notice=self.t('invalid'))

    @property
    def ussd_code(self):
        return current_app.config.get('USSD_CODE', '*384*4040#')


def ussd_callback(session_id, phone, text):
    """Handle one USSD request; returns 'CON ...' or 'END ...'."""
    record = db.session.get(UssdSession, session_id)
    if record is None:
        record = UssdSession(session_id=session_id, phone=phone, state='start',
                             language='en', data={})
    session = {'phone': record.phone, 'state': record.state, 'language': record.language,
               'data': dict(record.data or {})}

    try:
        patient = Patient.query.filter_by(phone=session['phone']).first()
        response = process(Ctx(session, patient), text or '')
    except Exception:
        logger.exception('USSD error')
        db.session.rollback()
        response = 'END ' + t('error', session.get('language', 'en'))

    try:
        record.state = session['state']
        record.language = session['language']
        record.data = dict(session['data'])
        record.updated_at = now()
        db.session.add(record)
        if random.random() < 0.01:
            UssdSession.query.filter(UssdSession.updated_at < now() - SESSION_MAX_AGE).delete(
                synchronize_session=False)
        db.session.commit()
    except Exception:
        logger.exception('Could not save USSD session')
        db.session.rollback()
    return response


def process(ctx, text):
    inp = text.split('*')[-1].strip() if text else ''

    if not text:  # a fresh dial
        ctx.data.clear()
        if ctx.patient:
            ctx.lang = ctx.patient.language
            ctx.patient.last_seen_at = now()
            db.session.commit()
            return ctx.goto('main')
        return ctx.goto('lang')

    if inp == '00':
        return ctx.goto('main')

    handler = HANDLE.get(ctx.session['state'])
    if handler is None:
        return ctx.goto('main')
    return handler(ctx, inp)


def require_patient(ctx, next_state):
    if ctx.patient:
        return ctx.goto(next_state)
    ctx.data['after_reg'] = next_state
    return ctx.goto('reg_name')


# ---------------------------------------------------------------------------
# Paged lists
# ---------------------------------------------------------------------------

def _pages(ctx, header, labels):
    footer = len('\n' + ctx.t('more')) + len('\n' + ctx.t('back'))
    pages, current, length = [], [], len(header) + footer
    for index, label in enumerate(labels):
        line = len(f'\n{len(current) + 1}. {label}')
        if current and (len(current) >= MAX_ITEMS_PER_PAGE or length + line > LIST_BUDGET):
            pages.append(current)
            current, length = [], len(header) + footer
            line = len(f'\n1. {label}')
        current.append(index)
        length += line
    if current:
        pages.append(current)
    return pages


def render_list(ctx, key, header, labels):
    pages = _pages(ctx, header, labels)
    page = min(ctx.data.get(key + '_page', 0), max(len(pages) - 1, 0))
    lines = [header]
    for number, index in enumerate(pages[page] if pages else [], 1):
        lines.append(f'{number}. {labels[index]}')
    if page < len(pages) - 1:
        lines.append(ctx.t('more'))
    lines.append(ctx.t('back'))
    return ctx.con('\n'.join(lines))


def pick(ctx, key, header, labels, inp):
    """Returns ('item', index), ('more', None), ('back', None) or ('invalid', None)."""
    pages = _pages(ctx, header, labels)
    page = min(ctx.data.get(key + '_page', 0), max(len(pages) - 1, 0))
    if inp == '0':
        if page > 0:
            ctx.data[key + '_page'] = page - 1
            return 'more', None
        ctx.data.pop(key + '_page', None)
        return 'back', None
    if inp == '9' and page < len(pages) - 1:
        ctx.data[key + '_page'] = page + 1
        return 'more', None
    if inp.isdigit() and pages and 1 <= int(inp) <= len(pages[page]):
        ctx.data.pop(key + '_page', None)
        return 'item', pages[page][int(inp) - 1]
    return 'invalid', None


# ---------------------------------------------------------------------------
# Language, main menu, emergency
# ---------------------------------------------------------------------------

@screen('lang')
class Language:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('welcome'))

    @staticmethod
    def handle(ctx, inp):
        if inp not in ('1', '2'):
            return ctx.invalid()
        ctx.lang = 'en' if inp == '1' else 'sw'
        return ctx.goto('main')


@screen('main')
class MainMenu:
    @staticmethod
    def render(ctx):
        greeting = f', {ctx.patient.first_name}' if ctx.patient else ''
        return ctx.con(ctx.t('main', greeting=greeting))

    @staticmethod
    def handle(ctx, inp):
        ctx.data.clear()
        if inp == '1':
            return require_patient(ctx, 'bk_specialty')
        if inp == '2':
            return require_patient(ctx, 'appts')
        if inp == '3':
            return ctx.goto('sx_group')
        if inp == '4':
            return ctx.goto('alerts')
        if inp == '5':
            numbers = '\n'.join(f'{number} {labels[ctx.lang]}' for number, labels in EMERGENCY_NUMBERS)
            return ctx.end(ctx.t('emergency', numbers=numbers))
        if inp == '6':
            return require_patient(ctx, 'account')
        return ctx.invalid()


# ---------------------------------------------------------------------------
# Registration and location
# ---------------------------------------------------------------------------

@screen('reg_name')
class RegName:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('reg_name'))

    @staticmethod
    def handle(ctx, inp):
        name = ' '.join(inp.split())
        if inp == '0':
            return ctx.goto('main')
        if not (2 <= len(name) <= 60) or not any(ch.isalpha() for ch in name):
            return ctx.invalid()
        ctx.data['reg_name'] = name.title()
        return ctx.goto('reg_age')


@screen('reg_age')
class RegAge:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('reg_age'))

    @staticmethod
    def handle(ctx, inp):
        if inp == '0':
            return ctx.goto('reg_name')
        if not inp.isdigit() or not 0 < int(inp) <= 120:
            return ctx.invalid()
        ctx.data['reg_age'] = int(inp)
        return ctx.goto('reg_gender')


@screen('reg_gender')
class RegGender:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('reg_gender'))

    @staticmethod
    def handle(ctx, inp):
        if inp == '0':
            return ctx.goto('reg_age')
        gender = {'1': 'female', '2': 'male', '3': 'other'}.get(inp)
        if not gender:
            return ctx.invalid()
        ctx.data['reg_gender'] = gender
        ctx.data['loc_purpose'] = 'reg'
        return ctx.goto('pick_region')


LOCATION_BACK = {'reg': 'reg_gender', 'sx': 'sx_danger', 'alerts': 'main', 'account': 'account'}


@screen('pick_region')
class PickRegion:
    @staticmethod
    def labels(ctx):
        return [names[ctx.lang] for _, names, _ in REGIONS]

    @staticmethod
    def render(ctx):
        return render_list(ctx, 'region', ctx.t('pick_region'), PickRegion.labels(ctx))

    @staticmethod
    def handle(ctx, inp):
        action, index = pick(ctx, 'region', ctx.t('pick_region'), PickRegion.labels(ctx), inp)
        if action == 'item':
            ctx.data['region'] = REGIONS[index][0]
            return ctx.goto('pick_county')
        if action == 'more':
            return ctx.goto('pick_region')
        if action == 'back':
            return ctx.goto(LOCATION_BACK.get(ctx.data.get('loc_purpose'), 'main'))
        return ctx.invalid()


@screen('pick_county')
class PickCounty:
    @staticmethod
    def render(ctx):
        return render_list(ctx, 'county', ctx.t('pick_county'),
                           region_counties(ctx.data.get('region')))

    @staticmethod
    def handle(ctx, inp):
        counties = region_counties(ctx.data.get('region'))
        action, index = pick(ctx, 'county', ctx.t('pick_county'), counties, inp)
        if action == 'item':
            return finish_location(ctx, counties[index])
        if action == 'more':
            return ctx.goto('pick_county')
        if action == 'back':
            return ctx.goto('pick_region')
        return ctx.invalid()


def finish_location(ctx, county):
    purpose = ctx.data.pop('loc_purpose', None)
    if purpose == 'reg':
        patient = Patient.query.filter_by(phone=ctx.phone).first()
        if patient is None:
            patient = Patient(phone=ctx.phone, name=ctx.data.pop('reg_name'),
                              age=ctx.data.pop('reg_age', None),
                              gender=ctx.data.pop('reg_gender', None),
                              county=county, language=ctx.lang)
            db.session.add(patient)
            db.session.commit()
        ctx.patient = patient
        return ctx.goto(ctx.data.pop('after_reg', 'main'),
                        notice=ctx.t('registered', name=patient.first_name))
    if purpose == 'sx':
        return save_report(ctx, county)
    if purpose == 'alerts':
        ctx.data['alert_county'] = county
        return ctx.goto('alerts')
    if purpose == 'account' and ctx.patient:
        ctx.patient.county = county
        db.session.commit()
        return ctx.goto('account', notice=ctx.t('account_updated'))
    return ctx.goto('main')


# ---------------------------------------------------------------------------
# Booking a specialist
# ---------------------------------------------------------------------------

def specialty_label(code, lang):
    return SPECIALTY_LABELS.get(code, {}).get(lang, code)


@screen('bk_specialty')
class BookSpecialty:
    @staticmethod
    def labels(ctx):
        return [labels[ctx.lang] for _, _, labels in SPECIALTIES]

    @staticmethod
    def render(ctx):
        return render_list(ctx, 'spec', ctx.t('bk_specialty'), BookSpecialty.labels(ctx))

    @staticmethod
    def handle(ctx, inp):
        action, index = pick(ctx, 'spec', ctx.t('bk_specialty'), BookSpecialty.labels(ctx), inp)
        if action == 'item':
            ctx.data['specialty'] = SPECIALTIES[index][0]
            return ctx.goto('bk_complaint')
        if action == 'more':
            return ctx.goto('bk_specialty')
        if action == 'back':
            return ctx.goto('main')
        return ctx.invalid()


@screen('bk_complaint')
class BookComplaint:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('bk_complaint'))

    @staticmethod
    def handle(ctx, inp):
        if inp == '0':
            return ctx.goto('bk_specialty')
        text = ' '.join(inp.split())
        if len(text) < 3:
            return ctx.invalid()
        ctx.data['complaint'] = text[:200]
        return ctx.goto('bk_mode')


@screen('bk_mode')
class BookMode:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('bk_mode'))

    @staticmethod
    def handle(ctx, inp):
        if inp == '0':
            return ctx.goto('bk_complaint')
        mode = {'1': 'phone', '2': 'in_person'}.get(inp)
        if not mode:
            return ctx.invalid()
        ctx.data['mode'] = mode
        specialists = bookable_specialists(ctx.data['specialty'], mode, ctx.patient.county)
        if not specialists:
            return waitlist(ctx)
        ctx.data['specialist_ids'] = [s.id for s in specialists[:24]]
        return ctx.goto('bk_specialist')


def waitlist(ctx):
    """No specialist available: record the unmet need and promise an SMS."""
    consultation = Consultation(patient=ctx.patient, specialty=ctx.data['specialty'],
                                mode=ctx.data['mode'], status='waitlist',
                                complaint=ctx.data.get('complaint'), county=ctx.patient.county)
    db.session.add(consultation)
    db.session.commit()
    label = specialty_label(consultation.specialty, ctx.lang)
    send_sms(ctx.phone, ctx.t('sms_waitlist', ref=consultation.reference, specialty=label),
             purpose='waitlist')
    return ctx.end(ctx.t('bk_waitlist', specialty=label, ref=consultation.reference))


def _specialists_in_session(ctx):
    found = {s.id: s for s in Specialist.query.filter(
        Specialist.id.in_(ctx.data.get('specialist_ids', []))).all()}
    return [found[i] for i in ctx.data.get('specialist_ids', []) if i in found]


@screen('bk_specialist')
class BookSpecialist:
    @staticmethod
    def labels(specialists):
        return [f'{s.short_name}, {s.county}, KES{s.fee_kes}' for s in specialists]

    @staticmethod
    def render(ctx):
        return render_list(ctx, 'sp', ctx.t('bk_specialist'),
                           BookSpecialist.labels(_specialists_in_session(ctx)))

    @staticmethod
    def handle(ctx, inp):
        specialists = _specialists_in_session(ctx)
        action, index = pick(ctx, 'sp', ctx.t('bk_specialist'),
                             BookSpecialist.labels(specialists), inp)
        if action == 'item':
            ctx.data['specialist_id'] = specialists[index].id
            return ctx.goto('bk_slot')
        if action == 'more':
            return ctx.goto('bk_specialist')
        if action == 'back':
            return ctx.goto('bk_mode')
        return ctx.invalid()


@screen('bk_slot')
class BookSlot:
    @staticmethod
    def render(ctx):
        specialist = db.session.get(Specialist, ctx.data.get('specialist_id'))
        slots = available_slots(specialist, limit=6) if specialist else []
        ctx.data['slots'] = [s.isoformat() for s in slots]
        if not slots:
            return ctx.con(ctx.t('bk_no_slots'))
        return render_list(ctx, 'slot', ctx.t('bk_slot'), [format_when(s, ctx.lang) for s in slots])

    @staticmethod
    def handle(ctx, inp):
        slots = [datetime.fromisoformat(s) for s in ctx.data.get('slots', [])]
        if not slots:
            return ctx.goto('bk_specialist') if inp == '0' else ctx.invalid()
        action, index = pick(ctx, 'slot', ctx.t('bk_slot'),
                             [format_when(s, ctx.lang) for s in slots], inp)
        if action == 'item':
            ctx.data['slot'] = slots[index].isoformat()
            return ctx.goto('bk_confirm')
        if action == 'back':
            return ctx.goto('bk_specialist')
        return ctx.invalid()


@screen('bk_confirm')
class BookConfirm:
    @staticmethod
    def render(ctx):
        specialist = db.session.get(Specialist, ctx.data['specialist_id'])
        when = datetime.fromisoformat(ctx.data['slot'])
        return ctx.con(ctx.t('bk_confirm', doctor=specialist.short_name,
                             specialty=specialty_label(specialist.specialty, ctx.lang),
                             when=format_when(when, ctx.lang),
                             mode=ctx.t('mode_' + ctx.data['mode']), fee=specialist.fee_kes))

    @staticmethod
    def handle(ctx, inp):
        if inp == '2':
            return ctx.end(ctx.t('bk_cancelled'))
        if inp == '0':
            return ctx.goto('bk_slot')
        if inp != '1':
            return ctx.invalid()

        specialist = db.session.get(Specialist, ctx.data['specialist_id'])
        when = datetime.fromisoformat(ctx.data['slot'])
        if not specialist or not specialist.is_bookable or not is_slot_free(specialist, when):
            return ctx.goto('bk_slot', notice=ctx.t('bk_taken'))

        consultation = Consultation(patient=ctx.patient, specialist=specialist,
                                    specialty=specialist.specialty, mode=ctx.data['mode'],
                                    scheduled_at=when, status='booked',
                                    complaint=ctx.data.get('complaint'),
                                    county=ctx.patient.county, fee_kes=specialist.fee_kes)
        db.session.add(consultation)
        db.session.commit()
        notify_booking(consultation, ctx.lang, ctx.ussd_code)

        values = dict(ref=consultation.reference, doctor=specialist.short_name,
                      when=format_when(when, ctx.lang), fee=specialist.fee_kes,
                      place=specialist.facility or specialist.county)
        key = 'bk_done_phone' if consultation.mode == 'phone' else 'bk_done_visit'
        return ctx.end(ctx.t(key, **values))


def notify_booking(consultation, lang, ussd_code):
    specialist = consultation.specialist
    patient = consultation.patient
    values = dict(ref=consultation.reference, doctor=specialist.short_name,
                  specialty=specialty_label(consultation.specialty, lang),
                  when=format_when(consultation.scheduled_at, lang), fee=consultation.fee_kes,
                  place=specialist.facility or specialist.county, code=ussd_code)
    key = 'sms_booked_phone' if consultation.mode == 'phone' else 'sms_booked_visit'
    send_sms(patient.phone, t(key, lang, **values), purpose='booking', commit=False)
    if specialist.user.phone:
        details = ', '.join(str(x) for x in (patient.age, patient.gender, patient.county) if x)
        send_sms(specialist.user.phone,
                 f'Tujali: new {consultation.mode_label.lower()} booking {consultation.reference} '
                 f"{consultation.scheduled_at.strftime('%a %d %b %H:%M')}. {patient.name} ({details}): "
                 f'{consultation.complaint or "no details"}',
                 purpose='booking_specialist', commit=False)
    db.session.commit()


# ---------------------------------------------------------------------------
# My appointments
# ---------------------------------------------------------------------------

def _patient_consultations(ctx):
    cutoff = now() - timedelta(days=60)
    items = []
    for c in ctx.patient.consultations:
        if c.status == 'booked' and c.scheduled_at and c.scheduled_at >= now() - timedelta(hours=1):
            items.append(c)
        elif c.status == 'waitlist':
            items.append(c)
        elif c.status == 'completed' and c.advice and (c.completed_at or c.created_at) >= cutoff:
            items.append(c)
    order = {'booked': 0, 'waitlist': 1, 'completed': 2}
    items.sort(key=lambda c: (order[c.status], c.scheduled_at or c.created_at))
    return items[:12]


def _consultation_label(c, lang):
    label = specialty_label(c.specialty, lang)
    if c.status == 'booked':
        return f'{format_when(c.scheduled_at, lang)} {label}'
    if c.status == 'waitlist':
        return f"{t('label_waiting', lang)}: {label}"
    return f"{t('label_advice', lang)}: {label}"


@screen('appts')
class Appointments:
    @staticmethod
    def render(ctx):
        items = _patient_consultations(ctx)
        ctx.data['appt_ids'] = [c.id for c in items]
        if not items:
            return ctx.con(ctx.t('appts_none'))
        return render_list(ctx, 'appt', ctx.t('appts'),
                           [_consultation_label(c, ctx.lang) for c in items])

    @staticmethod
    def handle(ctx, inp):
        ids = ctx.data.get('appt_ids', [])
        if not ids:
            if inp == '1':
                return ctx.goto('bk_specialty')
            return ctx.goto('main') if inp == '0' else ctx.invalid()
        items = [c for c in (db.session.get(Consultation, i) for i in ids) if c]
        action, index = pick(ctx, 'appt', ctx.t('appts'),
                             [_consultation_label(c, ctx.lang) for c in items], inp)
        if action == 'item':
            ctx.data['consult_id'] = items[index].id
            return ctx.goto('appt_detail')
        if action == 'more':
            return ctx.goto('appts')
        if action == 'back':
            return ctx.goto('main')
        return ctx.invalid()


def _own_consultation(ctx):
    consultation = db.session.get(Consultation, ctx.data.get('consult_id'))
    if consultation is None or consultation.patient_id != ctx.patient.id:
        return None
    return consultation


@screen('appt_detail')
class AppointmentDetail:
    @staticmethod
    def render(ctx):
        c = _own_consultation(ctx)
        if c is None:
            return ctx.goto('appts')
        label = specialty_label(c.specialty, ctx.lang)
        if c.status == 'waitlist':
            return ctx.con(ctx.t('appt_waitlist', ref=c.reference, specialty=label))
        doctor = c.specialist.short_name if c.specialist else ''
        if c.status == 'completed':
            advice = c.advice or ''
            if len(advice) > 70:
                advice = advice[:67].rstrip() + '...'
            return ctx.con(ctx.t('appt_advice', doctor=doctor, advice=advice))
        return ctx.con(ctx.t('appt_booked', ref=c.reference, doctor=doctor, specialty=label,
                             when=format_when(c.scheduled_at, ctx.lang),
                             mode=ctx.t('mode_' + c.mode)))

    @staticmethod
    def handle(ctx, inp):
        c = _own_consultation(ctx)
        if c is None or inp == '0':
            return ctx.goto('appts')
        if c.status in ('booked', 'waitlist') and inp == '1':
            return ctx.goto('appt_cancel')
        if c.status == 'completed' and inp == '1':
            send_sms(ctx.phone, ctx.t('sms_advice', doctor=c.specialist.short_name,
                                      ref=c.reference, advice=c.advice), purpose='advice')
            return ctx.end(ctx.t('advice_sent'))
        if c.status == 'completed' and inp == '2':
            return start_follow_up(ctx, c)
        return ctx.invalid()


def start_follow_up(ctx, consultation):
    ctx.data.update({'specialty': consultation.specialty, 'mode': consultation.mode,
                     'complaint': f'Follow-up {consultation.reference}: {consultation.complaint or ""}'[:200]})
    specialist = consultation.specialist
    if specialist and specialist.is_bookable:
        ctx.data['specialist_ids'] = [specialist.id]
        ctx.data['specialist_id'] = specialist.id
        return ctx.goto('bk_slot')
    return ctx.goto('bk_mode')


@screen('appt_cancel')
class AppointmentCancel:
    @staticmethod
    def render(ctx):
        c = _own_consultation(ctx)
        return ctx.con(ctx.t('appt_cancel_confirm', ref=c.reference)) if c else ctx.goto('appts')

    @staticmethod
    def handle(ctx, inp):
        c = _own_consultation(ctx)
        if c is None:
            return ctx.goto('appts')
        if inp == '2' or inp == '0':
            return ctx.goto('appt_detail')
        if inp != '1':
            return ctx.invalid()
        was_booked = c.status == 'booked'
        c.status = 'cancelled'
        c.cancelled_by = 'patient'
        if was_booked and c.specialist and c.specialist.user.phone:
            send_sms(c.specialist.user.phone,
                     f'Tujali: {c.reference} on {c.scheduled_at.strftime("%a %d %b %H:%M")} '
                     f'was cancelled by the patient.', purpose='cancellation_specialist', commit=False)
        send_sms(ctx.phone, ctx.t('sms_cancelled', ref=c.reference), purpose='cancellation',
                 commit=False)
        db.session.commit()
        return ctx.end(ctx.t('appt_cancelled', ref=c.reference))


# ---------------------------------------------------------------------------
# Illness reporting (outbreak surveillance)
# ---------------------------------------------------------------------------

@screen('sx_group')
class SymptomGroup:
    @staticmethod
    def labels(ctx):
        return [labels[ctx.lang] for _, labels, _ in SYNDROMES]

    @staticmethod
    def render(ctx):
        return render_list(ctx, 'sx', ctx.t('sx_group'), SymptomGroup.labels(ctx))

    @staticmethod
    def handle(ctx, inp):
        action, index = pick(ctx, 'sx', ctx.t('sx_group'), SymptomGroup.labels(ctx), inp)
        if action == 'item':
            ctx.data['syndrome'] = SYNDROMES[index][0]
            return ctx.goto('sx_people')
        if action == 'more':
            return ctx.goto('sx_group')
        if action == 'back':
            return ctx.goto('main')
        return ctx.invalid()


@screen('sx_people')
class SymptomPeople:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('sx_people'))

    @staticmethod
    def handle(ctx, inp):
        if inp == '0':
            return ctx.goto('sx_group')
        people = dict(HOUSEHOLD_SIZES).get(inp)
        if not people:
            return ctx.invalid()
        ctx.data['people'] = people
        return ctx.goto('sx_danger')


@screen('sx_danger')
class SymptomDanger:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('sx_danger'))

    @staticmethod
    def handle(ctx, inp):
        if inp == '0':
            return ctx.goto('sx_people')
        if inp not in ('1', '2'):
            return ctx.invalid()
        ctx.data['danger'] = inp == '1'
        if ctx.patient and ctx.patient.county:
            return save_report(ctx, ctx.patient.county)
        ctx.data['loc_purpose'] = 'sx'
        return ctx.goto('pick_region')


def reporter_hash(phone):
    """Pseudonymous reporter ID: lets us limit repeat reports without storing the number."""
    secret = current_app.config['SECRET_KEY']
    return hashlib.sha256(f'{secret}:{phone}'.encode()).hexdigest()


def save_report(ctx, county):
    syndrome = ctx.data['syndrome']
    danger = bool(ctx.data.get('danger'))
    reporter = reporter_hash(ctx.phone)
    since = now() - timedelta(days=1)
    recent = SymptomReport.query.filter(SymptomReport.reporter_hash == reporter,
                                        SymptomReport.syndrome == syndrome,
                                        SymptomReport.created_at >= since).count()
    if recent < MAX_REPORTS_PER_DAY:
        db.session.add(SymptomReport(patient_id=ctx.patient.id if ctx.patient else None,
                                     reporter_hash=reporter, county=county, syndrome=syndrome,
                                     people_affected=ctx.data.get('people', 1),
                                     danger_signs=danger))
        db.session.commit()

    if danger or syndrome in URGENT_SYNDROMES:
        return ctx.end(ctx.t('sx_urgent'))
    advice = SYNDROME_ADVICE.get(syndrome, SYNDROME_ADVICE['other'])[ctx.lang]
    return ctx.end(ctx.t('sx_thanks', advice=advice))


# ---------------------------------------------------------------------------
# Health alerts
# ---------------------------------------------------------------------------

def _alert_county(ctx):
    return ctx.data.get('alert_county') or (ctx.patient.county if ctx.patient else None)


@screen('alerts')
class Alerts:
    @staticmethod
    def labels(alerts):
        return [('! ' if a.level == 'emergency' else '') + a.title for a in alerts]

    @staticmethod
    def render(ctx):
        county = _alert_county(ctx)
        if not county:
            ctx.data['loc_purpose'] = 'alerts'
            return ctx.goto('pick_region')
        alerts = HealthAlert.live_for_county(county)[:16]
        ctx.data['alert_ids'] = [a.id for a in alerts]
        if not alerts:
            return ctx.con(ctx.t('alerts_none', county=county))
        return render_list(ctx, 'alert', ctx.t('alerts', county=county), Alerts.labels(alerts))

    @staticmethod
    def handle(ctx, inp):
        ids = ctx.data.get('alert_ids', [])
        alerts = [a for a in (db.session.get(HealthAlert, i) for i in ids) if a]
        if not alerts:
            return ctx.goto('main') if inp == '0' else ctx.invalid()
        action, index = pick(ctx, 'alert', ctx.t('alerts', county=_alert_county(ctx)),
                             Alerts.labels(alerts), inp)
        if action == 'item':
            ctx.data['alert_id'] = alerts[index].id
            return ctx.goto('alert_detail')
        if action == 'more':
            return ctx.goto('alerts')
        if action == 'back':
            return ctx.goto('main')
        return ctx.invalid()


@screen('alert_detail')
class AlertDetail:
    @staticmethod
    def render(ctx):
        alert = db.session.get(HealthAlert, ctx.data.get('alert_id'))
        if alert is None:
            return ctx.goto('alerts')
        body = f'{alert.title}\n{alert.message(ctx.lang)}'
        limit = MAX_SCREEN - len(ctx.t('back')) - 1
        if len(body) > limit:
            body = body[:limit - 3].rstrip() + '...'
        return ctx.con(f"{body}\n{ctx.t('back')}")

    @staticmethod
    def handle(ctx, inp):
        return ctx.goto('alerts') if inp == '0' else ctx.invalid()


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------

@screen('account')
class Account:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('account'))

    @staticmethod
    def handle(ctx, inp):
        if inp == '0':
            return ctx.goto('main')
        if inp == '1':
            return ctx.goto('account_lang')
        if inp == '2':
            ctx.data['loc_purpose'] = 'account'
            return ctx.goto('pick_region')
        if inp == '3':
            return ctx.goto('account_details')
        if inp == '4':
            return ctx.goto('account_delete')
        return ctx.invalid()


@screen('account_lang')
class AccountLanguage:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('account_lang'))

    @staticmethod
    def handle(ctx, inp):
        if inp not in ('1', '2'):
            return ctx.goto('account') if inp == '0' else ctx.invalid()
        ctx.lang = 'en' if inp == '1' else 'sw'
        ctx.patient.language = ctx.lang
        db.session.commit()
        return ctx.goto('account', notice=ctx.t('account_updated'))


@screen('account_details')
class AccountDetails:
    @staticmethod
    def render(ctx):
        p = ctx.patient
        return ctx.con(ctx.t('account_details', name=p.name, age=p.age or '-',
                             county=p.county or '-', phone=p.phone))

    @staticmethod
    def handle(ctx, inp):
        return ctx.goto('account') if inp == '0' else ctx.invalid()


@screen('account_delete')
class AccountDelete:
    @staticmethod
    def render(ctx):
        return ctx.con(ctx.t('account_delete'))

    @staticmethod
    def handle(ctx, inp):
        if inp in ('2', '0'):
            return ctx.goto('account')
        if inp != '1':
            return ctx.invalid()
        delete_patient_data(ctx.patient)
        return ctx.end(ctx.t('account_deleted'))


def delete_patient_data(patient):
    """Anonymise a patient. Consultation records stay (with no personal details)
    so specialists' histories and service statistics remain consistent."""
    for c in patient.consultations:
        if c.status in ('booked', 'waitlist'):
            c.status = 'cancelled'
            c.cancelled_by = 'patient'
        c.complaint = None
    for report in SymptomReport.query.filter_by(patient_id=patient.id):
        report.patient_id = None
    patient.name = 'Deleted user'
    patient.phone = f'deleted-{patient.id}'
    patient.age = None
    patient.gender = None
    db.session.commit()

"""Specialist matching and appointment slots."""
from datetime import datetime, timedelta

from models import db, Specialist, Consultation, User
from reference import COUNTY_REGION

LEAD_TIME = timedelta(hours=1)  # earliest bookable slot from now


def bookable_specialists(specialty, mode, county=None):
    """Verified specialists accepting `mode` bookings, nearest first.

    In-person visits are ordered by county, then region. Phone consultations
    can be with anyone in the country, so they are ordered by how soon the
    specialist is free.
    """
    query = (Specialist.query.join(User)
             .filter(Specialist.specialty == specialty,
                     Specialist.verified.is_(True),
                     Specialist.accepting.is_(True),
                     User.is_active_account.is_(True)))
    query = query.filter(Specialist.offers_phone.is_(True) if mode == 'phone'
                         else Specialist.offers_in_person.is_(True))
    specialists = [s for s in query.all() if s.availability]

    region = COUNTY_REGION.get(county)

    def distance_rank(s):
        if county and s.county == county:
            return 0
        if region and COUNTY_REGION.get(s.county) == region:
            return 1
        return 2

    if mode == 'in_person':
        specialists.sort(key=lambda s: (distance_rank(s), s.fee_kes))
    else:
        far_future = datetime.max
        specialists.sort(key=lambda s: (next_slot(s) or far_future, s.fee_kes))
    return specialists


def _booked_times(specialist, start, end):
    rows = (db.session.query(Consultation.scheduled_at)
            .filter(Consultation.specialist_id == specialist.id,
                    Consultation.status == 'booked',
                    Consultation.scheduled_at >= start,
                    Consultation.scheduled_at <= end).all())
    return {row[0] for row in rows}


def available_slots(specialist, start=None, days=7, limit=5):
    """Next free slots (datetimes) from the specialist's weekly hours."""
    start = start or datetime.now()
    earliest = start + LEAD_TIME
    end = start + timedelta(days=days + 1)
    booked = _booked_times(specialist, start, end)

    slots = []
    for offset in range(days + 1):
        day = (start + timedelta(days=offset)).date()
        for block in specialist.availability:
            if block.weekday != day.weekday():
                continue
            slot = datetime.combine(day, block.start_time)
            block_end = datetime.combine(day, block.end_time)
            step = timedelta(minutes=block.slot_minutes or 20)
            while slot + step <= block_end:
                if slot >= earliest and slot not in booked:
                    slots.append(slot)
                slot += step
        if len(slots) >= limit:
            break
    return sorted(slots)[:limit]


def next_slot(specialist):
    slots = available_slots(specialist, limit=1)
    return slots[0] if slots else None


def is_slot_free(specialist, when):
    if when < datetime.now():
        return False
    return when in available_slots(specialist, start=when - LEAD_TIME - timedelta(minutes=1),
                                   days=1, limit=200)

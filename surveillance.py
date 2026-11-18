"""Outbreak early warning from community symptom reports.

A signal is raised for a county + syndrome when this week's cases are well
above that county's own recent baseline, or when a red-flag syndrome
(e.g. unusual bleeding, stiff neck) is reported at all. The thresholds are
deliberately simple and explainable so a county health officer can verify
them by hand; tune them with WINDOW_DAYS / BASELINE_WEEKS / the rules below.
"""
from collections import defaultdict
from datetime import datetime, timedelta

from models import SymptomReport
from reference import SYNDROME_LABELS, SYNDROME_WATCH, URGENT_SYNDROMES, SYNDROMES

WINDOW_DAYS = 7
BASELINE_WEEKS = 3

LEVEL_ORDER = {'high': 0, 'medium': 1}


def detect_signals(at=None):
    at = at or datetime.now()
    window_start = at - timedelta(days=WINDOW_DAYS)
    baseline_start = window_start - timedelta(weeks=BASELINE_WEEKS)

    reports = SymptomReport.query.filter(SymptomReport.created_at >= baseline_start,
                                         SymptomReport.created_at <= at).all()
    current = defaultdict(lambda: {'reports': 0, 'cases': 0, 'danger': 0})
    baseline = defaultdict(int)
    for r in reports:
        key = (r.county, r.syndrome)
        if r.created_at >= window_start:
            current[key]['reports'] += 1
            current[key]['cases'] += r.people_affected
            current[key]['danger'] += int(r.danger_signs)
        else:
            baseline[key] += r.people_affected

    signals = []
    for (county, syndrome), stats in current.items():
        weekly_baseline = baseline[(county, syndrome)] / BASELINE_WEEKS
        ratio = stats['cases'] / max(weekly_baseline, 1)
        rise = (f'{ratio:.1f}x the usual weekly level' if weekly_baseline >= 1
                else f"{stats['cases']} cases where there are usually almost none")
        level = reason = None

        if syndrome in URGENT_SYNDROMES:
            level = 'high'
            reason = 'Red-flag syndrome reported'
        elif stats['cases'] >= 8 and ratio >= 3:
            level = 'high'
            reason = rise
        elif stats['cases'] >= 4 and ratio >= 2:
            level = 'medium'
            reason = rise
        elif stats['danger'] >= 3:
            level = 'medium'
            reason = f"{stats['danger']} reports with danger signs"

        if level:
            signals.append({
                'county': county,
                'syndrome': syndrome,
                'syndrome_label': SYNDROME_LABELS[syndrome]['en'],
                'watch_for': SYNDROME_WATCH.get(syndrome, ''),
                'level': level,
                'reason': reason,
                'reports': stats['reports'],
                'cases': stats['cases'],
                'danger': stats['danger'],
                'baseline': round(weekly_baseline, 1),
                'ratio': round(ratio, 1),
            })

    signals.sort(key=lambda s: (LEVEL_ORDER[s['level']], -s['ratio'], -s['cases']))
    return signals


def overview(days=30, county=None, syndrome=None, at=None):
    """Numbers and series for the surveillance dashboard."""
    at = at or datetime.now()
    start = (at - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    previous_start = start - timedelta(days=days)

    query = SymptomReport.query.filter(SymptomReport.created_at >= previous_start,
                                       SymptomReport.created_at <= at)
    if county:
        query = query.filter(SymptomReport.county == county)
    if syndrome:
        query = query.filter(SymptomReport.syndrome == syndrome)
    rows = query.order_by(SymptomReport.created_at).all()

    in_range = [r for r in rows if r.created_at >= start]
    previous = [r for r in rows if r.created_at < start]

    labels = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
    index = {label: i for i, label in enumerate(labels)}
    series = {code: [0] * days for code, _, _ in SYNDROMES}
    by_county = defaultdict(lambda: defaultdict(int))
    by_syndrome = defaultdict(int)
    for r in in_range:
        day = r.created_at.strftime('%Y-%m-%d')
        if day in index:
            series[r.syndrome][index[day]] += r.people_affected
        by_county[r.county][r.syndrome] += r.people_affected
        by_county[r.county]['_total'] += r.people_affected
        by_syndrome[r.syndrome] += r.people_affected

    cases = sum(r.people_affected for r in in_range)
    previous_cases = sum(r.people_affected for r in previous)
    change = None
    if previous_cases:
        change = round((cases - previous_cases) / previous_cases * 100)

    county_rows = sorted(({'county': c, **dict(v)} for c, v in by_county.items()),
                         key=lambda row: -row['_total'])
    return {
        'days': days,
        'reports': len(in_range),
        'cases': cases,
        'change_pct': change,
        'danger_reports': sum(1 for r in in_range if r.danger_signs),
        'counties_reporting': len(by_county),
        'labels': labels,
        'series': {k: v for k, v in series.items() if any(v)},
        'by_syndrome': dict(by_syndrome),
        'county_rows': county_rows,
        'heat_max': max([v for row in county_rows for k, v in row.items()
                         if k not in ('county', '_total')] or [0]),
        'recent': list(reversed(in_range[-15:])),
    }

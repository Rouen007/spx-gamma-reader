#!/usr/bin/env python3
"""Offline evidence contract checks and append-only JSONL storage; no signals."""
import argparse
from datetime import date, datetime, timedelta
import fcntl
import json
import math
from pathlib import Path
import sys
from zoneinfo import ZoneInfo


def timestamp(value, label, errors, required=True):
    if value is None and not required:
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            raise ValueError('timezone required')
        return dt
    except (ValueError, TypeError, AttributeError):
        errors.append(f'{label}: timezone-aware ISO timestamp required')
        return None


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate(record):
    errors, warnings = [], []
    if not isinstance(record, dict):
        return ['record must be an object'], warnings
    if not isinstance(record.get('record_id'), str) or not record['record_id'].strip():
        errors.append('record_id required')
    mode = record.get('mode')
    if mode not in ('observation', 'decision'):
        errors.append('mode must be observation or decision')
    cutoff = timestamp(record.get('decision_at'), 'decision_at', errors)
    items = record.get('evidence')
    if not isinstance(items, list) or not items:
        return errors + ['nonempty evidence list required'], warnings
    indexed = {}
    times = {}
    for e in items:
        if not isinstance(e, dict) or not isinstance(e.get('id'), str) or not e['id']:
            errors.append('each evidence needs an id')
            continue
        eid = e['id']
        if eid in indexed:
            errors.append(f'duplicate evidence id: {eid}')
        indexed[eid] = e
        for field in ('instrument', 'source', 'chart_type'):
            if not isinstance(e.get(field), str) or not e[field].strip():
                errors.append(f'{eid}: {field} required')
        if e.get('instrument') == 'ES' and not e.get('contract'):
            errors.append(f'{eid}: ES contract required; use unknown if unavailable')
        times[eid] = timestamp(e.get('evidence_at'), f'{eid}.evidence_at', errors, required=False)
        received = timestamp(e.get('received_at'), f'{eid}.received_at', errors, required=False)
        if times[eid] and received and received < times[eid]:
            errors.append(f'{eid}: received_at precedes evidence_at')
        if times[eid] and cutoff and times[eid] > cutoff:
            errors.append(f'{eid}: evidence is later than decision_at')
    used = record.get('used_evidence_ids')
    if not isinstance(used, list) or not used or any(not isinstance(x, str) for x in used):
        return errors + ['nonempty used_evidence_ids list required'], warnings
    if len(set(used)) != len(used):
        errors.append('duplicate used_evidence_ids')
    for eid in used:
        if eid not in indexed:
            errors.append(f'unknown evidence reference: {eid}')
            continue
        e, dt = indexed[eid], times[eid]
        if dt is None:
            (errors if mode == 'decision' else warnings).append(f'{eid}: evidence time unknown')
        if mode == 'decision':
            if e.get('instrument') == 'ES' and e.get('contract') == 'unknown':
                errors.append(f'{eid}: decision requires known ES contract')
            try:
                session = date.fromisoformat(e.get('session_date'))
                if dt and e.get('instrument') in ('SPX', 'ES'):
                    local = dt.astimezone(ZoneInfo('America/New_York'))
                    overnight = (e.get('instrument') == 'ES' and local.hour >= 18
                                 and local.date() + timedelta(days=1) == session)
                    if local.date() != session and not overnight:
                        errors.append(f'{eid}: evidence time contradicts session_date')
                if e.get('instrument') in ('SPX', 'ES') and cutoff:
                    # This is an equity-session key, not the overnight futures calendar date.
                    if session != cutoff.astimezone(ZoneInfo('America/New_York')).date():
                        errors.append(f'{eid}: decision session differs from cutoff ET date')
            except (TypeError, ValueError):
                errors.append(f'{eid}: valid session_date required for decision')
            received = timestamp(e.get('received_at'), f'{eid}.received_at', errors)
            if cutoff and received and received > cutoff:
                errors.append(f'{eid}: evidence not received by decision time')
    alignment = record.get('cross_instrument_alignment')
    if alignment not in ('separate', 'basis'):
        errors.append('cross_instrument_alignment must be separate or basis')
    if alignment == 'basis':
        b = record.get('basis')
        if not isinstance(b, dict):
            errors.append('basis object required')
        else:
            spot_at = timestamp(b.get('spot_at'), 'basis.spot_at', errors)
            futures_at = timestamp(b.get('futures_at'), 'basis.futures_at', errors)
            skew = record.get('basis_max_skew_seconds')
            age = record.get('basis_max_age_seconds')
            if not number(age) or age < 0:
                errors.append('explicit nonnegative basis_max_age_seconds required')
            elif cutoff:
                for dt in (spot_at, futures_at):
                    if dt and (cutoff - dt).total_seconds() > age:
                        errors.append('basis quote older than declared age')
            if not number(skew) or skew < 0:
                errors.append('explicit nonnegative basis_max_skew_seconds required')
            elif spot_at and futures_at and abs((spot_at - futures_at).total_seconds()) > skew:
                errors.append('basis quote times exceed declared skew')
            for dt in (spot_at, futures_at):
                if cutoff and dt and dt > cutoff:
                    errors.append('basis quote later than decision')
            if not b.get('source') or not b.get('contract') or b.get('contract') == 'unknown':
                errors.append('basis source and known contract required')
            if all(number(b.get(k)) for k in ('spot', 'futures', 'value')):
                if not math.isclose(b['futures'] - b['spot'], b['value'], abs_tol=1e-6):
                    errors.append('basis value must equal futures minus spot')
            else:
                errors.append('finite spot, futures and basis value required')
            used_instruments = {indexed[x].get('instrument') for x in used if x in indexed}
            if not {'SPX', 'ES'} <= used_instruments:
                errors.append('basis alignment requires SPX and ES evidence')
            for eid in used:
                if eid in indexed and indexed[eid].get('instrument') == 'ES':
                    if indexed[eid].get('contract') != b.get('contract'):
                        errors.append(f'{eid}: basis contract mismatch')
    comparisons = record.get('cvd_comparisons', [])
    if not isinstance(comparisons, list):
        errors.append('cvd_comparisons must be a list')
    else:
        for pair in comparisons:
            if not isinstance(pair, list) or len(pair) != 2 or any(x not in used for x in pair):
                errors.append('CVD pair must reference two used evidence ids')
                continue
            a, b = (indexed.get(x, {}) for x in pair)
            sa = a.get('settings', {}).get('cvd') if isinstance(a.get('settings'), dict) else None
            sb = b.get('settings', {}).get('cvd') if isinstance(b.get('settings'), dict) else None
            fields = ('range', 'start_at', 'min_size', 'max_size', 'reset')
            if not all(isinstance(s, dict) and all(k in s for k in fields) for s in (sa, sb)):
                errors.append('CVD comparison requires complete known settings')
            elif sa != sb or any(sa[k] in (None, 'unknown') for k in fields):
                errors.append('CVD comparison settings differ or are unknown')
            else:
                if sa['range'] not in ('session', 'chart'):
                    errors.append('CVD range must be session or chart')
                if sa['reset'] not in ('none', 'manual', 'scheduled'):
                    errors.append('CVD reset must be none, manual or scheduled')
                minimum, maximum = sa['min_size'], sa['max_size']
                if not number(minimum) or minimum < 0:
                    errors.append('CVD min_size must be nonnegative')
                if maximum != 'all' and (not number(maximum) or not number(minimum) or maximum < minimum):
                    errors.append('CVD max_size must be all or at least min_size')
                start = timestamp(sa['start_at'], 'CVD start_at', errors)
                for eid in pair:
                    if start and times.get(eid) and start > times[eid]:
                        errors.append('CVD start_at later than evidence')
            if (a.get('instrument'), a.get('contract')) != (b.get('instrument'), b.get('contract')):
                errors.append('CVD comparison instrument/contract mismatch')
            if not all(times.get(x) for x in pair):
                errors.append('CVD comparison requires evidence timestamps')
            elif times[pair[0]] >= times[pair[1]]:
                errors.append('CVD comparison must run from earlier to later evidence')
    if not isinstance(record.get('hypothesis'), dict):
        errors.append('hypothesis object required')
    elif not record['hypothesis']:
        warnings.append('empty hypothesis; validation does not confirm an actionable setup')
    return errors, warnings


def append_record(path, record):
    errors, _ = validate(record)
    if errors:
        raise ValueError('; '.join(errors))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+', encoding='utf-8') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        ids = set()
        for line in f:
            old = json.loads(line)
            ids.add(old['record_id'])
        if record['record_id'] in ids:
            raise ValueError('record_id already exists')
        if record.get('supersedes') and record['supersedes'] not in ids:
            raise ValueError('supersedes must reference an existing record')
        if record.get('supersedes') and not record.get('correction_reason'):
            raise ValueError('correction_reason required')
        f.seek(0, 2)
        if f.tell():
            f.seek(f.tell() - 1)
            if f.read(1) != '\n':
                raise ValueError('ledger lacks final newline; do not append to damaged ledger')
        f.seek(0, 2)
        f.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
        f.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'append'))
    parser.add_argument('record', type=Path)
    parser.add_argument('--ledger', type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding='utf-8'))
        errors, warnings = validate(record)
        if errors:
            print(json.dumps({'ok': False, 'errors': errors, 'warnings': warnings}, ensure_ascii=False))
            return 1
        if args.action == 'append':
            if not args.ledger:
                parser.error('append requires --ledger')
            append_record(args.ledger, record)
        print(json.dumps({'ok': True, 'warnings': warnings}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'ok': False, 'errors': [str(exc)]}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Extract DOSM CSVs, validate, transform, and write the static dashboard data."""
import csv
import io
import json
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = 'https://storage.dosm.gov.my/hies/'
NAMES = ('hh_income', 'hh_income_state', 'hh_income_district', 'hies_state_percentile')
REQUIRED = {
    'hh_income': {'date', 'income_median', 'income_mean'},
    'hh_income_state': {'date', 'state', 'income_median', 'income_mean'},
    'hh_income_district': {'date', 'state', 'district', 'income_median', 'income_mean'},
    'hies_state_percentile': {'date', 'state', 'percentile', 'variable', 'income'},
}

def fetch(name):
    url = BASE + name + '.csv'
    with urllib.request.urlopen(url, timeout=45) as response:
        raw = response.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(raw))
    if not REQUIRED[name].issubset(reader.fieldnames or []):
        raise ValueError(f'{name}: unexpected columns {reader.fieldnames}')
    rows = list(reader)
    if not rows:
        raise ValueError(f'{name}: empty CSV')
    return rows

def only(rows, **filters):
    found = [r for r in rows if all(r[k] == v for k, v in filters.items())]
    if len(found) != 1:
        raise ValueError(f'Expected one record for {filters}, got {len(found)}')
    return found[0]

def number(value):
    n = float(value)
    if not math.isfinite(n) or n < 0:
        raise ValueError(f'Invalid income: {value}')
    return round(n)

def build(datasets):
    years = [set(int(r['date'][:4]) for r in datasets[name]) for name in NAMES]
    common = set.intersection(*years)
    if not common:
        raise ValueError('No common survey year')
    year = max(common)
    date = f'{year}-01-01'
    national = only(datasets['hh_income'], date=date)
    selangor = only(datasets['hh_income_state'], date=date, state='Selangor')
    kuala_langat = only(datasets['hh_income_district'], date=date, state='Selangor', district='Kuala Langat')
    rows = [r for r in datasets['hies_state_percentile'] if r['date'] == date and r['state'] == 'Selangor']
    bands = []
    for p in range(1, 101):
        stats = {v: only(rows, percentile=str(p), variable=v) for v in ('minimum', 'median', 'maximum')}
        bands.append({'percentile': p, **{v: number(stats[v]['income']) if stats[v]['income'] else None for v in stats}})
    if len(bands) != 100 or any(bands[i]['median'] > bands[i+1]['median'] for i in range(99)):
        raise ValueError('Incomplete or unsorted percentile distribution')
    result = {
        'survey_year': year,
        'generated_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'medians': {'Malaysia': number(national['income_median']), 'Selangor': number(selangor['income_median']), 'Kuala Langat': number(kuala_langat['income_median'])},
        'means': {'Malaysia': number(national['income_mean']), 'Selangor': number(selangor['income_mean']), 'Kuala Langat': number(kuala_langat['income_mean'])},
        'selangor_percentiles': bands,
        'category_thresholds': {'m40': 5860, 't20': 12680},
        'category_note': 'National B40/M40/T20 cutoffs are rounded 2024 report thresholds; not Selangor thresholds.',
        'sources': {name: BASE + name + '.csv' for name in NAMES},
    }
    if year == 2024 and result['medians'] != {'Malaysia': 7017, 'Selangor': 10726, 'Kuala Langat': 10583}:
        raise ValueError('2024 source values differ from published figures; investigate before publishing')
    return result

def main():
    result = build({name: fetch(name) for name in NAMES})
    target = Path(__file__).resolve().parents[1] / 'data' / 'income.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"Wrote {target} for {result['survey_year']}: {result['medians']}")

if __name__ == '__main__':
    main()

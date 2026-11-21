#!/usr/bin/env python3
"""One-shot import of prototype telemetry CSV exports into a private Google Sheet.

No server or public Google credentials. Requires GOOGLE_ACCESS_TOKEN in the
researcher's environment, with the spreadsheets scope and Sheet edit access.
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HEADER = ['Timestamp', 'Group', 'Screen', 'Event', 'Detail', 'Event ID', 'Participant ID', 'Session ID']
RETRYABLE = {408, 429, 500, 502, 503, 504}


class SheetsError(Exception):
    def __init__(self, status):
        self.status = status
        super().__init__(f'Google Sheets request failed (HTTP {status}). Check API enablement, token scope, edit access, and tab name.')


def read_exports(paths):
    rows = {}
    for path in paths:
        with Path(path).open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.reader(handle)
            if next(reader, None) != HEADER:
                raise ValueError(f'{path}: expected the updated prototype telemetry CSV header')
            for line, row in enumerate(reader, 2):
                if not row:
                    continue
                if len(row) != 8 or not all(row[i] for i in (0, 1, 3, 5, 6, 7)):
                    raise ValueError(f'{path}:{line}: incomplete event')
                if row[1] not in ('A', 'B'):
                    raise ValueError(f'{path}:{line}: invalid prototype group')
                if row[5] in rows and rows[row[5]] != row:
                    raise ValueError(f'{path}:{line}: conflicting event ID')
                rows[row[5]] = row
    return list(rows.values())


def make_client(sheet_id, token):
    base = 'https://sheets.googleapis.com/v4/spreadsheets/' + sheet_id + '/values/'

    def call(method, range_name, body=None, append=False):
        url = base + urllib.parse.quote(range_name, safe='')
        if append:
            url += ':append?valueInputOption=RAW&insertDataOption=INSERT_ROWS'
        elif method == 'PUT':
            url += '?valueInputOption=RAW'
        request = urllib.request.Request(url, method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            raise SheetsError(exc.code) from None
    return call


def sync_rows(rows, tab, call, wait=time.sleep):
    """Read before append, deduplicating event IDs, including after an uncertain write.

    Use one importer at a time: Sheets append does not enforce unique IDs.
    """
    quoted_tab = "'" + tab.replace("'", "''") + "'"
    range_name = quoted_tab + '!A:H'
    remaining = {row[5]: row for row in rows}
    already_present = set()
    for attempt in range(5):
        try:
            existing = call('GET', range_name).get('values', [])
            if not existing:
                call('PUT', quoted_tab + '!A1:H1', {'values': [HEADER]})
            elif existing[0] != HEADER:
                raise ValueError('Destination header differs; use an empty Events tab or the exact export schema.')
            existing_ids = {row[5] for row in existing[1:] if len(row) > 5}
            already_present |= existing_ids & remaining.keys()
            pending = [row for key, row in remaining.items() if key not in existing_ids]
            for start in range(0, len(pending), 500):
                batch = pending[start:start + 500]
                call('POST', range_name, {'majorDimension': 'ROWS', 'values': batch}, append=True)
                for row in batch:
                    remaining.pop(row[5], None)
            return {'events_in_exports': len(rows), 'already_present_or_confirmed_after_retry': len(already_present),
                    'verified_or_uploaded': len(rows)}
        except (SheetsError, urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, SheetsError) and exc.status not in RETRYABLE:
                raise
            if attempt == 4:
                raise
            wait(2 ** attempt)
    raise RuntimeError('Upload did not finish')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exports', nargs='+', help='CSV files exported by either updated prototype')
    parser.add_argument('--spreadsheet-id', help='Private spreadsheet ID (not its full URL)')
    parser.add_argument('--tab', default='Events', help='Existing sheet tab, default Events')
    parser.add_argument('--dry-run', action='store_true', help='Validate and deduplicate files without Google access')
    args = parser.parse_args()
    try:
        rows = read_exports(args.exports)
        if args.dry_run:
            print(f'Validated {len(rows)} unique events; no data sent.')
            return
        if not args.spreadsheet_id or not re.fullmatch(r'[A-Za-z0-9_-]+', args.spreadsheet_id):
            parser.error('--spreadsheet-id must be a valid spreadsheet ID')
        token = os.environ.get('GOOGLE_ACCESS_TOKEN', '').strip()
        if not token:
            parser.error('Set GOOGLE_ACCESS_TOKEN in your local environment; never place it in the HTML')
        result = sync_rows(rows, args.tab, make_client(args.spreadsheet_id, token))
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, SheetsError, urllib.error.URLError, TimeoutError) as exc:
        print(f'Import failed: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

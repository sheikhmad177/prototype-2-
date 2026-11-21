"""Offline tests; deliberately never contacts Google or uses real participant data."""
import csv
import tempfile
import unittest
from pathlib import Path

from upload_to_sheets import HEADER, SheetsError, read_exports, sync_rows, main

ROW = ['2026-11-15T00:00:00Z', 'B', '4', 'complete_order', 'Final = ৳275', 'test-event', 'test-participant', 'test-session']


class UploadTests(unittest.TestCase):
    def test_csv_validation_and_deduplication(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'synthetic.csv'
            with path.open('w', newline='', encoding='utf-8-sig') as handle:
                writer = csv.writer(handle)
                writer.writerows([HEADER, ROW, ROW])
            self.assertEqual(read_exports([path, path]), [ROW])
            from unittest.mock import patch
            with patch('sys.argv', ['upload_to_sheets.py', str(path), '--dry-run']):
                main()

    def test_upload_retry_and_repeat_are_idempotent_for_single_importer(self):
        sheet = []
        uncertain = [True]

        def call(method, range_name, body=None, append=False):
            if method == 'GET':
                return {'values': sheet[:]}
            if method == 'PUT':
                sheet[:] = body['values']
                return {}
            self.assertTrue(append)
            sheet.extend(body['values'])
            if uncertain[0]:
                uncertain[0] = False
                raise TimeoutError('write succeeded but response was lost')
            return {}

        result = sync_rows([ROW], 'Events', call, wait=lambda _: None)
        self.assertEqual(sheet, [HEADER, ROW])
        self.assertEqual(result['verified_or_uploaded'], 1)
        sync_rows([ROW], 'Events', call, wait=lambda _: None)
        self.assertEqual(sheet, [HEADER, ROW])

    def test_header_mismatch_and_permission_error(self):
        with self.assertRaises(ValueError):
            sync_rows([ROW], 'Events', lambda *a, **k: {'values': [['wrong header']]})
        def denied(*args, **kwargs):
            raise SheetsError(403)
        with self.assertRaises(SheetsError):
            sync_rows([ROW], 'Events', denied)


if __name__ == '__main__':
    unittest.main()

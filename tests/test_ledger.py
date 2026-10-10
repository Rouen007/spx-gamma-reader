import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ledger', ROOT / 'spx-gamma-reader/scripts/ledger.py')
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class EvidenceChecks(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / 'examples/observation.json').read_text())

    def test_observation_accepts_unknown_time_but_decision_rejects(self):
        self.record['evidence'][0]['evidence_at'] = None
        self.assertFalse(ledger.validate(self.record)[0])
        self.assertTrue(ledger.validate(self.record)[1])
        self.record['mode'] = 'decision'
        self.assertTrue(ledger.validate(self.record)[0])

    def test_future_evidence_is_rejected(self):
        self.record['evidence'][0]['evidence_at'] = '2026-10-09T10:06:00-04:00'
        self.assertTrue(ledger.validate(self.record)[0])

    def test_naive_cutoff_is_rejected(self):
        self.record['decision_at'] = '2026-10-09T10:05:00'
        self.assertTrue(ledger.validate(self.record)[0])

    def test_received_after_cutoff_cannot_support_decision(self):
        self.record['mode'] = 'decision'
        self.record['evidence'][0]['received_at'] = '2026-10-09T10:06:00-04:00'
        self.assertTrue(ledger.validate(self.record)[0])

    def test_previous_session_cannot_support_current_decision(self):
        self.record['mode'] = 'decision'
        self.record['evidence'][0]['session_date'] = '2026-10-08'
        self.assertTrue(ledger.validate(self.record)[0])

    def test_basis_requires_matching_contract_and_time(self):
        spot = copy.deepcopy(self.record['evidence'][0])
        spot.update(id='spot', instrument='SPX', contract=None)
        self.record['evidence'].append(spot)
        self.record['used_evidence_ids'].append('spot')
        self.record['cross_instrument_alignment'] = 'basis'
        self.record['basis_max_skew_seconds'] = 2
        self.record['basis_max_age_seconds'] = 180
        self.record['basis'] = dict(spot=6000, futures=6020, value=20, contract='ESZ6',
                                   source='synthetic', spot_at='2026-10-09T10:03:00-04:00',
                                   futures_at='2026-10-09T10:03:01-04:00')
        self.assertFalse(ledger.validate(self.record)[0])
        self.record['basis']['contract'] = 'ESH7'
        self.assertTrue(ledger.validate(self.record)[0])
        self.record['basis']['contract'] = 'ESZ6'
        self.record['basis']['futures_at'] = '2026-10-09T10:04:00-04:00'
        self.assertTrue(ledger.validate(self.record)[0])
        self.record['basis']['futures_at'] = '2026-10-09T10:03:01-04:00'
        self.record['basis_max_age_seconds'] = 30
        self.assertTrue(ledger.validate(self.record)[0])

    def test_cvd_reset_and_unknown_settings_rejected(self):
        a = self.record['evidence'][0]
        b = copy.deepcopy(a)
        b['id'] = 'second'
        b['evidence_at'] = '2026-10-09T10:04:00-04:00'
        self.record['evidence'].append(b)
        self.record['used_evidence_ids'].append('second')
        self.record['cvd_comparisons'] = [[a['id'], b['id']]]
        self.assertTrue(ledger.validate(self.record)[0])
        settings = dict(range='session', start_at='2026-10-09T09:30:00-04:00',
                        min_size=0, max_size='all', reset='none')
        a['settings']['cvd'] = settings.copy()
        b['settings']['cvd'] = settings.copy()
        self.assertFalse(ledger.validate(self.record)[0])
        b['settings']['cvd']['reset'] = 'manual'
        self.assertTrue(ledger.validate(self.record)[0])

    def test_old_evidence_cannot_be_labeled_as_today(self):
        self.record['mode'] = 'decision'
        self.record['evidence'][0]['evidence_at'] = '2026-10-08T10:03:00-04:00'
        self.assertTrue(ledger.validate(self.record)[0])

    def test_cvd_malformed_settings_and_reverse_time_rejected(self):
        a = self.record['evidence'][0]
        b = copy.deepcopy(a)
        b.update(id='second', evidence_at='2026-10-09T10:04:00-04:00')
        self.record['evidence'].append(b)
        self.record['used_evidence_ids'].append('second')
        self.record['cvd_comparisons'] = [[b['id'], a['id']]]
        settings = dict(range=False, start_at='2099-01-01T00:00:00Z',
                        min_size=-5, max_size=-10, reset={})
        a['settings']['cvd'] = settings.copy()
        b['settings']['cvd'] = settings.copy()
        self.assertTrue(ledger.validate(self.record)[0])

    def test_duplicate_append_preserves_old_content(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'ledger.jsonl'
            ledger.append_record(path, self.record)
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                ledger.append_record(path, self.record)
            self.assertEqual(before, path.read_bytes())
            correction = copy.deepcopy(self.record)
            correction.update(record_id='correction', supersedes=self.record['record_id'],
                              correction_reason='new evidence')
            ledger.append_record(path, correction)
            self.assertTrue(path.read_bytes().startswith(before))
            self.assertEqual(2, len(path.read_text().splitlines()))


if __name__ == '__main__':
    unittest.main()

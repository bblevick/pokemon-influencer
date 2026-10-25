"""Rollback isolation and offline authorization; no native or hosted calls."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RollbackBindingTests(unittest.TestCase):
    def run_binding(self, experiment, rollback):
        env = dict(os.environ, POKEINFLUENCER_EXPERIMENT=experiment,
                   POKEINFLUENCER_RIVAL_ROLLBACK=rollback)
        return subprocess.run(
            [sys.executable, '-c',
             'import json; from campaign.provider import PRIVATE,E,LEDGER; '
             'print(json.dumps([str(PRIVATE),str(E),str(LEDGER)]))'],
            cwd=ROOT, env=env, capture_output=True, text=True)

    def test_rollback_workers_use_separate_carried_ledger(self):
        result = self.run_binding('rival01', '1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            str(ROOT / '.local/rival01-rollback'),
            str(ROOT / 'evidence/phase8/rival01-rollback'),
            str(ROOT / 'evidence/phase8/rival01-rollback/requests.json')])

    def test_original_rival_namespace_stays_original(self):
        result = self.run_binding('rival01', '0')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[2],
                         str(ROOT / 'evidence/phase8/rival01/requests.json'))

    def test_rollback_cannot_redirect_another_role_scope(self):
        result = self.run_binding('rocket01', '1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('rollback namespace requires Rival scope', result.stderr)

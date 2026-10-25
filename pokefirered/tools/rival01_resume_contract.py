#!/usr/bin/env python3
"""Reproduce parent-save cutoff behavior on a disposable retained-host copy.

No emulator, providers, opportunity creation, pairing, or original DB writes.
This diagnoses an unsupported reattachment; it does not implement one.
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
from campaign.scripted import ScriptedStore
from world.saves import fingerprint, layout_from_build
from rival01_prerequisites import METHODS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not args.label.replace('-', '').isalnum() or len(args.label) > 32:
        raise ValueError('bounded evidence label required')
    private = ROOT / '.local/rival01-native-resume'
    evidence = ROOT / 'evidence/phase8/rival01-native-resume'
    target = private / (args.label + '.sqlite3')
    result = evidence / (args.label + '.json')
    if target.exists() or result.exists():
        raise ValueError('refuse overwrite')
    source = ROOT / '.local/rival01-rollback/dots-renewal-committed-host.sqlite3'
    src = sqlite3.connect('file:' + str(source) + '?mode=ro', uri=True)
    dst = sqlite3.connect(target)
    src.backup(dst)
    dst.close()
    src.close()
    manifest_path = ROOT / 'evidence/phase8/rival01-rollback/manifest-native.json'
    manifest = json.loads(manifest_path.read_text())
    save = fingerprint((ROOT / '.local/rival01-rollback/pre-rival-pair.sav').read_bytes(),
                       layout_from_build(ROOT / manifest['rom_path']))
    expected = json.loads((ROOT / 'evidence/phase8/rival01-rollback/pre-rival-pair.json').read_text())
    committed = json.loads((ROOT / 'evidence/phase8/rival01-dots-renewal/committed-host-state.json').read_text())
    actor = 'trainer:fr:trainer:0326'
    with ScriptedStore(target, manifest_path) as store:
        def capture():
            return dict(campaign=store.campaign(), hashes={m:getattr(store, m)() for m in METHODS},
                        memos=[m for m in store.memo_records() if m['actor'] == actor],
                        lock=store.locked_preparation(actor),
                        strategyView=dict(store._one('SELECT * FROM strategy_view')),
                        prepView=dict(store._one('SELECT * FROM prep_view')))
        before = capture()
        assert before['memos'] == [committed['memo']] and before['lock'] == committed['lock']
        tables = ('strategy_log', 'prep_log', 'preparation_decision_log')
        def rows():
            return {t:[tuple(row) for row in store.db.execute('SELECT * FROM ' + t + ' ORDER BY rowid')]
                    for t in tables}
        original = rows()
        origin = store.authorize_launch(1731924082, save)
        after = capture()
        assert after['hashes'] == expected['hashes']
        assert not after['memos'] and after['lock'] is None and rows() == original
        report = dict(scope='Real retained DB-copy contract reproduction; not native reconnect proof',
                      before=before, after=after, origin=origin, hostedCalls=0,
                      originalRowsPreserved=True, activeMemoExcluded=True,
                      activeLockExcluded=True, parentCheckpointRestored=True,
                      reattachmentSupported=False, nativeRuntimeTested=False)
        result.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(activeMemoExcluded=True, activeLockExcluded=True,
                              hostedCalls=0, result=str(result))))

if __name__ == '__main__':
    main()

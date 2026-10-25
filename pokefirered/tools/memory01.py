#!/usr/bin/env python3
"""Trusted offline MEMORY administration, never a future model tool surface."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from world01 import manifest, save_identity
from memory.store import MemoryStore
E = ROOT / 'evidence/phase2/memory01'


def open_store(path):
    m = manifest()
    return MemoryStore(path, m['rom_sha256'], m['build_tag'])


def offline_store(path):
    with sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True) as db:
        meta = {k: json.loads(v) for k, v in db.execute('SELECT * FROM metadata')}
    return MemoryStore(path, meta['build'], meta['tag'])


def snapshot(w):
    return {'campaign': w.campaign(), 'canonicalSHA256': w.verify_replay(),
            'memorySHA256': w.verify_memory_replay(),
            'rick': w.for_actor('trainer:fr:trainer:0102').context(),
            'janice': w.for_actor('trainer:fr:trainer:0116').context(),
            'counts': {t: w._one('SELECT COUNT(*) n FROM ' + t)['n'] for t in
                       ('events', 'observations', 'memory_evidence')},
            'romSHA256': w.build}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['import', 'snapshot', 'context', 'replay', 'fixture-deliver', 'save-begin'])
    p.add_argument('--database', type=Path, default=ROOT / '.local/memory01/world.sqlite3')
    p.add_argument('--save', type=Path)
    p.add_argument('--actor', default='trainer:fr:trainer:0102')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    a.database.parent.mkdir(parents=True, exist_ok=True)
    with (open_store(a.database) if a.command in ('import', 'save-begin') else offline_store(a.database)) as w:
        if a.command == 'import':
            result = w.import_save(save_identity(a.save))
        elif a.command == 'context':
            result = w.for_actor(a.actor).context()
        elif a.command == 'fixture-deliver':
            rick = w.for_actor('trainer:fr:trainer:0102')
            source = next(r for r in rick.records(limit=256)['records'] if r['claim']['type'] == 'TRAINER_BATTLE_RESULT')
            c = w.campaign()
            did = w.deliver_fixture(delivery_id='rick-result-to-janice-v1', sender=source['actorID'], recipient='trainer:fr:trainer:0116', source_memory_id=source['memoryID'], campaign=c['id'], branch=c['active_branch'], cursor=c['cursor'])
            result = {'snapshot': snapshot(w), 'deliveredMemoryID': did,
                      'provenance': w.for_actor('trainer:fr:trainer:0116').provenance(did)}
        elif a.command == 'save-begin':
            cfg = json.loads((ROOT / '.local/memory01-launch.json').read_text())
            result = {'intent': w.begin_save(cfg['nonce'], save_identity(a.save or cfg['save']))}
        else:
            result = snapshot(w)
    serialized = json.dumps(result, indent=2) + '\n'
    if a.output:
        a.output.write_text(serialized)
    print(serialized)

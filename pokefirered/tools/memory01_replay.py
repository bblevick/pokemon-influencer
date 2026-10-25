#!/usr/bin/env python3
"""Offline stored-history replay: no emulator/ROM, provider, SQL input or .env.

Fixture JSON is administrative source history, NOT an actor-context packet.
"""
import argparse
import json
import tempfile
from pathlib import Path
from memory01 import offline_store, snapshot
from memory.store import MemoryStore

TABLES = ('campaigns', 'branches', 'events', 'launches', 'streams', 'deliveries',
          'observations', 'projection', 'checkpoints', 'save_intents', 'outbox',
          'memory_sources', 'memory_evidence', 'memory_branches', 'memory_view',
          'memory_checkpoints')


def export(w):
    return {'fixtureVersion': 1, 'worldSchema': 1, 'memorySchema': 1,
            'reducerVersion': 1, 'metadata': {r['key']: json.loads(r['value']) for r in w.db.execute('SELECT * FROM metadata')},
            'tables': {t: [dict(r) for r in w.db.execute('SELECT * FROM ' + t + ' ORDER BY rowid')] for t in TABLES},
            'expected': snapshot(w), 'classification': 'administrative stored source history; never model context'}


def replay_fixture(path):
    if path.stat().st_size > 8_000_000:
        raise ValueError('fixture byte limit')
    fixture = json.loads(path.read_text())
    if (fixture['fixtureVersion'], fixture['worldSchema'], fixture['memorySchema'], fixture['reducerVersion']) != (1, 1, 1, 1) or set(fixture['tables']) != set(TABLES):
        raise ValueError('fixture version/table allowlist')
    meta = fixture['metadata']
    with tempfile.TemporaryDirectory() as tmp, MemoryStore(Path(tmp) / 'replay.sqlite3', meta['build'], meta['tag']) as w:
        if meta != {r['key']: json.loads(r['value']) for r in w.db.execute('SELECT * FROM metadata')}:
            raise ValueError('fixture metadata compatibility')
        w.db.execute('BEGIN IMMEDIATE'); w.db.execute('PRAGMA defer_foreign_keys=ON')
        try:
            for table in TABLES:
                columns = [r['name'] for r in w.db.execute('PRAGMA table_info(' + table + ')')]
                rows = fixture['tables'][table]
                if not isinstance(rows, list) or len(rows) > 100_000 or any(set(r) != set(columns) for r in rows):
                    raise ValueError('fixture row/column allowlist')
                sql = 'INSERT INTO ' + table + '(' + ','.join(columns) + ') VALUES (' + ','.join('?' for _ in columns) + ')'
                w.db.executemany(sql, [[r[c] for c in columns] for r in rows])
            w.db.execute('COMMIT')
        except Exception:
            w.db.execute('ROLLBACK')
            raise
        result = snapshot(w)
        if result != fixture['expected']:
            raise ValueError('fixture replay/context mismatch')
        return {'passed': True, 'canonicalSHA256': result['canonicalSHA256'], 'memorySHA256': result['memorySHA256'], 'counts': result['counts'], 'scope': 'offline fixture replay; not a new playthrough'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database', type=Path)
    p.add_argument('--fixture', type=Path)
    p.add_argument('--export', type=Path)
    a = p.parse_args()
    if bool(a.database) == bool(a.fixture):
        p.error('exactly one database or fixture is required')
    if a.fixture:
        result = replay_fixture(a.fixture)
    else:
        with offline_store(a.database) as w:
            result = snapshot(w)
            if a.export:
                a.export.write_text(json.dumps(export(w), indent=2) + '\n')
    print(json.dumps(result, indent=2))

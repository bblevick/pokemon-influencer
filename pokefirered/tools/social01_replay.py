#!/usr/bin/env python3
"""Offline replay of committed administrative history, never NPC context."""
import argparse,json,tempfile
from pathlib import Path
from social01 import offline_store,snapshot
from social.store import SocialStore
from memory01_replay import TABLES as MEMORY_TABLES
TABLES=MEMORY_TABLES+('social_log','social_branches','social_view','social_checkpoints')

def export(w):
    return {'fixtureVersion':1,'worldSchema':1,'memorySchema':1,'socialSchema':1,'reducerVersion':1,
            'socialConfigSHA256':w.config_hash,'metadata':{r['key']:json.loads(r['value']) for r in w.db.execute('SELECT * FROM metadata')},
            'tables':{t:[dict(r) for r in w.db.execute('SELECT * FROM '+t+' ORDER BY rowid')] for t in TABLES},
            'expected':snapshot(w),'classification':'administrative source history; never model context'}

def replay_fixture(path):
    if path.stat().st_size>8_000_000:raise ValueError('fixture byte limit')
    f=json.loads(path.read_text())
    if any(f[k]!=1 for k in ('fixtureVersion','worldSchema','memorySchema','socialSchema','reducerVersion')) or set(f['tables'])!=set(TABLES):raise ValueError('fixture version/table allowlist')
    meta=f['metadata']
    with tempfile.TemporaryDirectory() as tmp,SocialStore(Path(tmp)/'replay.sqlite3',meta['build'],meta['tag']) as w:
        if meta!={r['key']:json.loads(r['value']) for r in w.db.execute('SELECT * FROM metadata')} or f['socialConfigSHA256']!=w.config_hash:raise ValueError('fixture compatibility')
        w.db.execute('BEGIN IMMEDIATE');w.db.execute('PRAGMA defer_foreign_keys=ON')
        try:
            for table in TABLES:
                cols=[r['name'] for r in w.db.execute('PRAGMA table_info('+table+')')];rows=f['tables'][table]
                if not isinstance(rows,list) or len(rows)>100_000 or any(not isinstance(r,dict) or set(r)!=set(cols) for r in rows):raise ValueError('fixture row/column allowlist')
                w.db.executemany('INSERT INTO '+table+'('+','.join(cols)+') VALUES ('+','.join('?' for _ in cols)+')',[[r[c] for c in cols] for r in rows])
            w.db.execute('COMMIT')
        except Exception:w.db.execute('ROLLBACK');raise
        result=snapshot(w)
        if result!=f['expected']:raise ValueError('fixture replay/context mismatch')
        return {'passed':True,**{k:result[k] for k in ('canonicalSHA256','memorySHA256','socialSHA256','counts')},'scope':'offline committed replay; no emulator, ROM or provider'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',type=Path);p.add_argument('--fixture',type=Path);p.add_argument('--export',type=Path);a=p.parse_args()
    if bool(a.database)==bool(a.fixture):p.error('exactly one database or fixture')
    if a.fixture:result=replay_fixture(a.fixture)
    else:
        with offline_store(a.database) as w:
            result=snapshot(w)
            if a.export:a.export.write_text(json.dumps(export(w),indent=2)+'\n')
    print(json.dumps(result,indent=2))

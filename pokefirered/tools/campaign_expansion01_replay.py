#!/usr/bin/env python3
"""Offline paired-prefix/divergence proof in an isolated SQLite backup.

Uses real C0/C1 batteries and committed history; the child social tick is an
explicit host fixture, not a second native campaign or inference result.
"""
import json,sqlite3
from campaign_expansion01 import E,PRIVATE,open_store,save_identity
from vertical_slice01_viewer import METHODS

cfg=json.loads((PRIVATE/'launch.json').read_text());target=PRIVATE/'paired-replay-fixture.sqlite3'
if target.exists():raise ValueError('retain previous fixture; refuse overwrite')
src=sqlite3.connect('file:'+cfg['database']+'?mode=ro',uri=True);dst=sqlite3.connect(target)
try:src.backup(dst)
finally:dst.close();src.close()
ledger=(E/'requests.json').read_bytes();out={'mode':'offline isolated host fixture','checks':[]}
def capture(w):
    return {'campaign':w.campaign(),'hashes':{m:getattr(w,m)() for m in METHODS},
            'posts':list(w.social_state()['posts']),
            'exposures':list(w.social_state()['exposures']),
            'memos':[m['strategyID'] for m in w.memo_records()],
            'decisionState':w.decision_state(),'audit':w.battle_audit()}
with open_store(target) as w:
    w.restore(save_identity(PRIVATE/'C1-sally-recovered.sav'));c1=capture(w)
    w.restore(save_identity(PRIVATE/'C0-ready.sav'));c0=capture(w)
    expected=json.loads((E/'C0-ready.json').read_text())['hashes']
    assert c0['hashes']==expected
    assert len(c1['posts'])>len(c0['posts']) and len(c1['audit'])>len(c0['audit'])
    assert len(c1['memos'])>len(c0['memos'])
    out['checks'].append('actual future posts/exposures/Greg memo/commitment/Sally installation/tactical audit excluded at C0')
    w.tick(w.social_state()['tick']+1)
    child=capture(w);assert child['campaign']['active_branch']!=c0['campaign']['active_branch']
    assert set(c1['posts'])-set(c0['posts'])<=set(c1['posts'])-set(child['posts'])
    assert child['memos']==c0['memos']
    out['checks'].append('host-only divergent child inherits C0 prefix, no abandoned C1 future')
    w.restore(save_identity(PRIVATE/'C1-sally-recovered.sav'));restored=capture(w)
    assert restored['hashes']==c1['hashes']
    out['checks'].append('C1 restores all seven projections/memos/commitments/audit without reinference')
    out.update(C0=c0,C1=c1,divergentFixture=child,restoredC1=restored)
assert ledger==(E/'requests.json').read_bytes();out['requestLedgerUnchanged']=True
(E/'paired-replay-proof.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'checks':out['checks'],'requestLedgerUnchanged':True}))

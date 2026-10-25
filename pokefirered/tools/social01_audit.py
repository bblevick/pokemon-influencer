#!/usr/bin/env python3
"""Trusted internal lineage/checkpoint audit; never register as an NPC tool."""
import argparse,json
from pathlib import Path
from social01 import offline_store,ROOT
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--database',type=Path,default=ROOT/'.local/social01/world.sqlite3');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with offline_store(a.database) as w:
        w.verify_replay();w.verify_memory_replay();w.verify_social_replay()
        result={'classification':'internal full provenance, not actor-readable context','campaign':w.campaign(),
                'branches':[dict(r) for r in w.db.execute('SELECT b.*,m.parent_cutoff memoryParentCutoff,s.parent_cutoff socialParentCutoff FROM branches b JOIN memory_branches m ON m.branch=b.id JOIN social_branches s ON s.branch=b.id ORDER BY b.rowid')],
                'checkpoints':[dict(r) for r in w.db.execute('SELECT c.*,m.cutoff memoryCutoff,s.cutoff socialCutoff,s.state_sha socialSHA256 FROM checkpoints c JOIN memory_checkpoints m ON m.checkpoint=c.id JOIN social_checkpoints s ON s.checkpoint=c.id ORDER BY c.created_at')],
                'socialLog':[{**dict(r),'payload':json.loads(r['payload'])} for r in w.db.execute('SELECT * FROM social_log ORDER BY seq')],
                'evidence':[{**dict(r),'claim':json.loads(r['claim'])} for r in w.db.execute('SELECT * FROM memory_evidence ORDER BY seq')],
                'canonical':[dict(r) for r in w.db.execute('SELECT * FROM events ORDER BY cursor')],
                'observations':[dict(r) for r in w.db.execute('SELECT * FROM observations ORDER BY rowid')]}
    a.output.write_text(json.dumps(result,indent=2)+'\n')

#!/usr/bin/env python3
"""Explicit closeout recovery using the existing validated normal-save APIs.

Requires stopped emulator/host. Never changes a receipt, battery, cursor, or
history. A suspended campaign is resumed only by restoring the newly validated
known pair. This is recovery evidence, not uninterrupted campaign acceptance.
"""
import json
from campaign_expansion01 import E,PRIVATE,open_store,save_identity
from vertical_slice01_viewer import METHODS

cfg=json.loads((PRIVATE/'launch.json').read_text())
receipt=json.loads((E/'save-receipts.jsonl').read_text().splitlines()[-1])
ledger=(E/'requests.json').read_bytes()
with open_store(cfg['database']) as w:
    intent=w.pending_save()
    if not intent or w.campaign()['status']!='incomplete':
        raise ValueError('explicit suspended pending-save recovery required')
    before=w.campaign()
    checkpoint=w.finish_save_with_progression(intent['id'],cfg['save'],receipt)
    w.restore(save_identity(cfg['save']))
    out={'mode':'existing service API recovery; not automatic host acceptance',
         'before':before,'intent':intent,'receipt':receipt,
         'checkpoint':checkpoint,'after':w.campaign(),
         'hashes':{m:getattr(w,m)() for m in METHODS}}
assert ledger==(E/'requests.json').read_bytes()
(E/'save-recovery.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'checkpoint':checkpoint['id'],'status':out['after']['status'],
                  'sevenHashesVerified':True,'requestLedgerUnchanged':True}))

#!/usr/bin/env python3
"""Existing managed workflow over the verified recovery copy; strictly offline."""
import os,sys,runpy,json
from pathlib import Path
os.environ['POKEINFLUENCER_EXPERIMENT']='campaign_expansion01';os.environ['POKEINFLUENCER_CAMPAIGN_FINAL']='1'
import campaign_expansion01 as original
ROOT=original.ROOT;original.E=ROOT/'evidence/phase6/campaign_expansion01_final/final-recovery';original.PRIVATE=ROOT/'.local/campaign_expansion01_recovery'
# No hosted route checks or network inference are permitted in this workflow.
import urllib.request
def forbidden(*a,**kw):raise RuntimeError('final recovery forbids hosted network requests')
urllib.request.urlopen=forbidden
if '--live' in sys.argv or '--continue-authorized-run' in sys.argv:raise ValueError('zero-inference recovery only')
for n in ('campaign.expansion_runtime','campaign.runtime'):
 module=__import__(n,fromlist=['E']);module.E=original.E
if sys.argv[1]=='paginate':
 (original.E/'kent-resolution').mkdir(exist_ok=True)
 sys.argv=[sys.argv[0],*sys.argv[2:]];runpy.run_path(str(ROOT/'tools/campaign_expansion01_paginate.py'),run_name='__main__')
elif sys.argv[1]=='capture':
 from campaign.recovery import PROOF_METHODS,table_hashes
 from roster.extract import digest
 cfg=json.loads((original.PRIVATE/'launch.json').read_text());label=sys.argv[2]
 with original.open_store(cfg['database']) as w:
  value={'campaign':w.campaign(),'save':original.save_identity(cfg['save']).as_dict(),'checkpoint':w.get_save_checkpoint(original.save_identity(cfg['save']).fingerprint),'sevenHashes':{m:getattr(w,m)() for m in PROOF_METHODS},'domainTableHashes':table_hashes(w),'preparationHash':digest(w.preparation_state()),'tacticalAuditHash':digest(w.battle_audit()),'pendingSave':w.pending_save(),'jobs':{t:[dict(r) for r in w.db.execute('SELECT * FROM '+t)] for t in ('strategy_jobs','puppeteer_jobs','preparation_decision_jobs')}}
 (original.E/(label+'.json')).write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({'label':label,'status':value['campaign']['status'],'cutoff':value['campaign']['cursor']}))
else:original.main()

#!/usr/bin/env python3
"""Capture actual active PREP evidence. Native actions remain separate and explicit."""
import argparse,json,shutil
from pathlib import Path
from prep01 import ROOT,E,open_store,save_identity
from prep01_report import report
from prep.domain import resolve_preparation_envelope,validate_preparation_candidate,PreparationEnvelope
RICK='trainer:fr:trainer:0102';BROCK='trainer:fr:trainer:0414';JANICE='trainer:fr:trainer:0116'
def capture(kind,label):
 cfg=json.loads((ROOT/'.local/prep01-launch.json').read_text());db=cfg['database']
 with open_store(db) as w:
  if w.campaign()['status']!='paired' or w.pending_save():raise ValueError('active paired normal save required')
  identity=save_identity(cfg['save']);cp=w.get_save_checkpoint(identity.fingerprint)
  if not cp or cp['kind']!='normal_save':raise ValueError('actual native normal checkpoint required')
  p=w.preparation_state();world=w.state();scope=dict(w._one('SELECT * FROM prep_view'))
  result={'evidenceKind':'actual managed mGBA normal battery Continue/save, not fixture','preparation':p,'world':world,'campaign':w.campaign(),'scope':scope,'save':identity.as_dict(),'launchNonce':cfg['nonce']}
  if kind in ('before','after'):
   pairings=[json.loads(line) for line in (E/'pairings.jsonl').read_text().splitlines()];result['pairing']=next(x for x in reversed(pairings) if x['checkpoint']['id']==cp['id'])
  else:
   shot=ROOT/'evidence/private/prep01'/f'{label}.png'
   if not shot.exists():raise ValueError('actual Continue screenshot missing')
   result['continueScreenshot']=str(shot.relative_to(ROOT))
   old=json.loads((E/'native-after-boulder.json').read_text())['rick']['result']['candidateSet']['candidates'][0]
   env=resolve_preparation_envelope(w,RICK)
   result['oldCandidateValidation']=validate_preparation_candidate(env,old,w) if isinstance(env,PreparationEnvelope) else {'valid':False,'reason':'preparation_opportunity_unavailable','activeResolution':env}
   result['oldEnvelopeID']=old['envelopeID'];result['activeEnvelopeID']=env.packet()['envelopeID'] if isinstance(env,PreparationEnvelope) else None
 result['rick']=report(db,RICK,'forest-post-boulder-1')
 if kind=='before':
  result['brock']=report(db,BROCK,'first');shutil.copy2(cfg['save'],ROOT/'.local/prep01/before-brock.sav');out=E/'native-before-brock.json'
 elif kind=='after':
  result['janice']=report(db,JANICE,'forest-post-boulder-1');result['janiceFirst']=report(db,JANICE,'first');shutil.copy2(cfg['save'],ROOT/'.local/prep01/post-boulder.sav');out=E/'native-after-boulder.json'
 else:
  out=E/'native-restores.json';all_results=json.loads(out.read_text()) if out.exists() else {};all_results[kind]=result;result=all_results
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'kind':kind,'output':str(out),'counter':identity.counter,'checkpointID':cp['id']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('kind',choices=['before','after','freshAfter','beforeRestore','afterRestore']);p.add_argument('--label',default='');a=p.parse_args();kind={'beforeRestore':'before','afterRestore':'after'}.get(a.kind,a.kind)
 # Restore keys must be distinct from native before/after capture actions.
 if a.kind.endswith('Restore'):
  capture(a.kind,a.label)
  path=E/'native-restores.json';r=json.loads(path.read_text());r[kind]=r.pop(a.kind);path.write_text(json.dumps(r,indent=2)+'\n')
 else:capture(kind,a.label)

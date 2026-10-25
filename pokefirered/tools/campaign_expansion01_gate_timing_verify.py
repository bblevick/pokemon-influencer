#!/usr/bin/env python3
"""Assert actual aborted native trial evidence; never treat it as campaign completion."""
import json,sys,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign_expansion01_gate_native import base
from battle.lifecycle import TERMINAL
E=base.E

def main():
 provider=[json.loads(l) for l in (E/'timing-provider.jsonl').read_text().splitlines()];audit=[json.loads(l) for l in (E/'battle-audit.jsonl').read_text().splitlines()];starts=[r for r in provider if r['event']=='deterministic-provider-start'];assert [r['case'] for r in starts]==['before','just-before','just-after','well-after','never'];nonce=starts[0]['scope']['nonce'];cases=[]
 cfg=json.loads((base.PRIVATE/'launch.json').read_text())
 database=base.PRIVATE/'abandoned-timing-branch.sqlite3'
 if not database.exists():database=Path(cfg['database'])
 with base.open_store(database) as w:
  events=[e for e in w.get_canonical_events() if e['record']['session']==nonce];assert not any(e['record']['eventType']=='BATTLE_ENDED' for e in events)
  lifecycle=[r for r in w.decision_lifecycle() if r['session']==nonce]
  for i,start in enumerate(starts,1):
   request=start['scope']['request'];rows=[r for r in lifecycle if r['nativeRequest']==request];terminals=[r for r in rows if r['stage'] in TERMINAL];assert len(terminals)==1
   native=next(r for r in audit if r['event']=='native-terminal' and r.get('session')==nonce and r['nativeRequest']==request)
   resolved=[e for e in events if e['record']['eventType']=='BATTLE_ACTION_RESOLVED' and e['record']['turnID']==i and e['record']['payload']['actorSide']==1];assert len(resolved)==1
   result=next((r for r in provider if r['case']==start['case'] and r['event']=='deterministic-provider-result'),None)
   if i<=2:assert terminals[0]['stage']=='EXECUTED' and native['source']=='external_test' and any(r['stage']=='RESULT_PUBLISHED' for r in rows)
   else:
    assert terminals[0]['stage']=='CANCELED_TIMEOUT_FALLBACK' and native['source']=='vanilla_fallback';assert not any(r['stage']=='RESULT_PUBLISHED' for r in rows)
    if result:assert result['elapsed']>2.75
   cases.append({'case':start['case'],'scope':start['scope'],'providerElapsedSeconds':result.get('elapsed') if result else None,'lifecycle':rows,'nativeTerminal':native,'canonicalResolvedAction':resolved[0],'lateOutputNotPublished':i>=3})
  assert len([e for e in events if e['record']['eventType']=='BATTLE_ACTION_RESOLVED' and e['record']['payload']['actorSide']==0 and e['record']['payload']['announcedMoveID']==45])==5
  report={'mode':'actual emulator, deterministic providers, deliberately aborted test branch; not live Greg acceptance','hostedGenerationRequests':0,'fiveCasesPassed':True,'cases':cases,'campaignCompleted':False,'canonicalTrialEvents':events,'campaign':w.campaign(),'batterySHA256':__import__('hashlib').sha256(Path(cfg['save']).read_bytes()).hexdigest(),'inputEvidence':'input-commands.jsonl; timing-* screenshots','heartbeatEvidence':'emulator.jsonl actual samples progressed through never-returning provider; RPC remained responsive'}
  (E/'native-timing-matrix.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'fiveCasesPassed':True,'nonce':nonce,'campaignCompleted':False}))
if __name__=='__main__':main()

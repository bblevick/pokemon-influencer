#!/usr/bin/env python3
"""Export actual closeout actions/checkpoints; never infer unobserved execution.

The native event ledger supplies resolution evidence. Provider selections and
native acceptance alone are not proof of resolution or model reasoning.
"""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from vertical_slice01_host import E,PRIVATE,open_store

def main():
 d=json.loads((E/'closeout-final.json').read_text())
 installation=next(iter(d['decisions']['installations'].values()))['receipt']
 nonce=installation['nonce'];battle=installation['battle']
 cfg=json.loads((PRIVATE/'launch.json').read_text())
 with open_store(cfg['database']) as w:
  events=[e for e in w.get_canonical_events() if e['record']['session']==nonce and e['record']['battleID']==battle]
 rows=[json.loads(x) for x in (E/'battle-audit.jsonl').read_text().splitlines()]
 selections=[x for x in rows if x['event']=='selection' and x['request']['nativeState']['nonce']==nonce]
 terminals=[x for x in rows if x['event']=='native-terminal' and x.get('session')==nonce]
 trace=[]
 for s in selections:
  req=s['request'];turn=req['nativeState']['turn']
  terminal=[x for x in terminals if x['turn']==turn]
  resolved=[e for e in events if e['record']['turnID']==turn and e['record']['eventType']=='BATTLE_ACTION_RESOLVED' and e['record']['payload']['actorSide']==1]
  trace.append({'turn':turn,'source':s['source'],'strategyID':req['strategyID'],'strategyMemoSubjective':d['memos'][0]['strategyText'],'authorizedStateAndPersonality':req['state'],'fairNativeState':req['nativeState'],'legalChoices':req['choices'],'selected':s['result'],'nativeSelected':s['nativeSelected'],'nativeAcceptance':[{k:v for k,v in t.items() if k!='selection'} for t in terminal],'actualNativeResolutionEvents':resolved,'hostLatencySeconds':s.get('hostLatencySeconds'),'interpretationLimit':'Memo is subjective intent; no inferred provider rationale. Announced native move is distinguished from accepted choice.'})
 (E/'closeout-turn-trace.json').write_text(json.dumps({'accepted':False,'battle':battle,'nonce':nonce,'turns':trace,'canonicalBattleEvents':events},indent=2)+'\n')
 inputs=[json.loads(x) for x in (E/'input-commands.jsonl').read_text().splitlines()]
 segments=[];pending=[]
 for r in inputs:
  pending.append(r)
  if r['command'].startswith('shot '):
   label=r['command'][5:]
   if label.startswith('closeout-'):segments.append({'label':label,'commands':pending})
   pending=[]
 checkpoints=[]
 for label in ('closeout-r1','closeout-r2','closeout-gym-ready','closeout-final'):
  snap=json.loads((E/(label+'.json')).read_text())
  checkpoints.append({'label':label,'checkpoint':snap['checkpoint']['id'],'fingerprint':snap['save']['fingerprint'],'normalBattery':str(PRIVATE.relative_to(ROOT)/(label+'.sav')),'restoreCommand':f'.venv/bin/python tools/vertical_slice01_launch.py --restore .local/vertical_slice01/{label}.sav --start','captureCommand':f'.venv/bin/python tools/vertical_slice01_capture.py closeout-restored-{label.removeprefix("closeout-")}','snapshotLimit':'Captured current host state may include results after the preceding Save. Restored artifacts establish the actual checkpoint cutoff.'})
 routes=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(E.glob('closeout*-route.json'))]
 out={'version':1,'accepted':False,'startsAt':'Fresh normal S1 restore containing the real Rick common prefix; native wild encounter created a legitimate branch','fullNewGameLiveGoldenTested':False,'fullBlindReplayTested':False,'nativeSegments':segments,'collisionRoutes':routes,'checkpoints':checkpoints,'turnTrace':'evidence/phase4/vertical_slice01/closeout-turn-trace.json','missingGates':['turn19 native fallback after bounded allocation exhaustion','no Boulder award on the live-memo branch'],'nondeterminism':['native encounter/damage/action RNG','provider latency and output','normal dialogue pacing; screenshot field verification required'],'nextReplaySeed':'closeout-gym-ready.sav retains exact memo/lock, no Gym result; any further hosted run requires a new explicit allowance','stopBefore':['campaign expansion','new roster selection','endgame']}
 (E/'closeout-native-path.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'actualTurns':len(trace),'nativeSegments':len(segments),'checkpointPaths':len(checkpoints),'accepted':False}))

if __name__=='__main__':main()

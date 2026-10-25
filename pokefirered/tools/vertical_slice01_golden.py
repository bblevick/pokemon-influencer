#!/usr/bin/env python3
"""Export retained actual native path; preserve recovery/nondeterminism honestly.

This records the run and checkpoint-driven regression commands. It does not
claim that blind input replay or a new-game/live-model golden run has passed.
"""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from vertical_slice01_host import E

def main():
 rows=[json.loads(x) for x in (E/'input-commands.jsonl').read_text().splitlines()]
 segments=[];pending=[];active=False
 for row in rows:
  pending.append(row['command'])
  if row['command'].startswith('shot '):
   label=row['command'][5:]
   if label=='clean-s0-field':active=True
   if active:segments.append({'label':label,'nativeCommands':pending,'recordedAtUnix':row['time']})
   pending=[]
   if label=='gym-brock-reader-close':active=False
 checkpoints=[]
 for stage in ('S0','S1','S2','S3'):
  d=json.loads((E/(stage+'.json')).read_text());cp=d['checkpoint']
  checkpoints.append({'stage':stage,'checkpoint':cp['id'],'normalBattery':'.local/vertical_slice01/'+stage+'.sav','restoreCommand':'.venv/bin/python tools/vertical_slice01_launch.py --restore .local/vertical_slice01/'+stage+'.sav --start','assertCommand':'.venv/bin/python tools/vertical_slice01_verify.py '+stage})
 routes=[]
 for path in sorted(E.glob('*-route.json')):
  routes.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 out={'version':1,'qualification':'actual checkpoint-driven native milestones and recorded input trace; live acceptance blocked by fallback StrategyMemo','startsAt':'explicit pre-Rick normal battery, not New Game or starter selection','fullBlindReplayTested':False,'fullNewGameLiveGoldenTested':False,'checkpoints':checkpoints,'nativeSegments':segments,'collisionRoutes':routes,'viewerReplayCommand':'.venv/bin/python tools/vertical_slice01_viewer.py S3 --menu-cursor 0','artifactCheckCommand':'.venv/bin/python tools/verify_vertical_slice01.py','nondeterminism':['wild encounter/species/action/damage RNG','Sammy loss and ordinary blackout recovery','provider availability/latency/text output','dialogue requires verified field before Save; retained same-intent recovery'],'stopBefore':['post-Brock preparation','follower rematch','campaign expansion','endgame']}
 (E/'golden-path.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'retainedNativeSegments':len(segments),'checkpointPaths':4,'collisionRouteArtifacts':len(routes),'fullLiveGoldenAccepted':False}))
if __name__=='__main__':main()

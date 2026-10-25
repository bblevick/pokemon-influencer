#!/usr/bin/env python3
"""Read retained actual artifacts; does not play the game or invoke providers."""
import sys,json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));E=ROOT/'evidence/phase4/battle_end01'
from bridge.events_wire import Message
from bridge.events import decode_event
from battle.lifecycle import TERMINAL
checks=[]
def check(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def read(name):return json.loads((E/name).read_text())
launches=list(map(json.loads,(E/'launches.jsonl').read_text().splitlines()))
logs=list(map(json.loads,(E/'emulator.jsonl').read_text().splitlines()))
starts=[i for i,x in enumerate(logs) if x['event']=='build-validated'];runs=[]
deliveries=list(map(json.loads,(E/'deliveries.jsonl').read_text().splitlines()))
for k,i in enumerate(starts):
 launch=launches[k];segment=logs[i:starts[k+1] if k+1<len(starts) else len(logs)]
 native=[{'frame':x['frame'],**dict(zip(('outcome','battleMain','callback2','request','controllerState','workPointer','eventCounter','mailSequence','mailState','lastAck'),map(int,x['detail'].split(','))))} for x in segment if x['event']=='battle-end-native']
 wire=[]
 for d in deliveries:
  m=Message.decode(bytes.fromhex(d['wireHex'])[2:])
  if m.nonce==launch['nonce']:
   r=decode_event(m)
   if r['eventType'] in ('BATTLE_ENDED','TRAINER_DEFEATED'):
    wire.append({'eventType':r['eventType'],'nativeBattle':r['battleID'],'turn':r['turnID'],'sequence':m.sequence,'run':m.generation,'payload':r['payload'],'commit':d['result'],'campaign':d['campaign'],'wireHex':d['wireHex']})
 # Keep terminal state transitions, last native action and retirement, not all frames.
 first=next((j for j,x in enumerate(native) if x['outcome']),len(native))
 terminal=native[max(0,first-1):]
 runs.append({'nonce':launch['nonce'],'ROM':launch['romSHA256'],'launchOrigin':launch['origin'],'nativeTrace':terminal,'terminalDeliveries':wire,'samples':[x for x in segment if x['event']=='sample'],'testInputStopped':[x for x in segment if x['event']=='player-path-stopped']})
(E/'lifecycle-trace.json').write_text(json.dumps({'format':1,'actualEmulator':True,'hostedRequests':0,'runs':runs,'originalBoundary':read('original-boundary-investigation.json')},indent=2)+'\n')
for label,outcome,mode in [('external-progress2',2,'external'),('external-delay-loss',2,'external'),('vanilla-result',2,'vanilla'),('victory-paired-final',1,'external')]:
 x=read(label+'.json');bs=[b for b in x['world']['battles'].values() if b['sourceTrainerID']==414]
 check(label+' exactly one completed native Brock result',len(bs)==1 and bs[0]['ended'] and bs[0]['outcome']==outcome)
 os=[o for o in x['obligations'].values() if o['actorID']=='trainer:fr:trainer:0414']
 check(label+' automatic unpublished mandatory recap',len(os)==1 and os[0]['battleID']==bs[0]['battleID'] and os[0]['status']=='RECAP_REQUIRED' and os[0]['outcome']==outcome)
 for r in x['lifecycle']:
  if r['stage']=='REQUESTED':
   identity=(r['session'],r['generation'],r['nativeRequest']);ends=[a for a in x['lifecycle'] if (a['session'],a['generation'],a['nativeRequest'])==identity and a['stage'] in TERMINAL]
   check(label+' terminal tactical disposition '+str(identity),len(ends)==1)
 if outcome==1:check('normal battery Boulder and defeated flags',all(x['batteryBoulder']['flags'].values()))
 elif mode=='vanilla':check('vanilla path has no external tactical work',not x['lifecycle'])
for run in runs:
 wire=run['terminalDeliveries'];ends=[r for r in wire if r['eventType']=='BATTLE_ENDED']
 if ends:
  check('same canonical terminal ID for all retries '+str(run['nonce']),len({r['commit']['eventID'] for r in ends})==1)
  first=ends[0];seq=first['sequence'];native=run['nativeTrace']
  check('terminal copied before heap cleanup and eventually retired '+str(run['nonce']),any(x['mailSequence']==seq and x['workPointer']==0 for x in native) and any(x['lastAck']==seq and x['mailState']==0 for x in native))
  terminalRequest=next(x['request'] for x in native if x['outcome'])
  check('no tactical request after native outcome '+str(run['nonce']),all(x['request']==terminalRequest for x in native if x['outcome']))
  if len(ends)>1:check('delayed ACK actual duplicate delivery '+str(run['nonce']),any(r['commit']['duplicate'] for r in ends))
check('fresh host duplicate is durable',read('fresh-host-terminal-dedupe.json')['worldHashUnchanged'])
check('fresh OS victory reload preserves scoped state',read('victory-reload-proof.json')['sevenHashesEqual'] and read('victory-reload-proof.json')['obligationsEqual'])
for label in ('pre-brock-restored','abort-restored'):
 x=read(label+'.json');check(label+' excludes all abandoned Brock state',not any(b['sourceTrainerID']==414 for b in x['world']['battles'].values()) and not x['lifecycle'] and not any(o['actorID']=='trainer:fr:trainer:0414' for o in x['obligations'].values()))
x=read('abort-after-stop.json');check('actual accepted unresolved result canceled by run abort',any(r['stage']=='CANCELED_RUN_ABORT' and r['nativeRequest']==5 for r in x['lifecycle']))
check('stale future obligation cannot commit',read('restore-stale-work-and-prominence.json')['staleWork']['rejected'])
check('source-bound Gym prominence, diffusion unrun',read('restore-stale-work-and-prominence.json')['trustedProminence']['kind']=='gym' and not read('restore-stale-work-and-prominence.json')['trustedProminence']['diffusionExecuted'])
for path,sha in read('protected-before.json').items():check('protected unchanged '+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha)
for mode in ('external','vanilla'):check(mode+' final build/static scope',all(read('manifest-'+mode+'.json')['lifecycle_checks'].values()))
check('host tests passed',re.search(r'Ran 23 tests.*\n\nOK',(E/'final-host-tests.log').read_text(),re.S))
check('native terminal tests passed','7 actual-C terminal cases passed' in (E/'native-tests-final.log').read_text())
check('native legality/controller lifecycle passed','native legality and controller execution/lifecycle matrix passed' in (E/'native-tests-final.log').read_text())
ledger=json.loads((ROOT/'evidence/phase4/vertical_slice01/requests.json').read_text());check('closed immutable ledger remains 66',len(ledger['attempts'])==66 and ledger['closed'])
result={'ticket':'BATTLE-END-01','accepted':True,'hostedRequests':0,'checks':checks,'checkCount':len(checks),'VERTICAL_SLICE_01':'still blocked; no new live gate was run','emulatorRuns':len(runs),'lossNonce':3158766498,'vanillaLossNonce':3287450572,'victoryNonce':3029093765,'actualAbortedChoice':{'nonce':1365259495,'nativeRequest':5,'terminal':'CANCELED_RUN_ABORT'},'finalROM':{m:read('manifest-'+m+'.json')['rom_sha256'] for m in ('external','vanilla')}}
(E/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'accepted':True,'checks':len(checks),'hostedRequests':0}))

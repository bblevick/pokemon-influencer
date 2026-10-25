#!/usr/bin/env python3
"""Verify retained real BRIDGE-02 traces; never generates or mocks gameplay."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase1/bridge02'
def read(name):return json.loads((E/name).read_text())
def rows(name):return [json.loads(x) for x in (E/name).read_text().splitlines()]
manifest=read('manifest-enabled.json');checkpoint=read('checkpoint-final.json')
nonce=checkpoint['session'];sha=manifest['rom_sha256'];checks=[]
def check(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    assert condition,name
records=[x for x in rows('events.jsonl') if x['session']==nonce]
check('final ROM only',records and all(x['romSHA256']==sha for x in records))
check('checkpoint ROM binding',checkpoint['romSHA256']==sha)
emulator=rows('emulator.jsonl')
offset=next(i for i,x in enumerate(emulator) if x['event']=='build-validated' and x['detail']==sha)
emulator=emulator[offset:]
def sample(label):
    r=next(x for x in reversed(emulator) if x['event']=='sample' and x['detail'].startswith(label+' '))
    return r,{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',r['detail'])}
def complete_battle(run,kind):
    r=[x for x in records if x['run']==run and x['battleID']==1]
    check(kind+' start',r[0]['eventType']=='BATTLE_STARTED' and r[0]['payload']['battleKind']==kind)
    check(kind+' coherent full lifecycle',r[-1]['eventType']=='BATTLE_ENDED' and r[-1]['payload']['outcome']==1 and not any(x['streamIncomplete'] for x in r))
    check(kind+' selection, observation, action',[x['eventType'] for x in r].count('BATTLE_OBSERVATION')>0 and any(x['eventType']=='BATTLE_ACTION_RESOLVED' for x in r))
    check(kind+' strict capture order',all(b['sequence']==a['sequence']+1 and b['frameCounter']>=a['frameCounter'] for a,b in zip(r,r[1:])))
    return r
trainer=complete_battle(1,'trainer');wild=complete_battle(2,'wild')
check('Rick source identity 102',trainer[0]['payload']['trainerID']==102 and trainer[-2]['eventType']=='TRAINER_DEFEATED' and trainer[-2]['payload']=={'trainerID':102,'previouslyUndefeated':True,'outcome':1})
check('defeat immediately before end',trainer[-1]['sequence']==trainer[-2]['sequence']+1)
observations=[x for x in records if x['recordClass']=='observation']
revealed=set()
for r in trainer:
    if r['eventType']=='BATTLE_ACTION_RESOLVED' and r['payload']['actorSide']==0 and r['payload']['announcedMoveID']:revealed.add(r['payload']['announcedMoveID'])
    if r['eventType']=='BATTLE_OBSERVATION':check('observation '+str(r['sequence'])+' revealed only',set(r['payload']['opponentActive']['revealedMoveIDs'])<=revealed)
check('initial trainer observation has no player moves',trainer[2]['payload']['opponentActive']['revealedMoveIDs']==[])
check('closed opponent surface',all(set(x['payload']['opponentActive'])=={'revealedSpeciesID','publicHPBar','publicHPBarMax','revealedMoveIDs'} for x in observations))
check('no fabricated complete legal actions',all(x['payload']['legalActionsComplete'] is False for x in observations))
check('first public seed then Tackle',set().union(*(set(x['payload']['opponentActive']['revealedMoveIDs']) for x in observations))=={33,73})
check('canonical and observation sinks differ',all(x['recordClass']=='canonical_event' for x in rows('canonical-events.jsonl')) and all(x['recordClass']=='observation' for x in rows('observations.jsonl')))
check('no duplicate accepted identity',len({(x['session'],x['run'],x['sequence']) for x in records})==len(records))
def host_session(mode):
    result=[];current=None
    for x in rows('host-'+mode+'.jsonl'):
        if x['event']=='hello':current=x['session']
        if current==nonce:result.append(x)
    return result
drop=host_session('drop-ack-once');disconnect=host_session('disconnect-once');stale=host_session('stale-ack-once')
check('missed ACK causes duplicate receipt',any(x['event']=='fault-injected' and x['sequence']==1 for x in drop) and any(x['event']=='duplicate' and x['sequence']==1 for x in drop))
check('disconnect retry preserves run',any(x['event']=='fault-injected' and x['sequence']==1 for x in disconnect) and any(x['event']=='duplicate' and x['run']==2 for x in disconnect))
check('stale ACK rejected live',any(x['event']=='stale-response-rejected' and x['detail']=='32' for x in emulator) and any(x['event']=='duplicate' and x['run']==3 and x['sequence']==33 for x in stale))
check('absent host has no fabricated full history',len([x for x in records if x['run']==3])==2 and all(x['streamIncomplete'] for x in records if x['run']==3))
check('reconnect exposes 32-record gap',next(x for x in records if x['run']==3)['sequenceGap']==32)
_,first=sample('final-absent-search');_,last=sample('final-absent-flee')
check('battle advances during absence',last['heartbeat']>first['heartbeat'] and last['sequence']>first['sequence'] and first['successes']==0 and first['failures']>=9)
check('degraded gameplay then real victory',next(x for x in records if x['run']==3 and x['eventType']=='BATTLE_ENDED')['payload']['outcome']==1)
check('diagnostic drops and retries',any(x['event']=='events-diagnostics' and 'captured=34 drops=32 retries=65' in x['detail'] for x in emulator))
check('real in-game save callback',any(x['event']=='savedataUpdated' for x in emulator) and read('trainer-battery-save.json')['saveCounter']==4)
check('reload crosses heartbeat boundary',any(x['event']=='reload-test' for x in emulator) and any(x['event']=='disconnected' and x['detail']=='ROM reset detected' for x in emulator))
check('restored IDs separated by run',trainer[0]['sequence']==wild[0]['sequence']==1 and trainer[0]['branch']!=wild[0]['branch'])
reset=read('pending-reset.json')
check('live pending reset is final ROM',reset['romSHA256']==sha and reset['session']==nonce and 'state=1' in reset['before']['detail'] and 'sequence=1' in reset['before']['detail'])
check('reset clears native IDs', 'state=0' in reset['after']['detail'] and 'sequence=0' in reset['after']['detail'] and any(x['event']=='events-diagnostics' and x['detail']=='captured=0 drops=0 retries=0 depth=0 battle=0 turn=0' for x in emulator))
check('explicit callback advances run to 7',any(x['event']=='reset-epoch' and x['detail']=='7' for x in emulator))
_,post=sample('final-reset-continue')
check('post reset native Continue and authenticated run',post['generation']==7 and post['state']==0 and any(x['event']=='hello' and x['run']==7 for x in host_session('normal')))
probe=read('reconnect-probe.json')
check('16 authenticated reconnects preserve run',probe['passed'] and probe['connections']==16 and probe['session']==nonce and probe['romSHA256']==sha)
check('explicit GC exercised',any(x['event']=='socket-guard-GC' and x['detail']=='retired=20 inputs=73' for x in emulator))
check('no gameplay listener unknown-error disconnect',not any(x['event']=='disconnected' and 'unknown' in x['detail'].lower() for x in emulator))
screens=[]
for label in ['final-rick-field','final-wild-field','final-absent-search','final-absent-recovery','final-absent-flee','final-reset-continue']:
    p=ROOT/'evidence/private/bridge02'/ (label+'.png');check('retained screenshot '+label,p.is_file())
    screens.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'review':'visually reviewed during real scenario; assertions here verify retention only'})
result={'passed':True,'assertionCount':len(checks),'session':nonce,'romSHA256':sha,'finalAcceptedRecords':len(records),'trainerTurns':trainer[-1]['turnID'],'wildTurns':wild[-1]['turnID'],'checks':checks,'privateScreenshots':screens,'limitations':['Retained trace verifier does not run an emulator','Separate input socket failure retained in test-input-disconnect.json','Reset command reply timed out; reset was independently measured','No arbitrary rollback, durable branch/save pairing, full NPC knowledge store or inference claimed']}
(E/'emulator-integration.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['passed','assertionCount','session','romSHA256','finalAcceptedRecords']}))

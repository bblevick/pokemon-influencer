#!/usr/bin/env python3
"""Read-only closeout of retained incident and isolated continuity evidence.

No historical replay, campaign writes, provider loading or emulator input.
"""
import hashlib,json,sqlite3,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from bridge.events import decode_event
from bridge.events_wire import Message,checksum
from world.saves import fingerprint,layout_from_build
from phase1_events_build import symbols

E=ROOT/'evidence/phase8/rival01-travel-repair'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    preserved=read(E/'preserved-inventory.json')
    after={p:{'bytes':(ROOT/p).stat().st_size,'sha256':sha(ROOT/p)} for p in preserved}
    assert after==preserved,'protected incident or original Save20 changed'
    old=read(ROOT/'evidence/phase8/rival01/verification-blocked.json')
    base=read(ROOT/'evidence/phase8/rival01/r0-baseline.json')
    payload=bytes.fromhex(old['retainedNativePayloadHex'])
    m=Message(1,2493534040,1,298,2285031545,3,payload)
    assert checksum(m.sequence,m.nonce,m.generation,m.typ,payload)==old['retainedPayloadChecksum']
    with sqlite3.connect('file:'+str(ROOT/'.local/rival01/travel-gap-forensic.sqlite3')+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        launch=dict(db.execute('SELECT * FROM launches WHERE nonce=?',(m.nonce,)).fetchone())
        stream=dict(db.execute('SELECT * FROM streams WHERE nonce=? AND run=?',(m.nonce,m.generation)).fetchone())
        campaign=dict(db.execute('SELECT * FROM campaigns WHERE id=?',(launch['campaign'],)).fetchone())
        assert stream['last']==297 and campaign['status']=='incomplete' and campaign['cursor']==669
        assert not db.execute('SELECT 1 FROM deliveries WHERE launch=? AND sequence>=298',(launch['id'],)).fetchone()
    ledger=read(ROOT/'evidence/phase8/rival01/requests.json');assert ledger['closed'] and not ledger['attempts']
    trial=E/'trial3';before=read(trial/'before-fresh-restart.json');fresh=read(trial/'fresh-field-reloaded.json')
    assert before['hashes']==fresh['hashes'] and before['save']==fresh['save'] and before['checkpoint']==fresh['checkpoint']
    assert fresh['campaign']['status']=='paired' and fresh['pendingSave'] is None
    assert not [b for b in fresh['world']['battles'].values() if not b['ended']]
    fault=read(trial/'ack-loss-after-commit.json');wire=fault['wireHex'];deliveries=[json.loads(x) for x in (trial/'deliveries.jsonl').read_text().splitlines()]
    repeats=[d['result'] for d in deliveries if d['wireHex']==wire]
    assert [r['duplicate'] for r in repeats]==[False,True]
    assert len({r['eventID'] for r in repeats})==1
    expiry=read(trial/'timed-expiry.json');assert expiry['frozen'] and expiry['twoSecondsLater']['drops']==0
    context=read(E/'rollback-context-verification.json');assert context['fullStrategyContextBytes']<=8192 and context['privateRocketReceiptsExcluded']==47
    assert context['publicReceiptsRetained']==22 and context['strategyJobsUnchanged'] and not context['memoryDeleted']
    assert not read(ROOT/'config/model_profiles.yaml')['hosted_inference_enabled']
    proc=subprocess.run(['pgrep','-fl','rival01_travel_repair.py (host|input|save)|continuity_supervisor.py|^'+str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA')],capture_output=True,text=True)
    assert not proc.stdout.strip(),'task-owned native or host still running'
    tests=(E/'host-tests-final.log').read_text();assert 'Ran 39 tests' in tests and tests.rstrip().endswith('OK')
    native=read(E/'native-static-verification.json');assert native['actualHeadroom']==4
    manifest=read(E/'manifest-native.json');sizes=layout_from_build(ROOT/manifest['rom_path'])
    rom=ROOT/manifest['rom_path'];elf=rom.with_suffix('.elf')
    assert sha(rom)==manifest['rom_sha256']==native['romSHA256'] and sha(elf)==native['elfSHA256']
    ram=[v['address']+v['size'] for v in symbols(elf).values() if 0x02000000<=v['address']<0x02040000 and v['size']]
    assert max(ram)==0x0203fffc and 0x02040000-max(ram)==4
    battery=(ROOT/'.local/rival01/pokefirered.sav').read_bytes();sid=fingerprint(battery,sizes)
    assert sid.fingerprint==base['checkpoint']['fingerprint'] and sid.counter==20
    sections={}
    for index in range(sid.slot*14,sid.slot*14+14):
        sector=battery[index*4096:(index+1)*4096]
        section,_,_,counter=struct.unpack_from('<HHII',sector,4084)
        assert counter==sid.counter;sections[section]=sector[:sizes[section]]
    sb1=b''.join(sections[i] for i in range(1,5))
    rollback_flags={str(trainer):bool(sb1[0xEE0+(0x500+trainer)//8]&(1<<((0x500+trainer)%8))) for trainer in (91,120)}
    assert not any(rollback_flags.values()),'Save20 unexpectedly contains Josh/Miriam'
    proof=read(trial/'fresh-restart-verification.json')
    result={'ticket':'RIVAL-01 TRAVEL-CONTINUITY GATE REPAIR','date':'2026-10-08',
      'status':'RIVAL-01 TRAVEL RECOVERY BLOCKED — EXACT CONTINUATION UNPROVABLE',
      'accepted':False,'genericManagedRepairQualified':True,'historicalExactRecoveryPerformed':False,
      'historicalEvent':{'nonce':m.nonce,'generation':m.generation,'sequence':m.sequence,'physicalBuildTag':m.tag,
        'origin':launch['id'],'campaign':campaign['id'],'branch':campaign['active_branch'],'cursorBeforeGap':669,
        'battle':10,'phase':0,'type':'BATTLE_STARTED','kind':'wild','trainer':0,'nativeFrame':1952875,
        'checksum':old['retainedPayloadChecksum'],'checksumValid':True,'payloadHex':payload.hex(),'payloadSHA256':hashlib.sha256(payload).hexdigest(),
        'decoded':decode_event(m),'lastCommittedSequence':297,'canonicalEventID':None,
        'failureBoundary':'host lifetime expired before native emission/delivery; volatile native retry queue exhausted',
        'nativeCounterpartAvailable':False,'workingBatteryStillSave20':sid.as_dict(),
        'nativeRollbackTrainerDefeatedFlags':rollback_flags,
        'subsequentRetainedNativeEvents':0,'replayed':False},
      'historicalBranch':campaign,'joshMiriam':{'records':old['travelVictories'],'disposition':'preserved only on suspended abandoned future; not active after Save20 rollback'},
      'safeRollback':{'nativeSave':'.local/rocket01/post-rocket-pair.sav','hostDatabase':'.local/rocket01/post-rocket-pair.sqlite3',
        'checkpoint':base['checkpoint'],'projectionHashes':context['projectionHashesAtSave20'],'exactContinuation':False},
      'qualificationOnlyPair':{'checkpoint':fresh['checkpoint'],'save':fresh['save'],'hashes':fresh['hashes'],
        'sameAsHistoricalBranch':False,'approvedAsReplacementCampaign':False},
      'nativeProof':{'actualWildEncounter':'Zubat11','normalOutcome':'ordinary Run / outcome4','lostACKEventID':repeats[0]['eventID'],
        'sameWireRetransmitted':True,'deduplicated':True,'preRestartEventCounter':5,'preRestartACK':5,'preRestartDrops':0,
        'timedExpiry':expiry,'freshRestart':proof},
      'context':context,'constructor':'existing native source334/actor0326 Charmander four-party fixture; compatibility regression passes, no active Rival encounter',
      'tests':{'focusedHost':39,'skipped':0,'exitCode':0,'log':'host-tests-final.log','fixturesDistinguishedFromLive':True},
      'nativeStatic':native,'protectedBefore':preserved,'protectedAfter':after,'protectedUnchanged':True,
      'inference':{'newHostedCalls':0,'originalCallsUsed':0,'maximum':40,'roleLimits':ledger['roleLimits'],'ledgerClosed':True,'defaultEnabled':False},
      'shutdown':{'ownedHostEmulatorSupervisorStopped':True,'remainingProcesses':proc.stdout.strip()},
      'remainingRisks':['historical native RAM/state unavailable','supervised configuration required; unmanaged launchers unchanged',
        '1x local macOS SIGSTOP profile only; fast-forward and simultaneous guardian+writer death unqualified',
        'finite native queue is not a durable native event journal','full Josh/Miriam travel replay and Rival live acceptance deferred',
        'all future driver helpers must obey managed input lease; PI_TEST path qualified'],
      'nextTask':'Separately authorized rollback-based RIVAL-01 continuation from original accepted Save20 using the managed supervisor; no new milestone'}
    (E/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','genericManagedRepairQualified','protectedUnchanged']},ensure_ascii=False))
if __name__=='__main__':main()

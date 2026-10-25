#!/usr/bin/env python3
"""Checks actual retained BATTLE-01 evidence; never fabricates a live gate."""
import sys,json,hashlib,sqlite3,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from battle01_launch import open_store,save_identity,E,PRIVATE
from roster.extract import digest
checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def main():
 protected=json.loads((E/'protected-before.json').read_text());check('452 protected inputs unchanged',len(protected)==452 and all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()))
 m=json.loads((E/'manifest-native.json').read_text());check('actual final ROM hash',hashlib.sha256((ROOT/m['rom_path']).read_bytes()).hexdigest()==m['rom_sha256'])
 check('48-byte named control and four-byte headroom',m['battle_control']['size']==48 and m['preparation_checks']['priorRAMSymbolsUnchanged'])
 check('actual ARM ABI',m['battle_abi']==[708,1036,48,16,52,340,452,708,1024])
 rows=list(map(json.loads,(E/'battle-audit.jsonl').read_text().splitlines()));term=[r for r in rows if r['event']=='native-terminal'];accepted={384821213,2594744355,2521941790};term=[r for r in term if r['session'] in accepted]
 check('one receipt per qualified decision',len({(r['session'],r['generation'],r['nativeRequest']) for r in term})==len(term))
 switch=next(r for r in term if r['session']==384821213 and r['nativeRequest']==1);check('live external switch',switch['nativeSelected']==513 and switch['source']=='external_test')
 history=json.loads((E/'turn-384821213-3.json').read_text())['nativeState']['history'];check('native resolved voluntary switch chronology',any(r['side']==1 and r['nativeActionKind']==12 and r['species']==10 for r in history))
 check('live sole forced replacement without provider',any(r['session']==384821213 and r['phase']==2 and r['source']=='engine_forced' and r['nativeSelected']==1024 for r in term))
 check('live delayed provider native timeout',any(r['session']==2594744355 and r['source']=='vanilla_fallback' and r['fallbackReason']==2 for r in term))
 check('late provider discarded',any(r['event']=='selection-timeout' and r['request']['nativeState']['nonce']==2594744355 for r in rows))
 packets=[json.loads(p.read_text()) for n in accepted for p in E.glob('turn-'+str(n)+'-*.json')];check('production Rick item stock zero',packets and all(not any(p['nativeState']['inventory']) and not any(':ITEM:' in c for c in p['choices']) for p in packets))
 check('fixed choices are complete one-to-one',all(set(p['choices'])==set(p['nativeActions']) and len(p['choices'])==len(p['nativeState']['actions']) for p in packets))
 latency=[r['hostLatencySeconds'] for r in rows if r['event']=='selection' and r['request']['nativeState']['nonce'] in accepted and r.get('source')=='external_test']
 heap=[r for r in map(json.loads,(E/'emulator.jsonl').read_text().splitlines()) if r['event']=='battle-heap'];check('actual heap allocated and freed',any('bytes=1036' in r['detail'] for r in heap) and any(r['detail']=='pointer=0 bytes=0' for r in heap))
 with open_store(PRIVATE/'world.sqlite3') as w:
  lock=w.locked_preparation('trainer:fr:trainer:0102');check('D33 commitment retained',lock['commitmentID']=='commitment:5952b1d593eb7d6e9661872cb6a5b7c7d86ccbb3a415480410d3781fb6d2e8dc')
  check('exact frozen subjective memo',all(lock['strategyText'] in p['state'] and p['strategySHA256']==hashlib.sha256(lock['strategyText'].encode()).hexdigest() for p in packets))
  events=[json.loads(r['record']) for r in w.db.execute('SELECT record FROM events')];events=[r for r in events if r['session']==2521941790]
  check('real selected Poison Sting resolves',any(r['eventType']=='BATTLE_ACTION_RESOLVED' and r['payload'].get('actorSide')==1 and r['payload'].get('announcedMoveID')==40 for r in events))
  selected=[r for r in term if r['session']==2521941790 and r['source']=='external_test'];check('all five external moves agree with resolved announcements',len(selected)==5 and all(r['nativeSelected']==256 and any(e['turnID']==r['turn'] and e['eventType']=='BATTLE_ACTION_RESOLVED' and e['payload'].get('actorSide')==1 and e['payload'].get('announcedMoveID')==40 for e in events) for r in selected))
  ended=next((r for r in events if r['eventType']=='BATTLE_ENDED'),None);check('full normal battle ended (player lost)',ended and ended['payload']['outcome']==2 and not ended['streamIncomplete'])
  job=w._one('SELECT * FROM puppeteer_jobs ORDER BY rowid DESC LIMIT 1');out=json.loads(job['outcome']);check('mandatory recap recovered offline',job['status']=='completed' and out['producer']=='deterministic_fallback' and out['model'] is None and out['postID'] in w.social_state()['posts'])
  full=w.battle_audit();check('five battle audits survive paired Save20 restore',len(full)==5 and {r['session'] for r in full}=={2521941790})
  state={'world':w.verify_replay(),'memory':w.verify_memory_replay(),'social':w.verify_social_replay(),'puppeteer':w.verify_puppeteer_replay(),'audit':digest(full)}
  save=save_identity(PRIVATE/'completed-save20.sav');cp=w.get_save_checkpoint(save.fingerprint);check('actual normal Save20 paired',save.counter==20 and cp['kind']=='normal_save' and cp['cursor']==179)
  with tempfile.TemporaryDirectory() as td:
   db=Path(td)/'w.sqlite3';b=sqlite3.connect(db);w.db.backup(b);b.close()
   with open_store(db) as copy:
    copy.restore(save);check('fresh SQLite reload preserves full audit',copy.battle_audit()==full)
    copy.restore(save_identity(ROOT/'.local/system1_01a/installed-save19.sav'));check('Save19 excludes future audit and post',copy.battle_audit()==[] and out['postID'] not in copy.social_state()['posts'])
 report={'checks':checks,'checkCount':len(checks),'modelsCalled':0,'acceptedSessions':sorted(accepted),'excludedTrials':'v1 oversized context; v2 premature terminal publication; incomplete trial continuations are not full completion proof','romSHA256':m['rom_sha256'],'elfSHA256':m['elf_sha256'],'hostDecisionLatencySeconds':{'min':min(latency),'max':max(latency),'count':len(latency),'meaning':'completed native snapshot to deterministic result publication on host; excludes later battle text/animation'},'fullBattleSession':2521941790,'fullBattleOutcome':'player lost, trainer won; normal outcome2','pairedCheckpoint':cp,'pipelineOutcome':out,'replaySHA256':state,'memory':{'fixedControlBytes':48,'reservedHeadroomBytes':4,'snapshotBytes':708,'workPayloadBytes':1036,'priorRAMSymbolsUnchanged':True},'limitations':['actual-C item/replacement fixtures capture native controller emissions; item animations/HP effects not an emulator proof','no live model latency or fast-forward model qualification','only armed D33 Rick ordinary singles; campaign/rematch UX and other formats deferred','arbitrary savestates not supported']}
 (E/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':len(checks),'modelsCalled':0,'romSHA256':m['rom_sha256']},indent=2))
if __name__=='__main__':main()

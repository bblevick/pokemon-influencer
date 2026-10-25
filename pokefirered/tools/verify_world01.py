#!/usr/bin/env python3
"""Verify retained real WORLD acceptance. Does not play or mock the emulator."""
import json,hashlib,re,sys,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from world.store import WorldStore,dump
from world01 import manifest,save_identity
E=ROOT/'evidence/phase2/world01'
def load(name):return json.loads((E/name).read_text())
def rows(name):return [json.loads(x) for x in (E/name).read_text().splitlines()]
checks={}
def check(name,value):checks[name]=bool(value)
def main():
 m=manifest();check('unchanged_final_B3_ROM',m['rom_sha256']=='739bd3eebb91aaa5210f8f8cd1f357a8272dc98db7060356c649b4c38a0dbc2d');check('EWRAM_224_unchanged',m['ewram_remaining']==224)
 for path,sha in m['overlay_sha256'].items():check('accepted_source_'+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha)
 seed=load('seed-fingerprint.json');s1=load('S1-fingerprint.json');s2=load('S2-fingerprint.json');restarted=load('S1-after-fresh-continue-fingerprint.json')
 check('real_S1_S2_counters_and_slots',(seed['counter'],s1['counter'],s2['counter'],s1['slot'],s2['slot'])==(4,5,6,1,0))
 check('real_S1_S2_distinct',s1['fingerprint']!=s2['fingerprint']);check('real_S1_restart_stable',s1['fingerprint']==restarted['fingerprint'])
 pairings=rows('pairings.jsonl');check('three_actual_normal_save_pairs',len(pairings)==3 and [p['checkpoint']['cursor'] for p in pairings]==[0,36,36])
 for i,p in enumerate(pairings):
  r=p['receipt'];check('save_receipt_'+str(i),r['event']=='savedataUpdated' and r['state']==r['depth']==r['drops']==0 and r['eventCounter']==r['ack']==[0,47,0][i])
 reopen=load('host-reopen.json');check('real_Rick_once_after_reopen',reopen['state']['trainers']['fr:trainer:0102']['defeats']==1 and reopen['state']['trainers']['fr:trainer:0102']['completedBattles']==1);check('actual_duplicate_delivery_no_change',reopen['duplicate']['duplicate'] and reopen['identicalAfterDuplicate'])
 restored=load('S1-restored-before-play.json');check('old_save_zero_active_future',restored['state']['cursor']==0 and restored['state']['trainers']=={} and restored['campaign']['pending_fork']==1)
 reconnected=load('S1-reconnected-state.json');check('reconnect_does_not_fork',reconnected['campaign']==restored['campaign'])
 fork=load('managed-restore-and-fork.json');check('distinct_branch_on_canonical_start',fork['branchA']!=fork['branchB'] and fork['branchBEvents'][0]['record']['eventType']=='BATTLE_STARTED');check('inactive_original_history_retained',fork['branchAEvents']==37 and fork['retainedRickDefeats']==1);check('no_Rick_in_divergent_active_world',fork['activeState']['trainers']=={})
 for name in ['rick-replay-db.json','rick-replay-fixture.json','branch-A-replay.json','branch-B-replay-db.json','branch-B-replay-fixture.json']:check(name,load(name)['passed'])
 check('db_fixture_Rick_replay_equivalent',load('rick-replay-db.json')['stateSHA256']==load('rick-replay-fixture.json')['stateSHA256']);check('db_fixture_branch_replay_equivalent',load('branch-B-replay-db.json')['stateSHA256']==load('branch-B-replay-fixture.json')['stateSHA256'])
 host=rows('host.jsonl');check('actual_clean_host_restart_identical',sum(x['event']=='host-close' and x.get('stateSHA256')==reopen['stateSHA256'] for x in host)>=1 and sum(x['event']=='host-open' and x.get('stateSHA256')==reopen['stateSHA256'] for x in host)>=2)
 emu=rows('emulator.jsonl');details=[x['detail'] for x in emu if x['event']=='persist'];check('native_S1_fresh_field',any('counter=5 partycount=1 level=7 hp=24 x=42 y=46' in d for d in details));check('absent_host_full_tile_motion',any('counter=5 partycount=1 level=7 hp=24 x=43 y=46' in d for d in details))
 final=load('S2-after-fresh-continue.json');check('Rick_identity_after_emulator_restart',final['state']['trainers']['fr:trainer:0102']['defeats']==1 and final['campaign']['cursor']==36);check('real_S2_restart_stable',s2['fingerprint']==final['save']['fingerprint'])
 check('final_host_113',bool(re.search(r'Ran 113 tests.*\n\nOK', (E/'final-host-regression.log').read_text(),re.S)));check('existing_regressions_passed',load('regressions/results.json')['passed'])
 with WorldStore(ROOT/'.local/world01/world.sqlite3',m['rom_sha256'],m['build_tag']) as w:
  check('live_final_replay',w.verify_replay()==hashlib.sha256(dump(w.state()).encode()).hexdigest());check('two_branches_retained',w.db.execute('SELECT COUNT(*) FROM branches').fetchone()[0]==2);check('schema_and_reducer_1',w.db.execute('PRAGMA user_version').fetchone()[0]==1 and w.state()['reducerVersion']==1)
  a=fork['branchA'];b=fork['branchB'];check('historical_branches_inspectable',len(w.get_canonical_events(a))==37 and len(w.get_canonical_events(b))>=1)
 images=['s1-save-writing','rick-reviewed-finish-11','s2-complete','s1-confirmed-field','s1-absent-right-confirmed','s1-absent-left-confirmed','s2-positive-field']
 for name in images:check('actual_capture_'+name,(ROOT/'evidence/private/world01'/f'{name}.png').is_file())
 report={'scope':'retained real final-ROM native battles/normal saves/fresh-process restore, SQLite state and regressions; not new execution','passed':all(checks.values()),'assertions':len(checks),'checks':checks,'romSHA256':m['rom_sha256'],'schemaVersion':1,'reducerVersion':1,'fingerprintAlgorithm':'fr-save-v1','campaignID':fork['campaign']['id'],'branchIDs':[fork['branchA'],fork['branchB']]}
 (E/'emulator-integration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()

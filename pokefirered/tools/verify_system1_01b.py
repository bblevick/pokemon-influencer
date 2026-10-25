#!/usr/bin/env python3
"""Verify actual SYSTEM1-01B shadow/native/pair evidence; no inference."""
import sys,json,hashlib,sqlite3,tempfile,statistics,jsonschema
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from system1_01b_launch import E,PRIVATE,SCREENS,open_store,save_identity
from roster.hashes import digest,file_hash
from system1_01a_verify_party import decode as decode_mon
from system1.validation import validate_decision
SHADOW=1660475733;ENABLED=3468328694
checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def stats(values):
 return {'count':len(values),'min':min(values),'median':statistics.median(values),'max':max(values),'p90':None,'p95':None,'percentiles':'not estimated with fewer than20 samples'}
def main():
 protected=json.loads((E/'protected-before.json').read_text());check('524 protected inputs unchanged',len(protected)==524 and all(file_hash(ROOT/p)==h for p,h in protected.items()))
 m=json.loads((ROOT/'evidence/phase4/battle01/manifest-native.json').read_text());check('native ROM and ELF unchanged',file_hash(ROOT/m['rom_path'])==m['rom_sha256'] and file_hash((ROOT/m['rom_path']).with_suffix('.elf'))==m['elf_sha256'])
 budget=json.loads((E/'requests.json').read_text());attempts=budget['attempts'];check('one closed ledger13 of30 incl errors/smoke',budget['closed'] and budget['maximumAttempts']==30 and len(attempts)==13 and len({a['jobID'] for a in attempts})==13)
 check('Mercury only',all(a['requestedModel']=='inception/mercury-decide:free' for a in attempts))
 responses=[a['response'] for a in attempts if 'response' in a];check('ten returned responses zero reported cost',len(responses)==10 and all(r['httpStatus']==200 and r['result']['usage']['cost']==0 and r['result']['provider']=='Inception' for r in responses))
 check('three interrupted attempts retained, no invented cost',sum('retrospectiveErrorEvidence' in a and 'response' not in a for a in attempts)==3)
 gate=json.loads((E/'shadow-accepted.json').read_text());check('actual full shadow precedes enabled',gate['passed'] and gate['session']==SHADOW and gate['totalLedgerAtGate']==9 and gate['timeoutCount']==0)
 rows=list(map(json.loads,(E/'battle-audit.jsonl').read_text().splitlines()));allterm=[r for r in rows if r['event']=='native-terminal'];term={n:[r for r in allterm if r['session']==n] for n in (SHADOW,ENABLED)}
 check('unique five native receipts each',all(len(t)==5 and len({r['nativeRequest'] for r in t})==5 for t in term.values()))
 shadow=[r for r in term[SHADOW] if r['selection']];enabled=[r for r in term[ENABLED] if r['selection']]
 check('four shadow proposals never executed',len(shadow)==4 and all(r['source']=='vanilla_fallback' and r['selection']['source']=='mercury_shadow' for r in shadow))
 check('four enabled decisions all actual Mercury, no fallback',len(enabled)==4 and all(r['source']=='mercury' and r['fallbackReason']==0 and r['nativeSelected']==r['selection']['nativeSelected'] for r in enabled))
 check('sole replacement native only in both',all(any(r['source']=='engine_forced' and r['phase']==2 and r['selection'] is None for r in t) for t in term.values()))
 selections=shadow+enabled;packets=[r['selection']['request'] for r in selections];qualifiedlat=[]
 for r in selections:
  p=r['selection']['request'];result=r['selection']['result'];validate_decision(result,p['choices']);assert r['selection']['nativeSelected']==p['nativeActions'][result['choiceID']]
  job='battle:'+hashlib.sha256(json.dumps([p['state'],p['question'],p['choices']],sort_keys=True).encode()).hexdigest();a=next(a for a in attempts if a['jobID']==job)
  body={'model':a['requestedModel'],'state':p['state'],'questions':{'preparation':{'type':'choice','instructions':p['question'],'criteria':p['choices']}}};assert a['requestSHA256']==digest(body)==result['diagnostics']['requestSHA256'];assert a['response']['result']['answers']['preparation']['choice']==result['choiceID'];qualifiedlat.append(a['response']['latencySeconds'])
 check('all eight exact POST state/choice hashes and probabilities validated',len(selections)==8)
 schema=json.loads((ROOT/'schemas/battle/request.schema.json').read_text());resolver=jsonschema.RefResolver((ROOT/'schemas/battle/').as_uri()+'/',schema)
 for r in selections:
  jsonschema.validate(r['selection']['request'],schema,resolver=resolver)
  jsonschema.validate(r['selection']['result'],json.loads((ROOT/'schemas/battle/result.schema.json').read_text()))
 check('eight actual request and result pairs satisfy current schemas',True)
 check('complete authoritative choice mapping',all(set(p['choices'])==set(p['nativeActions']) and len(p['choices'])==len(p['nativeState']['actions']) for p in packets))
 check('zero item stock and no item choices',all(not any(p['nativeState']['inventory']) and all(not o['heldItem'] for o in p['nativeState']['own']) and not any(':ITEM:' in k for k in p['choices']) for p in packets))
 check('visible opponent fields only',all(set(p['nativeState']['opponent'])=={'species','hpBar','status','revealedMoves'} for p in packets))
 check('bounded evolving resolved chronology',all(len(p['nativeState']['history'])<=16 for p in packets) and all(any(p['nativeState']['nonce']==n and p['nativeState']['turn']>1 and p['nativeState']['history'] for p in packets) for n in (SHADOW,ENABLED)))
 before=json.loads((E/'persistence-before.json').read_text());after=json.loads((E/'fresh-reload.json').read_text());check('fresh native Continue/host exact pair, no new requests',before['requestCount']==13 and all(before[k]==after[k] for k in ('save','checkpoint','audit','auditSHA256','replays','commitment','strategySHA256','requestCount')))
 with open_store(PRIVATE/'world.sqlite3') as w:
  lock=w.locked_preparation('trainer:fr:trainer:0102');check('D33 commitment and exact subjective memo unchanged',lock['commitmentID']=='commitment:5952b1d593eb7d6e9661872cb6a5b7c7d86ccbb3a415480410d3781fb6d2e8dc' and all(p['commitmentID']==lock['commitmentID'] and lock['strategyText'] in p['state'] and p['strategySHA256']==hashlib.sha256(lock['strategyText'].encode()).hexdigest() for p in packets))
  expected=[next(o for o in lock['candidate']['party'] if o['lineage']==lineage) for lineage in lock['candidate']['order']]
  check('all live own rosters match locked species/levels/moves/items',all([{k:o[k] for k in ('species','level','moves','heldItem')} for o in p['nativeState']['own']]==[{k:o[k] for k in ('species','level','moves','heldItem')} for o in expected] for p in packets))
  raw=json.loads((SCREENS/'native-party-private.json').read_text());decoded=[decode_mon(o) for o in raw['party']];check('actual enabled constructor once, checksum and party match',raw['nonce']==ENABLED and raw['nativeConstructorCount']==1 and [r[0] for r in decoded]==[{k:o[k] for k in ('species','level','moves','heldItem')} for o in expected])
  old=json.loads((ROOT/'evidence/phase3/system1_01a/native-installation.json').read_text());check('original personality/PP identity preserved at construction',[r[2] for r in decoded]==old['personalities'] and [r[1] for r in decoded]==old['partyPP'])
  events=[json.loads(r['record']) for r in w.db.execute('SELECT record FROM events')]
  ends={n:next(e for e in events if e['session']==n and e['eventType']=='BATTLE_ENDED') for n in (SHADOW,ENABLED)};check('both complete normal battles, no stream gap',all(e['payload']['outcome']==1 and not e['streamIncomplete'] for e in ends.values()))
  current=[e for e in events if e['session']==ENABLED]
  check('selected String Shot actually announces on turn1',any(e['eventType']=='BATTLE_ACTION_RESOLVED' and e['turnID']==1 and e['payload'].get('actorSide')==1 and e['payload'].get('announcedMoveID')==81 for e in current))
  check('Mercury switch selected513, resolved native history to Caterpie',any(r['turn']==2 and r['nativeSelected']==513 for r in enabled) and any(h['side']==1 and h['nativeActionKind']==12 and h['species']==10 for p in packets if p['nativeState']['nonce']==ENABLED for h in p['nativeState']['history']))
  check('native switch updates active slot, HP and PP in next request',any(p['nativeState']['nonce']==ENABLED and p['nativeState']['turn']==3 and p['nativeState']['activeSlot']==1 and p['nativeState']['own'][0]['hp']==6 and p['nativeState']['own'][0]['pp'][1]==39 and p['nativeState']['own'][1]['hp']==9 for p in packets))
  check('later faint interruptions distinguished from move announcements',all(any(e['eventType']=='BATTLE_ACTION_RESOLVED' and e['turnID']==t and e['payload'].get('actorSide')==1 and e['payload'].get('announcedMoveID')==0 for e in current) for t in (3,4)))
  job=w._one('SELECT * FROM puppeteer_jobs ORDER BY rowid DESC LIMIT 1');out=json.loads(job['outcome']);check('postbattle mandatory offline recap committed',job['status']=='completed' and out['producer']=='deterministic_fallback' and out['model'] is None and out['postID'] in w.social_state()['posts'])
  full=w.battle_audit();check('enabled five receipts survive pair, abandoned shadows excluded',len(full)==5 and {r['session'] for r in full}=={ENABLED})
  save=save_identity(PRIVATE/'completed-enabled-save20.sav');cp=w.get_save_checkpoint(save.fingerprint);check('actual enabled normal Save20 paired',save.counter==20 and cp['kind']=='normal_save' and cp['cursor']==177)
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'world.sqlite3';db=sqlite3.connect(path);w.db.backup(db);db.close()
   with open_store(path) as copy:
    copy.restore(save);check('fresh SQLite restores exact enabled audit',copy.battle_audit()==full)
    copy.restore(save_identity(ROOT/'.local/system1_01a/installed-save19.sav'));check('Save19 excludes future enabled audit and recap',copy.battle_audit()==[] and out['postID'] not in copy.social_state()['posts'])
  trace=[]
  for n,t in term.items():
   for r in t:
    s=r['selection'];p=s['request'] if s else None
    trace.append({'session':n,'turn':r['turn'],'phase':r['phase'],'nativeRequest':r['nativeRequest'],'source':r['source'],'nativeSelected':r['nativeSelected'],'fallbackReason':r['fallbackReason'],'actionSetHash':r['nativeHash'],'strategySHA256':p['strategySHA256'] if p else None,'stateSHA256':hashlib.sha256(p['state'].encode()).hexdigest() if p else None,'legalChoices':p['choices'] if p else None,'modelDecision':s['result'] if s else None,'hostLatencySeconds':s['hostLatencySeconds'] if s else None,'ownState':p['nativeState']['own'] if p else None,'visibleOpponent':p['nativeState']['opponent'] if p else None,'history':p['nativeState']['history'] if p else None,'resolvedCanonicalActions':[e['payload'] for e in events if e['session']==n and e['eventType']=='BATTLE_ACTION_RESOLVED' and e['turnID']==r['turn']]})
 config=json.loads((ROOT/'config/model_profiles.yaml').read_text());check('normal hosted default disabled',config['default_profile']=='offline' and not config['hosted_inference_enabled'])
 report={'ticket':'SYSTEM1-01B','accepted':True,'scope':'controlled locked Rick ordinary singles, normal speed only','checks':checks,'checkCount':len(checks),'protectedInputCount':len(protected),'requestCount':13,'hostedBattleAttempts':12,'syntheticSmokeAttempts':1,'returnedReportedCostUSD':0,'interruptedResponseCost':'unknown; three attempts returned no usage, qualified free routes only','shadowSession':SHADOW,'enabledSession':ENABLED,'battleEnds':ends,'checkpoint':cp,'pipelineOutcome':out,'romSHA256':m['rom_sha256'],'elfSHA256':m['elf_sha256'],'latency':{'qualifiedShadowAndEnabledHTTP':stats(qualifiedlat),'qualifiedHost':stats([r['selection']['hostLatencySeconds'] for r in selections]),'allReturnedBattleHTTP':stats([r['latencySeconds'] for r in responses if r['result']['usage']['input_tokens']>107]),'HTTPDeadlineMisses':2,'abortedTrialHardWorkerDeadlineMisses':1,'bounds':{'HTTP':2.35,'worker':2.55,'host':2.75,'nativeHeartbeatFrames':180},'smokeSeconds':.532},'trace':trace,'exclusions':['Initial hard-deadline/gap trial and early-trigger/configuration-label failures excluded; prior first full shadow is retained as failed latency qualification','Nonzero items/multiple replacements remain source/controller fixtures, not new live model execution','Fast-forward, arbitrary savestates, other trainers/modes, rematch UX, general installations and endgame not qualified']}
 (E/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checksPassed':len(checks),'accepted':True,'requests':13,'protectedInputs':len(protected)},indent=2))
if __name__=='__main__':main()

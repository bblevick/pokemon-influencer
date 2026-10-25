#!/usr/bin/env python3
"""Verify actual scoped closeout attempts; never grant a missing victory gate."""
import json,sys,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from roster.extract import digest
from vertical_slice01_host import E,PRIVATE,open_store

def main():
 read=lambda name:json.loads((E/(name+'.json')).read_text())
 checks=[]
 def check(label,value):
  if not value:raise AssertionError(label)
  checks.append(label)
 ledger=read('requests');original=read('requests-original30');base=read('closeout-gym-ready');clean=read('gate-final-clean')
 new=ledger['attempts'][30:]
 check('exact immutable original thirty',ledger['attempts'][:30]==original['attempts'])
 check('closed explicit maximum70 authorization',ledger['closed'] and ledger['maximumAttempts']==70 and ledger['gymCloseoutAuthorization']['baseAttempts']==30)
 check('36 additional battle and no additional other role',len(new)==36 and all(a['role']=='battle' for a in new))
 check('all66 receipts report zero cost',len(ledger['attempts'])==66 and all(a['outcome']['usage']['cost']==0 for a in ledger['attempts']))
 check('new requests are configured verified-free Mercury only',all(a['verifiedFree'] and a['requestedModel']=='inception/mercury-decide:free' and a['response']['httpStatus']==200 for a in new))
 check('new request audit identities are scoped Brock',all(a['scope']['trainerID']==414 and a['scope']['campaign']==base['campaign']['id'] and a['scope']['strategyID']==base['memos'][0]['strategyID'] for a in new))
 check('final clean restore exact seven hashes',clean['hashes']==base['hashes'])
 check('exact memo and lock unchanged',clean['memos']==base['memos'] and clean['decisions']==base['decisions'])
 check('no active failed Brock battle observation post or installation',not any(b['sourceTrainerID']==414 for b in clean['world']['battles'].values()) and not clean['decisions']['installations'] and not any(e['actorID']=='trainer:fr:trainer:0414' for e in clean['puppeteer']['episodes'].values()))
 check('clean restore retains no Boulder flags',not any(clean['boulder']['flags'].values()))
 check('downstream Sally has no abandoned Gym claims',not clean['sally']['reportedClaims'])
 rows=[json.loads(x) for x in (E/'battle-audit.jsonl').read_text().splitlines()]
 trace=[];attempts=[];latencies=[]
 cfg=json.loads((PRIVATE/'launch.json').read_text())
 with open_store(cfg['database']) as w:
  audit=w.battle_audit();paired=w._one('SELECT * FROM battle_audit_checkpoints WHERE checkpoint=?',(base['checkpoint']['id'],));view=w._one('SELECT * FROM battle_audit_view')
  check('final branch-visible tactical audit equals exact paired prebattle cutoff',view['cutoff']==paired['cutoff'] and digest(audit)==paired['state_sha'])
  check('no abandoned Brock tactical audit enters restored view',not any(r.get('session') in (3723204433,1081538346,408621241,2105259716,2834676294) for r in audit))
  (E/'gate-restored-audit.json').write_text(json.dumps({'checkpoint':dict(paired),'activeView':dict(view),'visibleRecords':audit,'visibleSHA256':digest(audit)},indent=2)+'\n')
  for i in range(1,5):
   before=read('gate-prebattle-restored' if i==1 else f'gate-attempt{i}-prebattle')
   after=read('gate-attempt4-budget-reached' if i==4 else f'gate-attempt{i}-result')
   check(f'attempt{i} starts at exact paired prebattle cutoff',before['hashes']==base['hashes'] and before['memos']==base['memos'] and before['decisions']==base['decisions'])
   check(f'attempt{i} preserved memo and commitment',after['memos']==base['memos'] and after['decisions']['commitments']==base['decisions']['commitments'])
   native=next(iter(after['decisions']['installations'].values()))['receipt'];nonce=native['nonce']
   check(f'attempt{i} source-authored constructor once',native['nativeConstructorCount']==1 and native['party']==[{'heldItem':0,'level':12,'moves':[33,111,0,0],'species':74},{'heldItem':0,'level':14,'moves':[33,20,317,0],'species':95}])
   selections=[r for r in rows if r['event']=='selection' and r['request']['nativeState']['nonce']==nonce]
   terminals=[r for r in rows if r['event']=='native-terminal' and r.get('session')==nonce]
   check(f'attempt{i} all provider results legal and exact subjective memo',all(r['source']=='mercury' and r['result']['choiceID'] in r['request']['choices'] and base['memos'][0]['strategyText'] in r['request']['state'] for r in selections))
   check(f'attempt{i} native accepted every supplied selection without fallback',len(terminals)==len(selections) and all(t['source']=='mercury' and t['fallbackReason']==0 for t in terminals))
   events=w.get_canonical_events(after['campaign']['active_branch'],after['world']['cursor'])
   events=[e for e in events if e['record']['session']==nonce]
   battle=next(b for b in after['world']['battles'].values() if b['sourceTrainerID']==414)
   expected=(4,6,14,12)[i-1]
   check(f'attempt{i} actual bounded decision count',len(selections)==expected)
   if i<4:check(f'attempt{i} correctly retained as uncompleted, no invented result',not battle['ended'] and battle.get('outcome') is None and not any(e['record']['eventType']=='BATTLE_ENDED' for e in events))
   else:check('fourth attempt unfinished at role exhaustion, no invented outcome',not battle['ended'] and not any(e['record']['eventType']=='BATTLE_ENDED' for e in events))
   attempts.append({'attempt':i,'branch':after['campaign']['active_branch'],'nonce':nonce,'battleID':battle['battleID'],'liveModelChoices':len(selections),'fullyLiveCompleted':battle['ended'],'outcome':battle.get('outcome'),'gateQualified':False,'reason':'sole player Pokemon visibly fainted; restored before canonical battle-end receipt' if i<4 else 'role_budget_exhausted_at_pending_turn12','sourceSnapshot':'gate-attempt4-budget-reached.json' if i==4 else f'gate-attempt{i}-result.json'})
   for s in selections:
    p=s['request'];n=p['nativeState'];resolved=[e for e in events if e['record']['turnID']==n['turn'] and e['record']['eventType']=='BATTLE_ACTION_RESOLVED' and e['record']['payload']['actorSide']==1]
    terminal=next(t for t in terminals if t['turn']==n['turn'])
    check(f'accepted action identity {i}/{n["turn"]}',terminal['nativeSelected']==s['nativeSelected'])
    latencies.append(s['hostLatencySeconds'])
    trace.append({'attempt':i,'branch':after['campaign']['active_branch'],'turn':n['turn'],'phase':n['phase'],'fairState':n,'authorizedStateAndSubjectiveMemo':p['state'],'legalChoices':p['choices'],'modelResult':s['result'],'hostLatencySeconds':s['hostLatencySeconds'],'nativeAcceptance':{k:v for k,v in terminal.items() if k!='selection'},'actualResolutionEvents':resolved,'resolutionStatus':'native_resolution_recorded' if resolved else 'accepted_pending_player_choice_at_shutdown','interpretationLimit':'No invented model rationale. Actual native announcements distinguish selected actions from pending/interrupted execution.'})
 check('35 choices have actual resolution; final charged accepted turn12 unrun',sum(bool(t['actualResolutionEvents']) for t in trace)==35 and trace[-1]['resolutionStatus']=='accepted_pending_player_choice_at_shutdown')
 out={'ticket':'VERTICAL-SLICE-01','status':'STILL BLOCKED','accepted':False,'passedEvidenceChecks':len(checks),'checks':checks,'originalRequests':30,'additionalRequests':36,'totalHistoricalRequests':66,'additionalMercury':36,'additionalHermes':0,'additionalStrategy':0,'additionalPreparation':0,'reservedHermesUnused':4,'totalReportedCostUSD':0,'attempts':attempts,'hostLatencyMedianSeconds':statistics.median(latencies),'hostLatencyMaxSeconds':max(latencies),'prebattleCheckpoint':base['checkpoint']['id'],'activeRestoredBranch':clean['campaign']['active_branch'],'missingGates':['fully live player victory and native Boulder progression','successful battle mandatory Hermes recap and high-profile downstream propagation','native PokeBook over that successful timeline','new successful normal save and fresh reload'],'stopReason':'additional36 Mercury role allowance exhausted; reserved4 Hermes calls require a successful fully-live victory and cannot be diverted'}
 (E/'gate-verification.json').write_text(json.dumps(out,indent=2)+'\n')
 (E/'gate-turn-traces.json').write_text(json.dumps({'successfulTrace':None,'status':'failure and incomplete attempt evidence only','turns':trace},indent=2)+'\n')
 print(json.dumps({k:v for k,v in out.items() if k not in ('checks','attempts')}))

if __name__=='__main__':main()

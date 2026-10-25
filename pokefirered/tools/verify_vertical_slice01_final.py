#!/usr/bin/env python3
"""Actual-artifact acceptance only. Never infer, publish, or mutate game state."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from vertical_slice01_host import E
BROCK='trainer:fr:trainer:0414';RICK_POST='11e722419022a5e2dc016ab285df168642f3a742a7456f181e9e24580d37c6fa'
def verify():
 def read(n):return json.loads((E/(n+'.json')).read_text())
 d=read('final-success');pre=read('final-pre-brock');restored=read('final-restored-success');rollback=read('final-restored-prefix');trace=read('final-turn-trace');gold=read('final-golden-trace');ledger=read('requests');old=read('final-original66')
 checks=[];gates=[]
 def check(name,condition,gate=None):
  checks.append({'name':name,'passed':bool(condition),'gate':gate})
  if gate:gates.append({'id':gate,'name':name,'passed':bool(condition)})
 battles=[b for b in d['world']['battles'].values() if b['sourceTrainerID']==414];b=battles[0] if len(battles)==1 else {}
 bp=gold['publicPost']['postID'];ob=gold['recapObligation'];ep=gold['gymViralityEpoch'];rp=gold['rickVirality'];memo=d['memos'][0];nonce=gold['nativeInstallation']['nonce'];turns=trace['turns']
 check('Rick real accepted battle and Hermes recap',RICK_POST in d['social']['posts'] and gold['rickBattle']['ended'] and gold['rickBattle']['defeated'] and any(e['producer']=='hermes' for e in gold['rickEpisode']),1)
 check('Brock prior public scouting retains Rick attribution',len([c for c in pre['brock']['reportedClaims'] if c['attribution']['postID']==RICK_POST])==2 and all(c['claim'] in d['social']['posts'][c['attribution']['postID']]['claims'] for c in pre['brock']['reportedClaims']),2)
 check('Exact accepted frozen StrategyMemo',d['memos']==pre['memos'] and memo['source']=='model' and hashlib.sha256(memo['strategyText'].encode()).hexdigest()=='0b641fa6e17877ea6eb04bbc9748b08ca4974555a450c442ead7874700173131' and all(memo['strategyText'] in t['authorizedStateAndPersonality'] for t in turns),3)
 check('Exact locked authored roster and one native installation',d['decisions']['commitments']==pre['decisions']['commitments'] and gold['nativeInstallation']['party']==[{'heldItem':0,'level':12,'moves':[33,111,0,0],'species':74},{'heldItem':0,'level':14,'moves':[33,20,317,0],'species':95}] and gold['nativeInstallation']['nativeConstructorCount']==1,4)
 check('All meaningful choices live and bounded with terminal disposition',bool(turns) and all(t['source']=='mercury' and t['selected']['choiceID'] in t['legalChoices'] and any(x['stage'] in ('EXECUTED','CANCELED_BATTLE_ENDED') for x in t['lifecycle']) for t in turns),5)
 receipts=[a for a in d['audit'] if not a.get('event')]
 forced=[a for a in receipts if a['source']=='engine_forced']
 def sole_replacement(a):
  following=next(t['fairNativeState'] for t in turns if t['fairNativeState']['request']>a['nativeRequest'])
  alive=[m for m in following['own'] if m['hp']>0]
  return a['phase']==2 and a['fallbackReason']==4 and len(alive)==1 and a['nativeSelected']==(4<<8)|alive[0]['slot'] and not any(r['role']=='battle' and r.get('scope',{}).get('nonce')==nonce and r['scope']['request']==a['nativeRequest'] for r in ledger['attempts'][66:])
 check('Zero meaningful vanilla fallback; separately proved sole native replacement',bool(receipts) and all((a['source']=='mercury' and a['fallbackReason']==0) or (a['source']=='engine_forced' and sole_replacement(a)) for a in receipts) and not any(a.get('stage')=='CANCELED_TIMEOUT_FALLBACK' for a in d['lifecycle']),6)
 check('Ordinary native player victory',len(battles)==1 and b.get('ended') and b.get('defeated') and b.get('outcome')==1,7)
 ends=[e for e in trace['canonicalEvents'] if e['record']['eventType']=='BATTLE_ENDED']
 check('One authoritative matching native victory end',len(ends)==1 and ends[0]['eventID']==b.get('endEvent') and ends[0]['record']['payload']['outcome']==1,8)
 check('Normal saved Boulder and Brock progression',all(d['boulder']['flags'].values()) and d['checkpoint']['kind']=='normal_save',9)
 check('Automatically created obligation matches native end',ob['battleID']==b.get('battleID') and ob['endEventID']==b.get('endEvent'),10)
 check('Actual live Hermes recap committed, not fallback',ob['status']=='PUBLISHED' and ob['outcome']['producer']=='hermes' and ob['outcome']['fallbackReason'] is None and ob['outcome']['model']['transport']=='live',11)
 check('Gym classified production high-profile',ep['prominence']=='gym' and ep['postID']==bp and ep['reach']==json.loads((ROOT/'config/virality_policy.json').read_text())['highProfile'],12)
 check('Unmodified production Gym diffusion exceeds ordinary Rick',len(ep['deliveries'])>len(rp['deliveries']) and ep['configSHA256']==rp['configSHA256'],13)
 claims=[c for c in d['sally']['reportedClaims'] if c['attribution']['postID']==bp]
 check('Legitimate upcoming Sally gains only post-derived intelligence',bool(claims) and all(c['claim'] in gold['publicPost']['claims'] for c in claims) and not pre['sally']['reportedClaims'],14)
 packets=list(gold['observedActorPackets'].values())+[d['sally']]
 check('Reported information is restricted to actually published claims',all(c['attribution'].get('postID') in d['social']['posts'] and c['claim'] in d['social']['posts'][c['attribution']['postID']]['claims'] for p in packets for c in p['reportedClaims']) and all(e['actorID']==BROCK for e in gold['privateDirectorEpisode']) and all(c['attribution']['author']==BROCK for c in claims),15)
 views=[read('final-viewer-proof'),read('final-restored-viewer-proof')]
 check('Native continuing feed/posts/followers viewer is read-only',all(v['sevenHashesUnchanged'] and v['requestLedgerUnchanged'] for v in views) and read('final-visual-review')['reviewed'] and all(hashlib.sha256((ROOT/v['path']).read_bytes()).hexdigest()==v['sha256'] for v in read('final-visual-review')['screens']),16)
 check('Fresh final paired reload restores exact seven projections/memo/lock/audit',restored['hashes']==d['hashes'] and restored['memos']==d['memos'] and restored['decisions']==d['decisions'] and restored['audit']==d['audit'] and restored['lifecycle']==d['lifecycle'] and all(restored['boulder']['flags'].values()),17)
 check('Pre-Brock prefix excludes winning and abandoned future states',rollback['hashes']==pre['hashes'] and not rollback['audit'] and not rollback['lifecycle'] and not any(x['sourceTrainerID']==414 for x in rollback['world']['battles'].values()) and bp not in rollback['social']['posts'] and not any(rollback['boulder']['flags'].values()) and len(battles)==1,18)
 check('Original 66 charged requests immutable',ledger['attempts'][:66]==old['attempts'])
 new=ledger['attempts'][66:];check('Closed aggregate and scoped role caps',ledger['closed'] and ledger['maximumAttempts']==150 and len(ledger['attempts'])<=150 and sum(a['role']=='battle' for a in new)<=80 and sum(a['role']=='puppeteer' for a in new)<=4 and all(a['role'] in ('battle','puppeteer') for a in new))
 check('Protected source/policies/prompts/user dump unchanged',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in read('final-protected').items()))
 recall=read('final-fresh-recall-proof');check('Fresh pinned Hermes retrieval after cleanup, explicitly zero hosted POST',recall['hostedPOSTs']==0 and recall['sevenHashesUnchanged'] and recall['requestLedgerUnchanged'] and any(e['producer']=='hermes' and e['postID']==bp for e in recall['episodes']) and all(e['actorID']==BROCK for e in recall['episodes']))
 cleanup=read('final-cleanup');check('Owned workers stopped and normal inference disabled',cleanup['workersStopped'] and cleanup['hostedDefaultDisabled'] and cleanup['liveRuntimeHomeRemoved'] and not any(Path(p).exists() for p in cleanup['recallCleanup']['candidates']))
 out={'ticket':'VERTICAL-SLICE-01','accepted':all(c['passed'] for c in checks),'gateCount':len(gates),'checkCount':len(checks),'gates':gates,'checks':checks,'campaign':d['campaign']['id'],'branch':d['campaign']['active_branch'],'brockBattle':b.get('battleID'),'brockPost':bp,'liveWinningChoices':len(turns),'newBattleCalls':sum(a['role']=='battle' for a in new),'newHermesCalls':sum(a['role']=='puppeteer' for a in new),'historicalChargedRequests':len(ledger['attempts']),'rickDeliveries':len(rp['deliveries']),'gymDeliveries':len(ep['deliveries']),'sallyPublicClaims':len(claims)}
 (E/'final-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('checks','gates')}));return out
if __name__=='__main__':
 result=verify();sys.exit(0 if result['accepted'] else 1)

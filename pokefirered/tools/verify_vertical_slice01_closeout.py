#!/usr/bin/env python3
"""Verify the new live branch's actual causal artifacts, never call a model."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from vertical_slice01_host import E
from vertical_slice01_verify import RICK_POST,BROCK

def verify():
 def read(n):return json.loads((E/(n+'.json')).read_text())
 checks=[]
 def check(n,yes):
  if not yes:raise AssertionError(n)
  checks.append(n)
 d=read('closeout-final');early=read('closeout-r2');ledger=read('requests');prior=read('requests-before-closeout')
 check('prior nine immutable charges',ledger['attempts'][:9]==prior['attempts'])
 check('closed same aggregate authorization',ledger['closed'] and ledger['maximumAttempts']==30 and len(ledger['attempts'])<=30)
 check('all completed responses have known zero cost',all((a.get('response',{}).get('usage') or a.get('outcome',{}).get('usage',{})).get('cost')==0 for a in ledger['attempts']))
 check('explicit recorded allocation changes',len(ledger['rebalances'])==2 and ledger['rebalances'][0]['priorAttempts']==9)
 check('actual new branch, old memo untouched',d['campaign']['active_branch']==early['campaign']['active_branch'] and d['campaign']['active_branch']!='3be1b7cc-1a3e-4244-911a-210ba4583cf9')
 check('one live immutable memo',len(d['memos'])==1 and d['memos']==early['memos'] and d['memos'][0]['source']=='model')
 check('exact prebattle lock',d['decisions']['commitments']==early['decisions']['commitments'] and len(d['decisions']['commitments'])==1)
 memo=d['memos'][0];lock=next(iter(d['decisions']['commitments'].values()))
 check('lock references actual live memo',lock['strategyID']==memo['strategyID'])
 check('prebattle only public Rick claims',len(early['brock']['reportedClaims'])==2 and all(x['attribution']['postID']==RICK_POST and x['claim']['type']!='MOVE_REVEALED' for x in early['brock']['reportedClaims']))
 check('early no Sally claims/Gym flags',not early['sally']['reportedClaims'] and not any(early['boulder']['flags'].values()))
 check('native loss awards no Boulder flags',not any(d['boulder']['flags'].values()))
 check('real Brock player loss completed',any(b['sourceTrainerID']==414 and b['ended'] and b['outcome']==2 for b in d['world']['battles'].values()))
 episodes=d['puppeteer']['episodes'];bp=next(e['postID'] for e in episodes.values() if e['actorID']==BROCK)
 check('actual configured Hermes Rick and Brock recaps',any(e['producer']=='hermes' and e['postID']==RICK_POST for e in episodes.values()) and any(e['producer']=='hermes' and e['postID']==bp for e in episodes.values()))
 check('Sally only attributed public Gym claims',len(d['sally']['reportedClaims'])==2 and all(x['attribution']['postID']==bp and x['claim']['type']!='MOVE_REVEALED' for x in d['sally']['reportedClaims']))
 a,b=d['virality']['epochs'][RICK_POST],d['virality']['epochs'][bp]
 check('Gym larger audience at same real fame',a['followerCount']==b['followerCount']==1 and a['prominence']=='ordinary' and b['prominence']=='gym' and len(b['deliveries'])>len(a['deliveries']))
 installation=next(iter(d['decisions']['installations'].values()))
 check('sole authored native roster',installation['receipt']['party']==[{'heldItem':0,'level':12,'moves':[33,111,0,0],'species':74},{'heldItem':0,'level':14,'moves':[33,20,317,0],'species':95}] and installation['receipt']['nativeConstructorCount']==1)
 rows=[json.loads(x) for x in (E/'battle-audit.jsonl').read_text().splitlines()]
 nonce=installation['receipt']['nonce']
 sels=[x for x in rows if x['event']=='selection' and x['request']['nativeState']['nonce']==nonce]
 live=[x for x in sels if x['source']=='mercury'];unavailable=[x for x in sels if x['source']=='unavailable']
 check('18 supplied live Mercury choices and explicit unavailable turn19',len(live)==18 and len(unavailable)==1 and unavailable[0]['request']['nativeState']['turn']==19 and all(x['result']['choiceID'] in x['request']['choices'] for x in live))
 terminals=[x for x in rows if x['event']=='native-terminal' and x.get('session')==nonce]
 unique={(x['session'],x['battle'],x['generation'],x['battler'],x['phase'],x['nativeRequest']):x for x in terminals}
 check('restarted terminal duplicates agree',all((x['source'],x['nativeSelected'],x['fallbackReason'])==(unique[(x['session'],x['battle'],x['generation'],x['battler'],x['phase'],x['nativeRequest'])]['source'],unique[(x['session'],x['battle'],x['generation'],x['battler'],x['phase'],x['nativeRequest'])]['nativeSelected'],unique[(x['session'],x['battle'],x['generation'],x['battler'],x['phase'],x['nativeRequest'])]['fallbackReason']) for x in terminals))
 check('native accepts 18 unique live choices then explicit fallback',len([x for x in unique.values() if x['source']=='mercury'])==18 and any(x['source']=='vanilla_fallback' and x['turn']==19 and x['fallbackReason']==2 for x in terminals))
 check('exact subjective memo in live packets',all(memo['strategyText'] in x['request']['state'] and x['request']['strategyID']==memo['strategyID'] for x in sels))
 check('no invented requested tactic manifests',all(x['nativeSelected'] in x['request']['nativeActions'].values() for x in live))
 check('new normal save',d['checkpoint']['kind']=='normal_save' and d['checkpoint']['branch']==d['campaign']['active_branch'])
 restore=read('closeout-restored-final')
 check('fresh normal restore exact seven projections',restore['hashes']==d['hashes'] and restore['memos']==d['memos'] and restore['decisions']==d['decisions'])
 check('native viewer changes no history or requests',read('closeout-viewer-proof')['sevenHashesUnchanged'] and read('closeout-viewer-proof')['requestLedgerUnchanged'])
 check('fresh restored native viewer changes no history or requests',read('closeout-restored-viewer-proof')['sevenHashesUnchanged'] and read('closeout-restored-viewer-proof')['requestLedgerUnchanged'] and read('closeout-restored-viewer-proof')['hashes']==d['hashes'])
 r1=read('closeout-restored-r1');gym=read('closeout-restored-gym');gym_before=read('closeout-gym-ready')
 check('earlier save excludes future memo lock and Brock post',not r1['memos'] and not r1['decisions']['commitments'] and bp not in r1['social']['posts'] and not any(r1['boulder']['flags'].values()))
 check('pre-Gym fresh restore exact cutoff and immutable lock',gym['hashes']==gym_before['hashes'] and gym['memos']==early['memos'] and gym['decisions']['commitments']==early['decisions']['commitments'] and not gym['decisions']['installations'] and bp not in gym['social']['posts'])
 recall=read('closeout-fresh-recall-proof')
 check('fresh pinned Hermes scoped recall after cleanup with zero POST',recall['hostedPOSTs']==0 and recall['sevenHashesUnchanged'] and recall['requestLedgerUnchanged'] and any(e['producer']=='hermes' and e['postID']==bp for e in recall['episodes']) and all(e['actorID']==BROCK for e in recall['episodes']))

 out={'passed':True,'count':len(checks),'checks':checks,'accepted':False,'missingGates':['fully live Gym battle without fallback','native Boulder win on live-memo branch'],'ticket':'VERTICAL-SLICE-01','campaign':d['campaign']['id'],'branch':d['campaign']['active_branch'],'strategyID':memo['strategyID'],'strategySource':'model','brockPost':bp,'hostedRequests':len(ledger['attempts']),'actualMercuryChoices':len(live),'vanillaFallbackTurns':[19],'rickDeliveries':len(a['deliveries']),'brockDeliveries':len(b['deliveries']),'scope':'actual first Rick common prefix followed by legitimately divergent live Brock branch; native normal saves and retained checkpoint milestones, not New Game/full campaign'}
 (E/'closeout-verification.json').write_text(json.dumps(out,indent=2)+'\n');return {k:v for k,v in out.items() if k!='checks'}
if __name__=='__main__':print(json.dumps(verify()))

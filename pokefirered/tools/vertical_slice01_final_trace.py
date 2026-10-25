#!/usr/bin/env python3
"""Read-only export of actual final-closeout artifacts; no model/game mutation."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from vertical_slice01_host import E,PRIVATE,open_store
BROCK='trainer:fr:trainer:0414';RICK='trainer:fr:trainer:0102'
RICK_POST='11e722419022a5e2dc016ab285df168642f3a742a7456f181e9e24580d37c6fa'
def main():
 d=json.loads((E/'final-success.json').read_text())
 battle=next(b for b in d['world']['battles'].values() if b['sourceTrainerID']==414)
 installation=next(iter(d['decisions']['installations'].values()))['receipt'];nonce=installation['nonce']
 cfg=json.loads((PRIVATE/'launch.json').read_text())
 with open_store(cfg['database']) as w:
  events=w.get_canonical_events()
  actors={'trainer:'+a for a in d['world']['trainers']}
  actors.update(r['recipient'] for ep in d['virality']['epochs'].values() for r in ep['deliveries'])
  actors.add('trainer:fr:trainer:0117')
  packets={a:w.trainer_packet(a) for a in sorted(actors)}
 selected_events=[e for e in events if e['battleID']==battle['battleID']]
 rows=[json.loads(x) for x in (E/'battle-audit.jsonl').read_text().splitlines()]
 selections=[r for r in rows if r['event']=='selection' and r['request']['nativeState']['nonce']==nonce]
 turns=[]
 for s in selections:
  req=s['request'];turn=req['nativeState']['turn']
  turns.append({'turn':turn,'source':s['source'],'strategyID':req['strategyID'],'strategyMemoSubjective':d['memos'][0]['strategyText'],'authorizedStateAndPersonality':req['state'],'fairNativeState':req['nativeState'],'legalChoices':req['choices'],'selected':s['result'],'nativeSelected':s['nativeSelected'],'nativeAcceptance':[{k:v for k,v in t.items() if k!='selection'} for t in rows if t['event']=='native-terminal' and t.get('session')==nonce and t['turn']==turn],'actualResolutionEvents':[e for e in selected_events if e['record']['eventType']=='BATTLE_ACTION_RESOLVED' and e['record']['turnID']==turn and e['record']['payload']['actorSide']==1],'lifecycle':[r for r in d['lifecycle'] if r['session']==nonce and r['turn']==turn],'hostLatencySeconds':s.get('hostLatencySeconds'),'interpretationLimit':'Subjective intent is not evidence; no inferred model rationale. A controller acceptance is not an execution receipt.'})
 (E/'final-turn-trace.json').write_text(json.dumps({'nonce':nonce,'canonicalBattleID':battle['battleID'],'turns':turns,'canonicalEvents':selected_events},indent=2)+'\n')
 obligation=next(o for o in d['puppeteer']['obligations'].values() if o['actorID']==BROCK)
 bp=obligation['outcome']['postID'];post=d['social']['posts'][bp]
 epoch=d['virality']['epochs'][bp]
 out={'version':1,'campaign':d['campaign']['id'],'branch':d['campaign']['active_branch'],'buildSHA256':installation.get('romSHA256',json.loads((ROOT/'evidence/phase4/battle_end01/manifest-external.json').read_text())['rom_sha256']),'preBrockCheckpoint':json.loads((E/'final-pre-brock.json').read_text())['checkpoint'],'rickBattle':d['world']['battles'][d['social']['posts'][RICK_POST]['battleID']],'rickPost':d['social']['posts'][RICK_POST],'rickEpisode':[v for v in d['puppeteer']['episodes'].values() if v['actorID']==RICK],'rickVirality':d['virality']['epochs'][RICK_POST],'brockPrebattleBriefing':json.loads((E/'final-pre-brock.json').read_text())['brock'],'strategyMemo':d['memos'][0],'commitment':next(iter(d['decisions']['commitments'].values())),'nativeInstallation':installation,'turnTrace':'evidence/phase4/vertical_slice01/final-turn-trace.json','battleEnd':battle,'nativeBattleEvents':selected_events,'normalProgression':d['boulder'],'recapObligation':obligation,'publicPost':post,'privateDirectorEpisode':[v for v in d['puppeteer']['episodes'].values() if v['actorID']==BROCK],'gymViralityEpoch':epoch,'upcomingSallyPacket':d['sally'],'observedActorPackets':packets,'pairedFinalSave':d['checkpoint'],'sevenHashes':d['hashes'],'limits':['not a fresh New Game replay','no general campaign expansion','no provider rationale inferred','no paid fallback','no hot-state/power-loss qualification','endgame deferred']}
 (E/'final-golden-trace.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'battle':battle['battleID'],'turns':len(turns),'brockPost':bp,'rickDeliveries':len(out['rickVirality']['deliveries']),'gymDeliveries':len(epoch['deliveries'])}))
if __name__=='__main__':main()

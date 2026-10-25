#!/usr/bin/env python3
"""Verify retained real-run artifacts without inference or gameplay injection.

Passing these checks does not accept the live slice: the StrategyMemo is fallback.
"""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from vertical_slice01_host import E
from vertical_slice01_verify import RICK_POST,BROCK_POST,BROCK

def main():
 checks=[]
 def read(n):return json.loads((E/(n+'.json')).read_text())
 def check(n,v):
  if not v:raise AssertionError(n)
  checks.append(n)
 d=read('gym-downstream');r=read('restore-S1');s3=read('S3');ledger=read('requests')
 check('closed ledger retains nine attempts',ledger['closed'] and len(ledger['attempts'])==9)
 check('all returned usages report cost zero',all(a['outcome']['usage']['cost']==0 for a in ledger['attempts']))
 check('no preparation POST',not any(a['role']=='preparation' for a in ledger['attempts']))
 for actor,post in (('trainer:fr:trainer:0102',RICK_POST),(BROCK,BROCK_POST)):
  check('actual Hermes episode '+actor,any(e['actorID']==actor and e['postID']==post and e['producer']=='hermes' for e in d['puppeteer']['episodes'].values()))
 check('Brock public Rick facts only',len(r['brock']['reportedClaims'])==2 and all(x['attribution']['postID']==RICK_POST and x['claim']['type']!='MOVE_REVEALED' for x in r['brock']['reportedClaims']))
 check('Sally initially knows none',not r['sally']['reportedClaims'])
 check('Sally later receives only Brock public claims',len(d['sally']['reportedClaims'])==2 and all(x['attribution']['postID']==BROCK_POST and x['claim']['type']!='MOVE_REVEALED' for x in d['sally']['reportedClaims']))
 epochs=d['virality']['epochs'];rick,brock=epochs[RICK_POST],epochs[BROCK_POST]
 check('same actual fame',rick['followerCount']==brock['followerCount']==1)
 check('real Gym broadens eligible audience',brock['prominence']=='gym' and rick['prominence']=='ordinary' and len(brock['deliveries'])>len(rick['deliveries']))
 check('explicitly labeled fallback memo',len(s3['memos'])==1 and s3['memos'][0]['source']=='fallback')
 check('one exact native authored installation',len(s3['decisions']['installations'])==1 and next(iter(s3['decisions']['installations'].values()))['receipt']['party']==[{'heldItem':0,'level':12,'moves':[33,111,0,0],'species':74},{'heldItem':0,'level':14,'moves':[33,20,317,0],'species':95}])
 audit=[json.loads(x) for x in (E/'battle-audit.jsonl').read_text().splitlines()]
 selections=[a for a in audit if a['event']=='selection']
 check('two real Mercury choices',len(selections)==2 and [a['nativeSelected'] for a in selections]==[257,258] and all(a['source']=='mercury' for a in selections))
 check('both chosen supplied legal IDs',all(a['result']['choiceID'] in a['request']['choices'] and a['request']['nativeActions'][a['result']['choiceID']]==a['nativeSelected'] for a in selections))
 check('native constructor observer is real Brock once',any(a['event']=='native-authored-constructor' and a['trainer']==414 and a['count']==1 for a in audit))
 check('sole forced replacement bypasses model',any(a['event']=='native-terminal' and a['nativeSelected']==1025 and a['source']=='engine_forced' for a in audit))
 check('native badge and defeated flags',all(read('restore-S3')['boulder']['flags'].values()))
 for stage in ('S0','S1','S2','S3'):
  z=read('restore-'+stage);check('actual normal restore '+stage,z['chargedRequests']==9 and len(z['posts'])=={'S0':0,'S1':1,'S2':1,'S3':4}[stage])
 check('divergent native branch rejects abandoned job',read('native-divergence')['oldStrategyJobCurrent'] is False)
 check('restored viewer leaves seven projections unchanged',read('restore-s3-viewer')['sevenHashesUnchanged'] and read('restore-s3-viewer')['requestLedgerUnchanged'])
 check('fresh Hermes retrieves real memory after cleanup',read('fresh-recall-proof')['hostedPOSTs']==0 and read('fresh-recall-proof')['sevenHashesUnchanged'])
 m=read('manifest-native');rom=ROOT/m['rom_path']
 check('exact retained native ROM',hashlib.sha256(rom.read_bytes()).hexdigest()=='80ce394e81952ebc31b0a28ac283d156280381090023c4188deb524a53990a89')
 rows=[json.loads(x) for x in (E/'emulator.jsonl.resources').read_text().splitlines()]
 viewer=[x for x in rows if x['label'].startswith(('rick-pokebook','gym-pokebook','restore-s3-viewer'))]
 resource={'measurement':'retained actual emulator heap/task/window/sprite snapshots; not stack or worst-case proof','allSampleMinimumFree':min(x['free'] for x in rows),'viewerMinimumFree':min(x['free'] for x in viewer if x['viewerOwner']),'viewerMinimumLargest':min(x['largest'] for x in viewer if x['viewerOwner']),'viewerReturnedOwnership':all(x['viewerOwner']==0 for x in viewer if x['label'].endswith('field')),'samples':viewer}
 check('viewer resource ownership returns',resource['viewerReturnedOwnership'])
 (E/'resource-summary.json').write_text(json.dumps(resource,indent=2)+'\n')
 out={'checks':checks,'count':len(checks),'passed':True,'liveAcceptance':False,'missingGate':'criterion 7: actual persisted live Brock StrategyMemo; primary encounter memo is immutable fallback','rickDeliveries':len(rick['deliveries']),'brockDeliveries':len(brock['deliveries']),'hostedPOSTs':9,'fullNewGameGoldenReplayQualified':False}
 (E/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='checks'}))
if __name__=='__main__':main()

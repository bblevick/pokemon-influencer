#!/usr/bin/env python3
"""Fresh pinned Hermes process retrieves real durable episodes; mock transport.

No hosted POST, new publication, or gameplay mutation. Requires restored S3
and no concurrently active campaign host/worker.
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from vertical_slice01_host import E,PRIVATE,open_store
from vertical_slice01_verify import verify,BROCK,BROCK_POST
from vertical_slice01_viewer import snapshot
from puppeteer.runtime import run_job,cleanup

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--closeout',action='store_true');parser.add_argument('--label',default=None);args=parser.parse_args()
 if args.label and not __import__('re').fullmatch('[a-z0-9-]{1,40}',args.label):raise ValueError('evidence label')
 if not args.closeout:verify('S3')
 before=snapshot();ledger=(E/'requests.json').read_bytes()
 cfg=json.loads((PRIVATE/'launch.json').read_text())
 with open_store(cfg['database']) as w:
  grant=w.begin_recall_job(BROCK)
  expected=[p for p in w.puppeteer_state()['episodes'].values() if p['actorID']==BROCK]
 result=run_job(cfg['database'],grant['jobID'],transport='mock',behavior='recall',experiment='closeout',store_factory=open_store,audit_directory=E/'fresh-recall')
 recalls=[t['output'] for t in result['tools'] if t['name']=='recall_puppeteer_memory' and 'output' in t]
 assert result['transport']=='mock' and result['workerExit']==0 and len(recalls)==1
 episodes=recalls[0]['episodes']
 assert episodes and all(p['actorID']==BROCK for p in episodes)
 assert any(p['producer']=='hermes' and (args.closeout or p['postID']==BROCK_POST) for p in episodes)
 assert {p['episodeID'] for p in episodes}=={p['episodeID'] for p in expected}
 assert snapshot()==before and (E/'requests.json').read_bytes()==ledger
 cleaned=cleanup(result['runtimeHome'],dry_run=False)
 out={'workflow':'fresh actual pinned Hermes process with explicitly mocked model transport; real restored durable actor-private episodes','hostedPOSTs':0,'hermesRevision':result['hermesRevision'],'jobID':grant['jobID'],'episodes':episodes,'sevenHashesUnchanged':True,'requestLedgerUnchanged':True,'cleanup':cleaned}
 (E/((args.label+'-fresh-recall-proof.json') if args.label else ('closeout-fresh-recall-proof.json' if args.closeout else 'fresh-recall-proof.json'))).write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'assertions':'passed','hostedPOSTs':0,'episodes':len(episodes),'sevenHashesUnchanged':True}))
if __name__=='__main__':main()

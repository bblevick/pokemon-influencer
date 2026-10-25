#!/usr/bin/env python3
"""Assert actual paired campaign prefixes; never fabricate gameplay or inference."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from vertical_slice01_host import E,PRIVATE,open_store,save_identity
from prep.progression import read_boulder
RICK='trainer:fr:trainer:0102';BROCK='trainer:fr:trainer:0414';SALLY='trainer:fr:trainer:0117'
RICK_POST='11e722419022a5e2dc016ab285df168642f3a742a7456f181e9e24580d37c6fa'
BROCK_POST='590964db7f848cd1a08afa3722203429c33a25c6947a772181615870f83abe9b'

def verify(stage):
 cfg=json.loads((PRIVATE/'launch.json').read_text());saved=json.loads((E/'S3.json').read_text())
 with open_store(cfg['database']) as w:
  social=w.social_state();decisions=w.decision_state();pp=w.puppeteer_state()
  hashes={k:getattr(w,m)() for k,m in {'worldSHA256':'verify_replay','memorySHA256':'verify_memory_replay','socialSHA256':'verify_social_replay','puppeteerSHA256':'verify_puppeteer_replay','strategySHA256':'verify_strategy_replay','decisionSHA256':'verify_decision_replay','viralitySHA256':'verify_virality_replay'}.items()}
  out={'stage':stage,'workflow':'actual fresh managed normal-battery restore and native Continue; hosted inference disabled','campaign':w.campaign(),'checkpoint':w.get_save_checkpoint(save_identity(cfg['save']).fingerprint),'hashes':hashes,'posts':social['posts'],'playerFollowers':[e for e in social['follows'].values() if e['followed']=='player:'+w.campaign()['id']],'memos':w.memo_records(),'decisions':decisions,'puppeteer':pp,'brock':w.trainer_packet(BROCK),'sally':w.trainer_packet(SALLY),'boulder':read_boulder(Path(cfg['save']).read_bytes(),w.build),'chargedRequests':len(json.loads((E/'requests.json').read_text())['attempts'])}
  assert out['checkpoint']['kind']=='normal_save' and out['chargedRequests']==9 and not w.pending_save()
  assert len(out['posts'])=={'S0':0,'S1':1,'S2':1,'S3':4}[stage]
  assert len(out['playerFollowers'])==(0 if stage=='S0' else 1)
  assert len(out['memos'])==(1 if stage in ('S2','S3') else 0)
  assert len(decisions['commitments'])==(1 if stage in ('S2','S3') else 0)
  assert len(decisions['installations'])==(1 if stage=='S3' else 0)
  assert all(out['boulder']['flags'].values()) if stage=='S3' else not any(out['boulder']['flags'].values())
  if stage!='S0':
   assert RICK_POST in out['posts']
   assert any(o['producer']=='hermes' and o['postID']==RICK_POST for o in pp['episodes'].values())
  if stage in ('S1','S2'):
   assert not out['sally']['reportedClaims']
   assert len(out['brock']['reportedClaims'])==2
   assert all(r['claim']['type']!='MOVE_REVEALED' for r in out['brock']['reportedClaims'])
  if stage in ('S2','S3'):
   assert out['memos']==saved['memos']
   assert decisions['commitments']==saved['decisions']['commitments']
  if stage=='S3':
   assert all(hashes[k]==saved[k] for k in hashes)
   assert any(o['producer']=='hermes' and o['postID']==BROCK_POST for o in pp['episodes'].values())
   assert len(out['sally']['reportedClaims'])==2
   assert all(r['attribution']['postID']==BROCK_POST for r in out['sally']['reportedClaims'])
  (E/('restore-'+stage+'.json')).write_text(json.dumps(out,indent=2)+'\n')
  return {'stage':stage,'assertions':'passed','checkpoint':out['checkpoint']['id'],'chargedRequests':9}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['S0','S1','S2','S3']);print(json.dumps(verify(p.parse_args().stage)))

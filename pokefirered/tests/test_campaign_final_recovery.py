"""Real retained Kent evidence on isolated copies; no hosted work or native replay."""
import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from campaign.expansion import ExpansionStore
from campaign.recovery import prove,recover,table_hashes,native_state,PROOF_METHODS
from battle.transport import Handler
from world.store import WorldError
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase6/campaign_expansion01_final';P=ROOT/'.local/campaign_expansion01_final';M=E/'manifest-native.json'
def read(p):return json.loads(p.read_text())
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'world.sqlite3'
  src=sqlite3.connect('file:'+str(P/'kent-resolution-suspended.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(self.path)
  try:src.backup(dst)
  finally:dst.close();src.close()
  self.w=ExpansionStore(self.path,M);self.proof=read(E/'final-recovery/causal-cut-manifest.json');self.layout=read(ROOT/'config/prep_save_layout.json');self.identity,_=native_state(P/'Kent-victory-UNPAIRED.sav',self.layout)
  self.network=patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden'));self.network.start()
 def tearDown(self):self.network.stop();self.w.close();self.tmp.cleanup()
 def arguments(self):
  return dict(battery=P/'Kent-victory-UNPAIRED.sav',prior_battery=P/'C3-james-blocked.sav',receipt=json.loads((E/'save-receipts.jsonl').read_text().splitlines()[-1]),launch=read(P/'launch.json'),settled=read(E/'k-Kent-social-settled.json'),lock=read(E/'kent-resolution/lock-before.json'),inventory=read(E/'final-recovery/retained-inventory.json'),manifest_path=M,layout=self.layout)
 def test_real_suspended_database_causal_proof_no_write(self):
  before=table_hashes(self.w);p=prove(self.w,**self.arguments());self.assertEqual(p['sevenHashes'],self.proof['sevenHashes']);self.assertEqual(p['realDatabaseRuntimeProof']['pendingRequests'],0);self.assertEqual(before,table_hashes(self.w));self.assertEqual(self.w.campaign()['status'],'incomplete')
 def test_pair_metadata_idempotent_then_official_restore(self):
  before=table_hashes(self.w);cp=recover(self.w,self.proof,self.identity);self.assertEqual(cp,recover(self.w,self.proof,self.identity));self.assertEqual(self.w.db.execute('SELECT COUNT(*) FROM retrospective_pairs').fetchone()[0],1);self.w.restore(self.identity);self.assertEqual(cp,recover(self.w,self.proof,self.identity));self.assertEqual(before,table_hashes(self.w));self.assertEqual({m:getattr(self.w,m)() for m in PROOF_METHODS},self.proof['sevenHashes'])
 def test_cut_and_manifest_changes_fail_closed(self):
  for field,value in [('canonicalCutoff',397),('branch','wrong'),('admissible',False)]:
   p=copy.deepcopy(self.proof);p[field]=value
   with self.assertRaises(WorldError):recover(self.w,p,self.identity)
  self.assertIsNone(self.w.get_save_checkpoint(self.identity.fingerprint))
 def test_native_receipt_gap_and_nonempty_queue_reject(self):
  for field,value in [('ack',74),('depth',1),('nonce',17),('counter',17),('drops',1)]:
   args=self.arguments();args['receipt'][field]=value
   with self.assertRaises(WorldError):prove(self.w,**args)
 def test_changed_critical_post_or_lock_reject(self):
  for key in ('social','decisions','memos'):
   args=self.arguments();args['settled'][key]={} if key!='memos' else []
   with self.assertRaises(WorldError):prove(self.w,**args)
 def test_native_audit_lookup_ignores_later_lifecycle_rows(self):
  prior=next(r for r in self.w.battle_audit() if r.get('event')!='decision-disposition' and r['session']==720367614 and r['nativeRequest']==9)
  h=Handler({},Path(self.tmp.name));before=table_hashes(self.w)
  try:
   incoming={**prior,'source':'external_test','selection':None};self.assertEqual(h.retained_terminal(self.w,incoming,1),prior)
   incoming['nativeSelected']+=1
   with self.assertRaises(ValueError):h.retained_terminal(self.w,incoming,1)
   h.recover(self.w);self.assertFalse(h.pending);self.assertFalse(h.awaiting);self.assertIsNone(h.job);self.assertEqual(before,table_hashes(self.w))
  finally:h.close()
 def test_real_c3_rollback_excludes_kent_and_restore_returns_exact(self):
  cp=recover(self.w,self.proof,self.identity);self.w.restore(self.identity);final={m:getattr(self.w,m)() for m in PROOF_METHODS}
  prior,_=native_state(P/'C3-james-blocked.sav',self.layout);self.w.restore(prior)
  self.assertEqual({m:getattr(self.w,m)() for m in PROOF_METHODS},read(E/'C3-offline-restored.json')['hashes'])
  self.assertFalse(any(b['sourceTrainerID']==108 for b in self.w.state()['battles'].values()));self.assertEqual(len(self.w.social_state()['posts']),8)
  self.assertFalse(any(r['session']==720367614 for r in self.w.battle_audit()));self.assertFalse(any(e['postID']==self.proof['Kent']['postID'] for e in self.w.virality_state()['epochs'].values()))
  h=Handler({},Path(self.tmp.name))
  try:
   before=table_hashes(self.w);h.recover(self.w);self.assertFalse(h.pending);self.assertEqual(before,table_hashes(self.w))
  finally:h.close()
  self.w.restore(self.identity);self.assertEqual({m:getattr(self.w,m)() for m in PROOF_METHODS},final);self.assertEqual(self.w.get_save_checkpoint(self.identity.fingerprint),cp)
if __name__=='__main__':unittest.main()

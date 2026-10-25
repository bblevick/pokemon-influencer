"""Host/source tests, using an isolated copy of the accepted campaign, no cloud."""
import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from content.campaign import CampaignContent
from campaign.expansion import ExpansionStore
from campaign.expansion_runtime import ExpansionServices
from campaign.budget import CampaignBudget
from prep.domain import resolve_preparation_bundle
from roster.extract import file_hash
from world.saves import fingerprint,layout_from_build
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase6/campaign_expansion01';M=E/'manifest-native.json';SOURCE=ROOT/'.local/vertical_slice01/world.sqlite3'
class CampaignExpansionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'world.sqlite3'
  src=sqlite3.connect('file:'+str(SOURCE)+'?mode=ro',uri=True);dst=sqlite3.connect(self.path)
  try:src.backup(dst)
  finally:dst.close();src.close()
  self.w=ExpansionStore(self.path,M)
 def tearDown(self):self.w.close();self.tmp.cleanup()
 def test_source_baselines_and_sole_candidates(self):
  self.w.adopt_content()
  for actor,t in self.w.content.extension['trainers'].items():
   b=resolve_preparation_bundle(self.w,actor,'first');self.assertEqual(len(b['candidateSet']['candidates']),1)
   candidate=b['candidateSet']['candidates'][0]
   self.assertEqual([(p['species'],p['level'],p['moves'],p['heldItem']) for p in candidate['party']],[(p['species'],p['level'],p['moves'],p['heldItem']) for p in t['originals']]);self.assertEqual(candidate['acquisitionCount'],0);self.assertEqual(candidate['resourceCosts'],[])
 def test_sally_public_is_not_brock_private(self):
  self.w.adopt_content();p=self.w.context_packet('trainer:fr:trainer:0117','first')
  facts=p['modelInput']['authorizedSocialEvidence']['authorizedFacts'];self.assertEqual(len(facts),2)
  self.assertNotIn('MOVE_REVEALED',json.dumps(facts));self.assertEqual(p['modelInput']['opponentCurrentLead'],'UNKNOWN')
  self.assertEqual(self.w.trainer_packet('trainer:fr:trainer:0117')['directObservations'],[])
 def test_personas_differ_and_contexts_are_actor_bound(self):
  self.w.adopt_content();packets=[self.w.context_packet(a,'first') for a in self.w.content.extension['trainers']]
  self.assertEqual(len({p['modelInput']['campaignBehavior']['identity'] for p in packets}),4)
  self.assertEqual(len({p['scope']['actor'] for p in packets}),4)
  for p in packets:self.assertEqual(p['scope']['actor'],p['modelInput']['authorizedSocialEvidence']['actorID'])
 def test_adoption_deduplicates_and_restore_excludes_extension(self):
  before=self.w.preparation_state();self.w.adopt_content();after=self.w.preparation_state();self.w.adopt_content();self.assertEqual(after,self.w.preparation_state())
  m=json.loads(M.read_text());sav=fingerprint((ROOT/'.local/vertical_slice01/final-success.sav').read_bytes(),layout_from_build(ROOT/m['rom_path']))
  self.w.restore(sav);self.assertEqual(self.w.preparation_state(),before);self.assertFalse(hasattr(self.w.content,'extension'));self.assertIsNone(self.w.get_trainer_companion_state('trainer:fr:trainer:0117'))
 def test_source_tamper_and_grants_rejected(self):
  c=CampaignContent.load();x=copy.deepcopy(c.extension);x['trainers']['trainer:fr:trainer:0117']['originals'][0]['level']+=1
  with self.assertRaisesRegex(ValueError,'baseline'):CampaignContent(c.base,x)
  x=copy.deepcopy(c.extension);x['trainers']['trainer:fr:trainer:0117']['resources']['initialStock']=[{'item':13,'quantity':1}]
  with self.assertRaisesRegex(ValueError,'resources'):CampaignContent(c.base,x)
 def test_offline_generic_scheduler_locks_without_hosted_call(self):
  self.w.adopt_content();services=ExpansionServices(self.path,live=False);services.log=lambda *a,**kw:None
  try:
   services.tick(self.w);services.tick(self.w)
   lock=self.w.locked_preparation('trainer:fr:trainer:0117');self.assertIsNotNone(lock)
   memo=[m for m in self.w.memo_records() if m['actor']=='trainer:fr:trainer:0117'][0];self.assertEqual(memo['source'],'fallback')
   services.tick(self.w);self.assertEqual(lock,self.w.locked_preparation('trainer:fr:trainer:0117'))
  finally:services.close(self.w)
 def test_legacy_campaign_writer_rejected(self):
  from campaign.store import CampaignStore
  self.w.adopt_content()
  with self.assertRaisesRegex(ValueError,'version-aware'):CampaignStore(self.path,M)
 def test_content_follow_permissions_restore(self):
  actor='trainer:fr:trainer:0117';self.assertFalse(self.w._follow_eligible(actor));self.w.adopt_content();self.assertTrue(self.w._follow_eligible(actor));self.assertFalse(self.w._follow_eligible('trainer:fr:trainer:0105'))
 def test_budget_subbounds_and_closed_ledger(self):
  path=Path(self.tmp.name)/'requests.json'
  with CampaignBudget(path) as b:
   b.authorize_campaign_expansion()
   for i in range(40):b.charge('battle',str(i),'free-model',str(i))
   with self.assertRaises(ValueError):b.charge('battle','over','free-model','over')
   b.close()
   with self.assertRaises(ValueError):b.charge('strategy','closed','free-model','closed')
 def test_native_permanent_ram_zero(self):
  r=json.loads((E/'native-memory.json').read_text());self.assertTrue(r['allRAMSymbolsIdentical']);self.assertEqual(r['nativeDeltaBytes'],0);self.assertEqual(r['beforeRemaining'],r['afterRemaining']);self.assertEqual(r['afterRemaining'],4)
 def test_provider_failure_is_encounter_scoped(self):
  from campaign.provider import CampaignBattleProvider
  from unittest.mock import patch
  import subprocess
  provider=CampaignBattleProvider(lambda:{})
  packet={'nativeState':{'trainerID':117,'battle':2,'turn':1,'phase':'NORMAL_TURN','nonce':1},'scope':{'campaign':'c','branch':'b','nonce':1,'generation':1,'battle':2},'strategyID':'memo','commitmentID':'lock','state':'text','question':'q','choices':{'a':'legal'}}
  with patch('campaign.provider.subprocess.run',side_effect=[subprocess.TimeoutExpired('fixture',2.55),subprocess.CompletedProcess('fixture',0,'{"source":"fixture"}')]) as request:
   self.assertIsNone(provider.decide_scoped(packet));self.assertIsNone(provider.decide_scoped(packet));self.assertEqual(request.call_count,1)
   packet['scope']['battle']=3;packet['nativeState']['battle']=3;packet['nativeState']['trainerID']=106
   self.assertEqual(provider.decide_scoped(packet),{'source':'fixture'});self.assertEqual(request.call_count,2)
 def test_viewer_orders_publications_and_excludes_private(self):
  from pokebook.viewer import Viewer
  from unittest.mock import patch
  state=self.w.social_state();posts=list(state['posts'].values())
  # Deliberately reverse lexical IDs; fixture checks chronology, no history write.
  public={**posts[0],'postID':'f'*64};later={**posts[0],'postID':'a'*64}
  private={**posts[0],'postID':'b'*64,'visibility':'actor_private'}
  fixture={**state,'posts':{public['postID']:public,later['postID']:later,private['postID']:private}}
  with patch.object(self.w,'social_state',return_value=fixture):
   self.assertEqual([p['postID'] for p in Viewer(self.w)._public()],[public['postID'],later['postID']])
 def test_campaign_progression_binding_rejects_wrong_area(self):
  c=CampaignContent.load();x=copy.deepcopy(c.extension)
  x['participation']['trainer:fr:trainer:0108']['campaignStage']='route3'
  with self.assertRaisesRegex(ValueError,'progression'):CampaignContent(c.base,x)
if __name__=='__main__':unittest.main()

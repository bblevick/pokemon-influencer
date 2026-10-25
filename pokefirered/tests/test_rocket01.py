"""Rocket contracts/source and typed-event fixtures; not live game evidence."""
import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from virality.store import ViralityPuppeteerStore
from virality import policy
from strategy.social_context import build_social_evidence
from content.rocket import RocketContent
from campaign.rocket import RocketStore
from campaign.budget import CampaignBudget
from prep.domain import resolve_preparation_bundle
from world.store import WorldError,dump
from world.saves import fingerprint,layout_from_build
from test_world01 import BUILD,TAG,SIZES,flash,msg
from test_memory01 import visible
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'evidence/phase7/rocket01/manifest-native.json';MEMBER='trainer:fr:trainer:0352';LEADER='trainer:fr:trainer:0348';GYM='trainer:fr:trainer:0414';ORDINARY='trainer:fr:trainer:0103';RIVAL='trainer:fr:trainer:0326'

class RocketFixtureTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'world.sqlite3';self.w=ViralityPuppeteerStore(self.path,BUILD,TAG);self.s1=fingerprint(flash(),SIZES);self.w.import_save(self.s1);self.w.authorize_launch(100,self.s1);self.w.activate_puppeteer();self.w.activate_virality()
 def tearDown(self):self.w.close();self.temp.cleanup()
 def battle(self,win=True):
  from bridge.events_wire import Message
  ms=[msg(1,1,1,trainer=352),msg(2,2,1,trainer=352)]
  v=msg(3,6,trainer=352);payload=bytearray(v.payload);payload[52:54]=(33).to_bytes(2,'little');ms.append(Message(v.kind,v.nonce,v.generation,v.sequence,v.tag,v.typ,bytes(payload)))
  # Ordinary visible move announcement from the player side.
  ms.append(msg(4,3,1,trainer=352))
  if win:ms.append(msg(5,4,1,trainer=352))
  ms.append(msg(len(ms)+1,5,1,trainer=352,outcome=1 if win else 2))
  for m in ms:self.w.ingest(m)
 def records(self,actor):return self.w.for_actor(actor).records(limit=256)['records']
 def test_private_independent_complete_retry_restart(self):
  self.battle();direct=self.records(MEMBER);reported=self.records(LEADER)
  self.assertTrue(direct);self.assertFalse(self.w.social_state()['posts']);self.assertEqual([r['claim'] for r in direct],[r['claim'] for r in reported]);self.assertTrue(all(r['mode']=='delivered' and r['source']['sender']==MEMBER and r['source']['channel']=='ROCKET_INTEL' for r in reported))
  for r in reported:self.assertEqual(self.w.for_actor(LEADER).provenance(r['memoryID'])[1]['actorID'],MEMBER)
  before=self.w.verify_virality_replay();self.w.advance_social('battle_completion');self.assertEqual(before,self.w.verify_virality_replay());self.w.close();self.w=ViralityPuppeteerStore(self.path,BUILD,TAG);self.assertEqual(before,self.w.verify_virality_replay())
 def test_public_subset_separate_leader_channels_no_faction_leak(self):
  self.battle();o=next(iter(self.w.puppeteer_state()['obligations'].values()));job=self.w.begin_job(o['obligationID']);self.w.fallback(job['jobID']);post=next(iter(self.w.social_state()['posts'].values()))
  private=[r for r in self.records(LEADER) if r['source'].get('channel')=='ROCKET_INTEL'];public=[r for r in self.records(LEADER) if r['source'].get('channel')=='pokebook'];direct=self.records(MEMBER)
  self.assertEqual(len(private),len(direct));self.assertEqual([r['claim'] for r in public],post['claims']);self.assertLess(len(post['claims']),len({dump(r['claim']) for r in direct}));self.assertTrue(any(r['claim']['type']=='MOVE_REVEALED' for r in private));self.assertNotIn('moveID',dump(public))
  for actor in (GYM,ORDINARY,RIVAL):
   self.assertTrue(all(r['source'].get('channel')!='ROCKET_INTEL' for r in self.records(actor)))
   self.assertTrue(all(r['claim'] in post['claims'] for r in self.records(actor)))
  ctx=build_social_evidence(self.w,LEADER);self.assertTrue(any(f['evidenceQuality']['attribution']=='reported' and f['evidenceQuality']['organizationalFidelity']=='full_observed_claim' for f in ctx['authorizedFacts']));self.assertNotIn('hiddenParty',dump(ctx))
 def test_loss_automatic_report_and_mandatory_public_obligation(self):
  self.battle(False);self.assertTrue(self.w.virality_state()['intel']);self.assertEqual(len(self.w.puppeteer_state()['obligations']),1);self.assertFalse(any(e['followed']==self.w.player_actor() for e in self.w.social_state()['follows'].values()))
 def test_wrong_recipient_and_unobserved_fields_denied(self):
  self.battle();source=self.w.for_actor(MEMBER)._find(self.records(MEMBER)[0]['memoryID'])
  for actor in (GYM,ORDINARY,RIVAL,MEMBER):
   with self.assertRaises(WorldError):self.w._authorize_rocket_reference(MEMBER,actor,source)
  r=copy.deepcopy(self.records(MEMBER));r[0]['claim']['hiddenParty']=[150]
  with self.assertRaises(WorldError):policy.rocket_intelligence(self.w.viral_config,member=MEMBER,leader=LEADER,records=r,campaign=self.w.campaign()['id'],branch=self.w.get_active_branch())
 def test_rollback_late_delivery_work_denied(self):
  self.battle();last=6;s2=fingerprint(flash(2,2),SIZES);self.w.finish_save(self.w.begin_save(100,self.s1),s2,dict(event='savedataUpdated',nonce=100,run=1,eventCounter=last,ack=last,depth=0,state=0,drops=0,counter=2));scope=self.w.virality_scope();after=self.w.verify_virality_replay();self.w.restore(self.s1)
  self.assertFalse(self.w.virality_state()['intel']);self.assertFalse(self.records(LEADER));self.assertFalse(self.records(MEMBER))
  with self.assertRaises(WorldError):self.w.advance_social('battle_completion',expected_scope=scope)
  self.w.restore(s2);self.assertEqual(after,self.w.verify_virality_replay())
 def test_grunt_ordinary_non_scout_no_follower_requirement(self):
  p=self.w.viral_config['profiles'][MEMBER];self.assertEqual(p['prominence'],'ordinary');self.assertIsNone(p['scouting']);self.battle();self.assertTrue(self.w.virality_state()['intel']);self.assertFalse(any(e['followed']==self.w.player_actor() for e in self.w.social_state()['follows'].values()))

class RocketContentTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'world.sqlite3';src=sqlite3.connect('file:'+str(ROOT/'.local/campaign_expansion01_recovery/world.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(self.path);src.backup(dst);dst.close();src.close();self.w=RocketStore(self.path,M)
 def tearDown(self):self.w.close();self.temp.cleanup()
 def test_source_bound_baseline_zero_inference_prep(self):
  self.w.adopt_content();b=resolve_preparation_bundle(self.w,MEMBER,'first');cs=b['candidateSet']['candidates'];self.assertEqual(len(cs),1);self.assertEqual([p['species'] for p in cs[0]['party']],[27,19,41]);self.assertEqual([p['level'] for p in cs[0]['party']],[11]*3);self.assertEqual(cs[0]['resourceCosts'],[]);self.assertEqual(cs[0]['acquisitionCount'],0);self.assertFalse(self.w._follow_eligible(MEMBER));self.assertTrue(self.w._follow_eligible('trainer:fr:trainer:0117'))
 def test_adoption_retry_restore_parent_and_locked_history(self):
  before=copy.deepcopy(self.w.decision_state());self.w.adopt_content();content=self.w.preparation_state();self.w.adopt_content();self.assertEqual(content,self.w.preparation_state());self.assertEqual(before,self.w.decision_state())
  m=json.loads(M.read_text());sav=fingerprint((ROOT/'.local/rocket01/pre-rocket.sav').read_bytes(),layout_from_build(ROOT/m['rom_path']));self.w.restore(sav);self.assertEqual(self.w.content.hash,RocketContent.load().previous.hash);self.assertIsNone(self.w.get_trainer_companion_state(MEMBER))
 def test_offline_context_has_no_global_director_access(self):
  self.w.adopt_content();p=self.w.context_packet(MEMBER,'first');self.assertEqual(p['scope']['actor'],MEMBER);self.assertEqual(p['modelInput']['opponentCurrentLead'],'UNKNOWN');self.assertEqual(p['modelInput']['authorizedSocialEvidence']['actorID'],MEMBER)
 def test_ram_and_combat_source_unchanged(self):
  r=json.loads((M.parent/'native-memory.json').read_text());self.assertEqual(r['nativeDeltaBytes'],0);self.assertEqual(r['afterRemaining'],4);self.assertTrue(r['allRAMSymbolsIdentical']);self.assertTrue(r['combatSourceIdentical'])
 def test_budget_separate_nonfungible_closed(self):
  with CampaignBudget(Path(self.temp.name)/'requests.json') as b:
   b.authorize_rocket();self.assertEqual(b.read()['maximumAttempts'],50)
   for i in range(36):b.charge('battle',str(i),'verified-free-fixture',str(i))
   with self.assertRaises(WorldError):b.charge('battle','37','verified-free-fixture','37')
   b.close()
   with self.assertRaises(WorldError):b.charge('strategy','closed','verified-free-fixture','closed')
 def test_live_battle_authorization_is_selected_member_only(self):
  from campaign import provider
  path=Path(self.temp.name)/'scoped-requests.json'
  with patch.object(provider,'EXPERIMENT','rocket01'):
   for trainer in (106,348,351,353,414):
    budget_type=provider.scoped_battle_budget({'trainerID':trainer})
    with budget_type(path) as budget:
     with self.assertRaises(ValueError):budget.charge('blocked','verified-free-fixture')
    self.assertFalse(path.exists())
   with CampaignBudget(path) as budget:budget.authorize_rocket()
   with provider.scoped_battle_budget({'trainerID':352})(path) as budget:
    budget.charge('allowed','verified-free-fixture')
    self.assertEqual(len(budget.read()['attempts']),1)
if __name__=='__main__':unittest.main()

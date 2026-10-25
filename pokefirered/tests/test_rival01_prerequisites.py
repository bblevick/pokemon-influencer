"""Offline context/source gates. Native evidence is verified separately."""
import copy,json,tempfile,unittest,sqlite3
from pathlib import Path
from unittest.mock import patch
from strategy.selection import select,load_policy,public_candidates
from campaign.scripted import ScriptedStore
from content.scripted import ScriptedContent
from world.store import dump,WorldError
from campaign.expansion import ExpansionStore
from roster.hashes import digest
R=Path(__file__).resolve().parents[1];A='trainer:fr:trainer:0326';E=R/'evidence/phase8/rival01-prerequisites';M=E/'manifest-native.json'
def row(n,claim=None,**changes):
 return {'claim':claim or {'type':'POKEMON_SEEN','speciesID':n},'evidenceID':'e:'+str(n),'postID':'p:'+str(n),'sourceActor':'trainer:fr:trainer:0102','originalSourceActor':'trainer:fr:trainer:0102','channel':'pokebook','sourceTrainerID':102,'publicationOrder':n,'originStage':'mtmoon','prominence':'ordinary',**changes}
def choose(rows,**kw):return select(rows,{'subjectivePersona':'é日本語'},actor=A,stage='cerulean',opportunity='fixture-opportunity',**kw)
class SelectionTests(unittest.TestCase):
 def test_deterministic_input_permutation(self):
  rows=[row(i) for i in range(1,50)];self.assertEqual(choose(rows),choose(list(reversed(rows))))
 def test_large_history_unicode_complete_records(self):
  rows=[row(i,postID='日本語'+str(i),evidenceID='évidence'+str(i)) for i in range(1,300)];m,a=choose(rows);self.assertLessEqual(len(dump(m).encode('utf-8')),8192);self.assertTrue(m['authorizedSocialEvidence']['truncated']);ids={r['evidenceID'] for r in rows};self.assertTrue(set(a['selectedEvidenceIDs'])<=ids);self.assertEqual(len(a['eligible']),299)
 def test_dedup_same_origin_not_independent_corroboration(self):
  c={'type':'POKEMON_SEEN','speciesID':1,'battleID':'same'};rows=[row(i,c) for i in range(1,5)];m,a=choose(rows);g=m['authorizedSocialEvidence']['claims'][0];self.assertEqual(g['independentOriginCount'],1);self.assertEqual(len(g['references']),1);self.assertEqual(len(a['eligible']),4)
 def test_independent_origin_count_all_retained_not_frequency(self):
  rows=[row(i,{'type':'POKEMON_SEEN','speciesID':1,'battleID':'b'+str(i)}) for i in range(1,5)];m,a=choose(rows);self.assertEqual(m['authorizedSocialEvidence']['claims'][0]['independentOriginCount'],4);self.assertEqual(len(a['groups'][0]['evidenceIDs']),4)
 def test_conflicting_outcomes_atomic_and_linked(self):
  rows=[row(1,{'type':'TRAINER_BATTLE_RESULT','battleID':'b','nativeOutcome':1}),row(2,{'type':'TRAINER_BATTLE_RESULT','battleID':'b','nativeOutcome':2})];m,a=choose(rows);claims=m['authorizedSocialEvidence']['claims'];self.assertEqual(len(claims),2);self.assertTrue(all(c['conflictingClaimIDs'] for c in claims));m,a=choose(rows,evidence_budget=300);self.assertEqual(m['authorizedSocialEvidence']['claims'],[]);self.assertEqual(len(a['eligible']),2)
 def test_private_descriptor_never_looked_up(self):
  class Actor:
   def records(self,**kw):return {'records':[{'source':{'channel':'ROCKET_INTEL','postID':'PRIVATE'},'mode':'delivered'}],'hasMore':False}
  class Store:
   def for_actor(self,actor):return Actor()
   def social_state(self):return {'posts':{}}
   def virality_state(self):return {'epochs':{}}
   def get_battle(self,*a):raise AssertionError('private descriptor lookup')
   def read_public_post(self,*a):raise AssertionError('private exposure lookup')
  self.assertEqual(public_candidates(Store(),A),[])
 def test_private_rejected_before_selection(self):
  with self.assertRaises(WorldError):choose([row(1,channel='ROCKET_INTEL')])
 def test_major_old_event_not_assumed_current(self):
  m,a=choose([row(1,originStage='pewter',prominence='gym'),row(11)]);gym=next(r for r in a['eligible'] if r['prominence']=='gym');self.assertEqual(gym['features']['campaignDistance'],4);self.assertEqual(gym['features']['currentRelevance'],'OLDER');self.assertTrue(gym['selectedReference'])
 def test_new_stage_uses_encounter_not_actor_home(self):
  _,a=choose([row(1,sourceTrainerID=334,originStage='pallet')]);self.assertEqual(a['eligible'][0]['features']['campaignDistance'],0);self.assertEqual(a['eligible'][0]['features']['currentRelevance'],'CURRENT')
 def test_required_base_cannot_silently_clip(self):
  with self.assertRaises(WorldError):select([],{'huge':'x'*9000},actor=A,stage='cerulean',opportunity='o')
 def test_policy_not_mutated_by_budget(self):
  p=load_policy();before=digest(p);choose([row(1)],policy=p,evidence_budget=256);self.assertEqual(digest(p),before)
class RealHostTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name)/'world.sqlite3';src=sqlite3.connect('file:'+str(R/'.local/rocket01/post-rocket-pair.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(self.p);src.backup(dst);dst.close();src.close();self.w=ScriptedStore(self.p,M)
 def tearDown(self):self.w.close();self.t.cleanup()
 def test_real22_full_packet_and_memory_no_mutation(self):
  before=self.w.for_actor(A).records(limit=256)['records'];self.w.adopt_content();rows=public_candidates(self.w,A);self.assertEqual(len(rows),22)
  with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
   p=self.w.context_packet(A);p2=self.w.context_packet(A)
  self.assertEqual(p,p2);self.assertLessEqual(len(dump(p).encode()),8192);self.assertEqual(before,self.w.for_actor(A).records(limit=256)['records']);self.assertEqual(p['modelInput']['opponentCurrentLead'],'UNKNOWN')
  private={r['memoryID'] for r in self.w.virality_state()['intel'].values()};self.assertEqual(len(private),47);self.assertFalse(private&set(p['scope']['selectedEvidenceIDs']));self.assertTrue(all(r['channel']=='pokebook' for r in rows))
 def test_old_context_jobs_immutable_adoption(self):
  old=[tuple(r) for r in self.w.db.execute('SELECT id,context,outcome FROM strategy_jobs')];self.w.adopt_content();self.assertEqual(old,[tuple(r) for r in self.w.db.execute('SELECT id,context,outcome FROM strategy_jobs')])
 def test_native_observer_uses_canonical_family_key(self):
  self.w.adopt_content();seen=[];fake=type('Fake',(),{})();fake._expanded_content=self.w._expanded_content;fake.registry=self.w.registry;fake.locked_preparation=lambda actor:seen.append(actor);ExpansionStore.observe_native_preparation(fake,{'trainerID':334});self.assertEqual(seen,[A])
class SourceTests(unittest.TestCase):
 def test_all_starter_branches_and_source_party(self):
  for starter,native,last in [(0,334,4),(1,333,1),(2,332,7)]:
   c=ScriptedContent.load(starter=starter);t=c.pack['trainers'][A];self.assertEqual(t['sourceTrainer'],native);self.assertEqual(t['originals'][-1]['species'],last);self.assertEqual(t['signatureOrigins'],[str(native)+':3']);self.assertEqual(len(t['originals']),4);self.assertEqual(t['originals'][1]['moves'],[100,0,0,0]);self.assertEqual(len(t['sourceVariants']),27)
 def test_trusted_rival_high_profile_no_rocket(self):
  from virality.policy import plan
  p=json.loads((R/'config/virality_policy.json').read_text());self.assertEqual(p['profiles'][A]['rocketRole'],'none')
  for n in (332,333,334):self.assertEqual(p['sourceActors'][str(n)],A);self.assertEqual(p['eventKinds'][str(n)],'rival')
 def test_zero_permanent_ram(self):
  p=json.loads((E/'native-memory.json').read_text());self.assertEqual(p['nativeDeltaBytes'],0);self.assertGreaterEqual(p['afterRemaining'],4);self.assertTrue(p['allRAMSymbolsIdentical'])

class TerminalCompatibilityTests(unittest.TestCase):
 def test_cerulean_terminal_typed_fixture_and_duplicate(self):
  from test_world01 import flash,msg,BUILD,TAG,SIZES
  from world.saves import fingerprint
  from world.store import WorldStore
  with tempfile.TemporaryDirectory() as d:
   with WorldStore(Path(d)/'world.sqlite3',BUILD,TAG) as w:
    identity=fingerprint(flash(),SIZES);w.import_save(identity);w.authorize_launch(100,identity)
    packets=[msg(1,1,1,trainer=334),msg(2,2,1,trainer=334),msg(3,4,1,trainer=334),msg(4,5,1,trainer=334,outcome=1)]
    for p in packets:w.ingest(p)
    self.assertTrue(w.ingest(packets[-1])['duplicate']);b=next(iter(w.state()['battles'].values()));self.assertEqual(b['trainerID'],'fr:trainer:0326');self.assertEqual(b['sourceTrainerID'],334);self.assertTrue(b['ended']);self.assertTrue(b['defeated']);self.assertEqual(w.state()['trainers']['fr:trainer:0326']['completedBattles'],1)

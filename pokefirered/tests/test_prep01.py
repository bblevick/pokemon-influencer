"""Isolated normal-save/typed-event fixtures, not native Boulder proof."""
import unittest,tempfile,json,struct,copy,sqlite3,sys
from pathlib import Path
from dataclasses import replace
from world.saves import fingerprint
from world.store import WorldError
from prep.store import PrepStore
from prep.progression import read_boulder,FLAGS
from prep.domain import PreparationEnvelope,resolve_preparation_envelope,generate_preparation_candidates,validate_preparation_candidate,current_envelope
from roster.extract import digest
from tests.test_world01 import msg
ROOT=Path(__file__).resolve().parents[1]
LAYOUT=json.load(open(ROOT/'config/prep_save_layout.json'));BUILD=LAYOUT['romSHA256'];TAG=json.load(open(ROOT/'evidence/phase2/pokebook01/manifest-enabled.json'))['build_tag']
RICK='trainer:fr:trainer:0102';DOUG='trainer:fr:trainer:0103';BROCK='trainer:fr:trainer:0414';JANICE='trainer:fr:trainer:0116'

def flash(counter=1,boulder=False):
    sizes=LAYOUT['sectionSizes'];sections={i:bytearray(s) for i,s in enumerate(sizes)}
    block=bytearray(LAYOUT['saveBlock1Bytes'])
    for flag in FLAGS.values():
        if boulder:block[LAYOUT['flagsOffset']+flag//8]|=1<<(flag&7)
    pos=0
    for sid in (1,2,3,4):sections[sid][:]=block[pos:pos+sizes[sid]];pos+=sizes[sid]
    data=bytearray(b'\xff'*131072)
    for sid,payload in sections.items():
        sector=bytearray(4096);sector[:len(payload)]=payload
        total=sum(struct.unpack('<'+'I'*(len(payload)//4),payload))&0xffffffff;crc=((total>>16)+total)&0xffff
        struct.pack_into('<HHII',sector,4084,sid,crc,0x08012025,counter)
        index=(counter%2)*14+sid;data[index*4096:(index+1)*4096]=sector
    return bytes(data)

class PrepTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'test.sqlite3';self.battery=Path(self.tmp.name)/'test.sav'
        self.w=PrepStore(self.path,BUILD,TAG);self.data=flash();self.save=fingerprint(self.data,LAYOUT['sectionSizes']);self.battery.write_bytes(self.data)
        self.w.import_save(self.save);self.w.authorize_launch(100,self.save);self.w.activate_preparation();self.last=0;self.counter=1;self.nonce=100
    def tearDown(self):self.w.close();self.tmp.cleanup()
    def battle(self,trainer=102):
        bid=self.last+1
        for typ in [1,2,6,3,4,5]:
            self.last+=1;self.w.ingest(replace(msg(self.last,typ,battle=bid,trainer=trainer),tag=TAG))
    def checkpoint(self,boulder):
        intent=self.w.begin_save(self.nonce,self.save);self.counter=self.save.counter+1;self.data=flash(self.counter,boulder);self.battery.write_bytes(self.data)
        receipt={'event':'savedataUpdated','nonce':self.nonce,'run':1,'eventCounter':self.last,'ack':self.last,'depth':0,'state':0,'drops':0,'counter':self.counter}
        cp=self.w.finish_save_with_progression(intent,self.battery,receipt);self.save=fingerprint(self.data,LAYOUT['sectionSizes']);return cp
    def eligible(self,trainer=102):
        self.battle(trainer);self.checkpoint(True)
        return resolve_preparation_envelope(self.w,RICK if trainer==102 else DOUG)
    def resign(self,candidate):
        body={k:v for k,v in candidate.items() if k not in ('candidateID','validation','descriptors')}
        candidate['candidateID']='candidate:'+digest(body)
        return candidate

    def test_native_flag_split_and_bad_save(self):
        self.assertFalse(any(read_boulder(flash(),BUILD)['flags'].values()))
        self.assertTrue(all(read_boulder(flash(boulder=True),BUILD)['flags'].values()))
        damaged=bytearray(flash());damaged[14*4096+10]^=1
        with self.assertRaises(ValueError):read_boulder(bytes(damaged),BUILD)
        with self.assertRaises(ValueError):read_boulder(flash(),'0'*64)
    def test_opportunity_before_and_once_after(self):
        self.battle();self.checkpoint(False)
        self.assertIsNone(self.w.get_preparation_opportunity(RICK));self.assertIsInstance(resolve_preparation_envelope(self.w,RICK),dict)
        self.checkpoint(True);first=self.w.get_preparation_opportunity(RICK);self.assertEqual(first['status'],'available')
        self.checkpoint(True);self.assertEqual(first['opportunityID'],self.w.get_preparation_opportunity(RICK)['opportunityID'])
        self.assertEqual(len(self.w.preparation_state()['opportunities']),1)
    def test_reordered_prerequisites(self):
        self.checkpoint(True);self.assertIsNone(self.w.get_preparation_opportunity(RICK));self.battle()
        self.assertEqual(self.w.get_preparation_opportunity(RICK)['status'],'available')
    def test_restart_and_initialization_once(self):
        e=self.eligible();state=self.w.preparation_state();self.w.activate_preparation();self.assertEqual(state,self.w.preparation_state())
        self.w.close();self.w=PrepStore(self.path,BUILD,TAG)
        self.assertEqual(state,self.w.preparation_state());self.assertEqual(e.packet(),resolve_preparation_envelope(self.w,RICK).packet())
    def test_exact_companions_zero_resources_and_query_purity(self):
        state=self.w.preparation_state();c=self.w.get_trainer_companion_state(RICK);r=self.w.get_trainer_resource_state(RICK)
        self.assertEqual([x['level'] for x in c],[6,6]);self.assertEqual([x['species'] for x in c],[13,10]);self.assertEqual(r['stock'],[])
        self.assertTrue(all(x['quantity']==0 for x in r['categories']));self.assertFalse(r['restock'])
        self.assertEqual(state,self.w.preparation_state())
    def test_restore_future_opportunity_and_stale_generation(self):
        self.battle();self.checkpoint(False);early=self.save
        self.checkpoint(True);later=self.save;e=resolve_preparation_envelope(self.w,RICK)
        self.w.restore(early);self.assertIsNone(self.w.get_preparation_opportunity(RICK));self.assertFalse(current_envelope(self.w,e))
        self.w.restore(later);self.assertEqual(self.w.get_preparation_opportunity(RICK)['status'],'available');self.assertFalse(current_envelope(self.w,e))
    def test_divergent_branch_prefix(self):
        self.battle();self.checkpoint(False);early=self.save;branch=self.w.get_active_branch();self.checkpoint(True)
        self.w.restore(early);self.w.authorize_launch(200,early)
        seq=0
        for typ in [1,2,6,3,4,5]:
            seq+=1;self.w.ingest(replace(msg(seq,typ,battle=99,nonce=200),tag=TAG))
        self.assertNotEqual(branch,self.w.get_active_branch());self.assertIsNone(self.w.get_preparation_opportunity(RICK))
    def test_missing_initialization_and_stage(self):
        self.assertEqual(resolve_preparation_envelope(self.w,RICK)['reason'],'preparation_opportunity_unavailable')
        with self.assertRaises(WorldError):self.w.trusted_state('trainer:fr:trainer:0104')
    def test_rick_envelope(self):
        e=self.eligible();self.assertIsInstance(e,PreparationEnvelope);p=e.packet()
        self.assertEqual([v['target'] for v in p['levels'].values()],[10,10]);self.assertEqual(p['budgets']['aggregateMoveChanges'],2);self.assertEqual(p['acquisition']['allowance'],0)
        self.assertEqual(p['resources']['available'],[]);self.assertNotIn('playerParty',json.dumps(p));self.assertTrue(p['evidence']['nativeReceiptIDs'])
    def test_doug_brock_janice(self):
        e=self.eligible(103);self.assertIsInstance(e,PreparationEnvelope);self.assertEqual([v['target'] for v in e.packet()['levels'].values()],[11,11,11])
        brock=resolve_preparation_envelope(self.w,BROCK,'first');self.assertIsInstance(brock,dict) # milestone already awarded
        self.save=fingerprint(flash(),LAYOUT['sectionSizes']);self.w.restore(self.save);self.nonce=201;self.w.authorize_launch(self.nonce,self.save);self.last=0;self.w.activate_preparation();self.checkpoint(False)
        brock=resolve_preparation_envelope(self.w,BROCK,'first');self.assertIsInstance(brock,PreparationEnvelope)
        self.assertEqual(brock.packet()['identityPolicy']['theme']['maximumSupport'],0)
        first=generate_preparation_candidates(brock);self.assertEqual(len(first['candidates']),1)
        altered=copy.deepcopy(first['candidates'][0]);altered['order'].reverse();self.resign(altered)
        self.assertEqual(validate_preparation_candidate(brock,altered,self.w)['reason'],'authored_first_party_order')
        self.checkpoint(True);janice=resolve_preparation_envelope(self.w,JANICE,'first');self.assertIsInstance(janice,PreparationEnvelope)
        self.assertIsNone(self.w.get_preparation_opportunity(JANICE))
    def test_complete_candidates_determinism_and_purity(self):
        e=self.eligible();before=self.w.preparation_state();r=generate_preparation_candidates(e);again=generate_preparation_candidates(e)
        self.assertEqual(r,again);self.assertEqual(before,self.w.preparation_state());self.assertIsNone(r['selectedCandidateID'])
        self.assertGreater(len(r['candidates']),2);self.assertLessEqual(len(r['candidates']),16)
        self.assertEqual([c['species'] for c in r['candidates'][0]['party']],[13,10])
        self.assertTrue(any(c['descriptors']['evolvedCompanions'] for c in r['candidates']))
        self.assertTrue(all(validate_preparation_candidate(e,c,self.w)['valid'] for c in r['candidates']))
    def test_illegal_moves_levels_resources_and_retention(self):
        e=self.eligible();c=generate_preparation_candidates(e)['candidates'][0]
        for mutate in [lambda p:p['party'][0].update(level=11),lambda p:p['party'][0].update(moves=[53,81,0,0]),lambda p:p['party'].pop(),lambda p:p.update(resourceCosts=[[13,1]]),lambda p:p.update(acquisitionCount=1)]:
            bad=copy.deepcopy(c);mutate(bad);self.resign(bad);self.assertFalse(validate_preparation_candidate(e,bad)['valid'])
    def test_stale_after_reservation_and_no_resource_mint(self):
        e=self.eligible();c=generate_preparation_candidates(e)['candidates'][0];oid=e.packet()['scope']['opportunityID']
        with self.assertRaises(WorldError):self.w.reserve_resources(oid,((4,1),),'bad')
        self.w.reserve_resources(oid,(),'empty-reservation')
        with self.assertRaises(WorldError):self.w.reserve_resources(oid,(),'second-reservation')
        self.assertFalse(validate_preparation_candidate(e,c,self.w)['valid']);self.assertEqual(self.w.get_trainer_resource_state(RICK)['stock'],[])
    def test_legacy_writer_refused(self):
        from puppeteer.store import PuppeteerStore
        with self.assertRaises(WorldError):PuppeteerStore(self.path,BUILD,TAG)
    def test_schema_content_mismatch_and_append_only(self):
        with self.assertRaises(sqlite3.DatabaseError):self.w.db.execute('DELETE FROM prep_log')
        self.w.close()
        p=copy.deepcopy(self.w.content.pack);p['version']+=1
        from content.policy import OpeningContent
        content=OpeningContent(p,self.w.content.data,self.w.content.basis,self.w.content.registry)
        with self.assertRaises(WorldError):PrepStore(self.path,BUILD,TAG,content=content)
        self.w=PrepStore(self.path,BUILD,TAG)

    def test_lifecycle_future_consumption_contract_is_pure(self):
        from prep.opportunities import transition,enumerable,OpportunityStatus
        before=self.w.preparation_state();status=OpportunityStatus.UNAVAILABLE
        for event in ['earned','available','reserve','commit','consume']:status=transition(status,event)
        self.assertEqual(status,OpportunityStatus.CONSUMED);self.assertFalse(enumerable(status))
        with self.assertRaises(ValueError):transition(status,'reserve')
        self.assertEqual(transition(status,'rewind'),OpportunityStatus.REWOUND)
        self.assertEqual(before,self.w.preparation_state())

    def test_consumed_opportunity_guard_without_live_commit(self):
        e=self.eligible();state=replace(e.trusted_state,consumed_opportunities=frozenset([e.packet()['scope']['opportunityID']]))
        self.assertEqual(self.w.content.resolve(state,'forest-post-boulder-1')['reason'],'opportunity_already_consumed')
        candidate=generate_preparation_candidates(e)['candidates'][0]
        self.assertFalse(validate_preparation_candidate(replace(e,trusted_state=state),candidate)['valid'])
        # This is a downstream-state fixture, not a team commitment writer.
        self.assertEqual(self.w.get_preparation_opportunity(RICK)['status'],'available')

    def test_envelope_tampering_missing_state_and_invalid_evolution(self):
        e=self.eligible();c=generate_preparation_candidates(e)['candidates'][0]
        packet=e.packet();packet['budgets']['aggregateMoveChanges']=9
        tampered=replace(e,encoded=json.dumps(packet))
        self.assertEqual(validate_preparation_candidate(tampered,c)['reason'],'envelope_integrity_or_version')
        bad=copy.deepcopy(c);lineage=bad['party'][0]['lineage']
        bad['paths'][lineage]=[{'kind':'level','species':13,'level':7,'value':0,'slot':0},{'kind':'evolution','species':15,'level':7,'value':0,'slot':0}]
        bad['party'][0].update(species=15,level=7);bad['validation']={};bad['descriptors']={};self.resign(bad)
        self.assertFalse(validate_preparation_candidate(e,bad)['valid'])
        # A pure missing-state fixture cannot create an optimistic policy result.
        state=replace(e.trusted_state,inventory_initialized=False)
        self.assertEqual(self.w.content.resolve(state,'forest-post-boulder-1')['status'],'missing_trusted_state')

    def test_candidate_metadata_schema_and_each_companion_growth(self):
        e=self.eligible();r=generate_preparation_candidates(e);keys=[]
        for c in e.trusted_state.context.companions:
            self.assertTrue(any(x['lineage']==c.lineage and x['level']==10 for p in r['candidates'] for x in p['party']))
        for c in r['candidates']:
            keys.append(digest([c['party'],c['order'],c['battleItems']]))
            self.assertLessEqual(c['validation']['electiveMoveChanges'],2)
            self.assertTrue(all(not set(x['moves'])&{78,79,16} for x in c['party'] if x['species']==12))
        self.assertEqual(len(keys),len(set(keys)))
        for field in ['validation','descriptors']:
            c=copy.deepcopy(r['candidates'][0]);c[field]['electiveMoveChanges']=100
            self.assertFalse(validate_preparation_candidate(e,c)['valid'])
        bad=copy.deepcopy(r['candidates'][0]);bad['playerParty']=[1]
        self.assertEqual(validate_preparation_candidate(e,bad)['reason'],'candidate_schema')

    def test_aggregate_three_elective_moves_rejected(self):
        from roster.domain import Step
        from prep.domain import _replay
        e=self.eligible();c=generate_preparation_candidates(e)['candidates'][0];owned=e.trusted_state.context.companions
        paths=[(Step('level',13,7),Step('evolution',14,7),Step('level_move',14,7,106,2),Step('level',14,10)),
               (Step('level',10,7),Step('evolution',11,7),Step('level_move',11,7,106,2),Step('level',11,10),Step('evolution',12,10),Step('level_move',12,10,93,3))]
        from dataclasses import asdict
        for index,(partner,path) in enumerate(zip(owned,paths)):
            final=_replay(partner,path);c['paths'][partner.lineage]=[asdict(x) for x in path]
            c['party'][index].update(species=final.species,level=final.level,moves=list(final.moves))
        c['validation']={};c['descriptors']={};self.resign(c)
        self.assertFalse(validate_preparation_candidate(e,c)['valid'])
        self.assertEqual(validate_preparation_candidate(e,c)['reason'],'aggregate_move_change_limit')

    def test_reservation_retry_release_restore_and_finite_exclusion_fixture(self):
        e=self.eligible();early=self.save;oid=e.packet()['scope']['opportunityID']
        reservation=self.w.reserve_resources(oid,(),'idempotent-empty')
        self.assertEqual(reservation,self.w.reserve_resources(oid,(),'idempotent-empty'))
        self.assertTrue(self.w.release_reservation(oid,'idempotent-empty'));self.assertFalse(self.w.release_reservation(oid,'idempotent-empty'))
        with self.assertRaises(WorldError):self.w.reserve_resources(oid,(),'idempotent-empty')
        self.w.restore(early);self.assertFalse(self.w.preparation_state()['reservations'])
        self.assertFalse(current_envelope(self.w,e))
        # Explicit hypothetical finite-stock fixture, never source/production entitlement.
        def fixture():
            self.w._writable();actor=copy.deepcopy(self.w.preparation_state()['actors'][RICK]);actor['resources']['stock']=[[4,1]]
            self.w._append_prep('INITIALIZED','scenario-only-finite-stock',actor)
            for index in [1,2]:self.w._append_prep('EARNED','scenario-only-'+str(index),{'opportunityID':'scenario-only-'+str(index),'actor':RICK,'stage':'scenario-only','scenarioOnly':True})
        self.w._tx(fixture)
        self.w.reserve_resources('scenario-only-1',((4,1),),'scenario-exclusive-1')
        with self.assertRaises(WorldError):self.w.reserve_resources('scenario-only-2',((4,1),),'scenario-exclusive-2')
        self.assertEqual(self.w.get_trainer_resource_state(RICK)['stock'],[[4,1]])

    def test_pairing_failure_rolls_back_progression(self):
        self.battle();before=self.w.preparation_state();intent=self.w.begin_save(self.nonce,self.save)
        self.battery.write_bytes(flash(2,True))
        with self.assertRaises(WorldError):self.w.finish_save_with_progression(intent,self.battery,{'event':'savedataUpdated'})
        self.assertEqual(before,self.w.preparation_state());self.assertIsNone(self.w.get_preparation_opportunity(RICK))

    def test_future_cap_one_two_interfaces_are_scenario_only(self):
        from tests.test_content01_addendum import AdaptationTests
        from prep.domain import resolve_future_acquisition_envelope
        fixtures=AdaptationTests();fixtures.opening=self.w.content;fixtures.rules=self.w.content.adaptation
        for limit in [1,2]:
            ctx,profile=fixtures.inputs(limit)
            envelope=resolve_future_acquisition_envelope(self.w.content,ctx,profile,campaign_acquisitions=0,grants=frozenset(['travel.forest.route2']))
            self.assertEqual(envelope['acquisitionLimit'],limit)
            self.assertEqual(envelope['constraintResult']['remainingAllowance'],limit)
            self.assertEqual(envelope['constraintResult']['conditionalOriginWeights'],{'native':.8,'nearby':.2})
            self.assertFalse(envelope['originSamplerImplemented']);self.assertIsNone(envelope['selectedCandidateID'])
            with self.assertRaises(ValueError):resolve_future_acquisition_envelope(self.w.content,replace(ctx,fixture=False),profile,campaign_acquisitions=0)
            insufficient=resolve_future_acquisition_envelope(self.w.content,replace(ctx,inventory=()),profile,campaign_acquisitions=0)
            self.assertEqual(insufficient['constraintResult']['status'],'prohibited_by_policy')
        self.assertEqual(self.w.content.pack['defaults']['catchBudget'],0)

if __name__=='__main__':unittest.main()

import unittest,json,copy,tempfile,subprocess,sqlite3
from pathlib import Path
from dataclasses import replace
from roster.extract import ROOT,extract,digest,INPUTS,initial_moves
from roster.domain import Catalog,Step,Companion,validate_moveset
from roster.fixtures import RICK,baseline,context,policy,butterfly

class RosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'config/roster_catalog.json').read_text());cls.p=json.loads((ROOT/'config/roster_policy.json').read_text());cls.cat=Catalog(cls.data,cls.p);cls.ids=cls.cat.constants
    def fixture(self,**kw):
        c=Catalog(self.data,policy(self.p,self.cat));return c.bind(context(c,**kw))
    def route(self,species,map='MAP_VIRIDIAN_FOREST',method='land_mons'):
        return next(r['routeID'] for r in self.data['encounters'] if r['species']==self.ids['SPECIES_'+species] and r['map']==map and r['method']==method)
    def test_deterministic_regeneration(self):self.assertEqual(extract(),self.data)
    def test_effective_version(self):
        self.assertTrue(all('_FireRed:' in r['routeID'] for r in self.data['encounters']))
        self.assertGreater(len(self.data['excludedOtherVersion']),0)
        # Deoxys FireRed-specific compiled learnset.
        self.assertIn([30,self.ids['MOVE_SUPERPOWER']],self.cat.lookup('species',self.ids['SPECIES_DEOXYS'])['learnset'])
    def test_reference_integrity(self):
        for s in self.data['species']:
            for l,m in s['learnset']:self.assertTrue(1<=l<=100 and 0<m<len(self.data['moves']))
            for method,param,target in s['evolutions']:
                if method:self.assertTrue(0<target<len(self.data['species']))
        for r in self.data['encounters']:self.assertTrue(0<r['species']<len(self.data['species']) and 1<=r['minLevel']<=r['maxLevel']<=100)
    def test_default_rick(self):
        b=self.cat.own_baseline(RICK,102)
        self.assertEqual([(p['species'],p['level'],p['moves']) for p in b['party']],[(13,6,[40,81,0,0]),(10,6,[33,81,0,0])])
        self.assertTrue(all(p['moveMode']=='default' for p in b['party']))
    def test_brock_custom(self):
        b=self.cat.own_baseline('trainer:fr:trainer:0414',414)
        self.assertEqual(b['party'][1]['moves'],[33,20,317,0]);self.assertEqual(b['party'][1]['moveMode'],'authored')
    def test_alias_sentinels_unused(self):
        self.assertEqual(self.data['species'][0]['learnsetAlias'],self.data['species'][1]['learnsetAlias'])
        self.assertTrue(self.data['items'][52]['unused'])
        for n in [0,self.ids['SPECIES_EGG'],self.ids['SPECIES_OLD_UNOWN_B']]:
            with self.assertRaises(ValueError):self.cat.lookup('species',n)
        with self.assertRaises(ValueError):self.cat.lookup('items',52)
    def test_default_duplicate_algorithm(self):self.assertEqual(initial_moves([[1,33],[1,45],[2,33],[3,81],[4,40],[5,100]],5),[45,81,40,100])
    def test_cross_actor_baseline(self):
        with self.assertRaises(ValueError):self.cat.own_baseline('trainer:fr:trainer:0116',102)
        with self.assertRaises(ValueError):self.cat.bind(context(self.cat,companions=(replace(baseline(self.cat)[0],actor='trainer:fr:trainer:0116'),)))
    def test_narrow_baseline(self):
        v=self.cat.bind(context(self.cat));c=v.ctx.companions[0]
        self.assertEqual(v.move(c.lineage,self.ids['MOVE_POISON_STING']).status,'allowed')
        with self.assertRaises(ValueError):self.cat.bind(context(self.cat,companions=(replace(c,moves=(self.ids['MOVE_SURF'],0,0,0)),)))
        with self.assertRaises(ValueError):self.cat.bind(context(self.cat,companions=(replace(c,origin='116:0'),)))
    def test_production_stage_missing(self):
        v=self.cat.bind(context(self.cat));self.assertEqual(v.growth(v.ctx.companions[0].lineage,7).code,'missing_trainer_stage_target')
    def test_earned_growth_named_gate(self):
        for milestones,epochs,status in [(frozenset(),('e1',),'unqualified'),(frozenset({'badge.boulder'}),(),'blocked'),(frozenset({'badge.boulder'}),('e1',),'allowed')]:
            v=self.fixture(milestones=milestones,earned_epochs=epochs);self.assertEqual(v.growth(v.ctx.companions[0].lineage,10).status,status)
        v=self.fixture(milestones=frozenset({'badge.boulder'}),earned_epochs=('e1',));self.assertEqual(v.growth(v.ctx.companions[0].lineage,11).status,'blocked')
    def test_applied_epoch_no_reuse(self):
        v=self.fixture(milestones=frozenset({'badge.boulder'}),earned_epochs=('e1',),applied_epochs=('e1',));self.assertEqual(v.growth(v.ctx.companions[0].lineage,7).status,'blocked')
    def test_capture_first_epoch(self):
        v=self.fixture(milestones=frozenset({'badge.boulder'}),earned_epochs=('e1',),permissions=frozenset({'capture:land'}),inventory=((4,1),));self.assertEqual(v.acquisition(self.route('CATERPIE')).code,'first_epoch_no_capture')
    def test_native_capture_finite_stock(self):
        for stock,status in [(0,'blocked'),(1,'allowed')]:
            v=self.fixture(milestones=frozenset({'badge.boulder'}),earned_epochs=('e1','e2'),permissions=frozenset({'capture:land'}),inventory=((4,stock),));r=v.acquisition(self.route('CATERPIE'));self.assertEqual(r.status,status)
            if stock:self.assertEqual(r.ids['tier'],'native');self.assertFalse(r.fully_legal)
    def test_nearby_permission(self):
        kwargs=dict(earned_epochs=('e1','e2'),permissions=frozenset({'capture:land'}),inventory=((4,1),))
        v=self.fixture(milestones=frozenset({'badge.boulder'}),**kwargs);self.assertEqual(v.acquisition(self.route('CATERPIE','MAP_ROUTE2')).code,'inaccessible_map')
        v=self.fixture(milestones=frozenset({'badge.boulder','permission.rick.route2'}),**kwargs);self.assertEqual(v.acquisition(self.route('CATERPIE','MAP_ROUTE2')).ids['tier'],'nearby')
    def test_off_region_and_other_version(self):
        v=self.fixture();self.assertEqual(v.acquisition(self.route('PIDGEY','MAP_ROUTE1')).code,'off_region_no_explicit_permission')
        self.assertEqual(v.acquisition(self.route('CATERPIE').replace('_FireRed','_LeafGreen')).code,'unknown_or_other_version_route')
        self.assertEqual(v.acquisition('gift:squirtle').status,'blocked')
        self.assertEqual(v.acquisition_routes(self.ids['SPECIES_BLASTOISE']),())
    def test_capture_permissions_spacing_limits(self):
        base=dict(milestones=frozenset({'badge.boulder'}),earned_epochs=('e1','e2'),inventory=((4,1),))
        self.assertEqual(self.fixture(**base).acquisition(self.route('CATERPIE')).code,'capture_permission_missing')
        self.assertEqual(self.fixture(**base,permissions=frozenset({'capture:land'}),acquisitions=2).acquisition(self.route('CATERPIE')).code,'campaign_acquisition_limit')
        self.assertEqual(self.fixture(**base,permissions=frozenset({'capture:land'}),last_capture_epoch=1).acquisition(self.route('CATERPIE')).code,'capture_spacing')
    def test_water_method_unqualified(self):
        route=next(r['routeID'] for r in self.data['encounters'] if r['method']=='fishing_mons')
        self.assertEqual(self.fixture().acquisition(route).code,'unsupported_acquisition_method')
    def test_owned_evolved_below_threshold(self):
        r=self.route('METAPOD');row=self.cat.routes[r];s=row['species'];l=row['minLevel'];c=Companion('fixture-wild',RICK,r,'wild',l,s,l,tuple(initial_moves(self.data['species'][s]['learnset'],l)))
        v=self.cat.bind(context(self.cat,companions=(c,)));self.assertLess(l,7);self.assertEqual(v.move(c.lineage,c.moves[0]).status,'allowed')
    def test_butterfree_exact_source(self):
        learnset=self.cat.lookup('species',12)['learnset']
        for l,m in [(14,'STUN_SPORE'),(15,'SLEEP_POWDER'),(28,'GUST')]:self.assertIn([l,self.ids['MOVE_'+m]],learnset)
    def test_butterfree_future_boundary(self):
        p=policy(self.p,self.cat,target=29,cap=29,stage='rainbow');cat=Catalog(self.data,p)
        for l,m in [(14,'STUN_SPORE'),(15,'SLEEP_POWDER'),(28,'GUST')]:
            c=butterfly(cat,l-2);v=cat.bind(context(cat,companions=(c,),milestones=frozenset({'badge.rainbow'}),earned_epochs=('e2',),permissions=frozenset({'learn:level'})))
            self.assertEqual(v.move(c.lineage,self.ids['MOVE_'+m],'level_up',level=l-1).status,'blocked')
            self.assertEqual(v.move(c.lineage,self.ids['MOVE_'+m],'level_up',level=l).status,'allowed')
    def test_retention_not_family_union(self):
        c=butterfly(self.cat);v=self.fixture(companions=(c,))
        self.assertEqual(v.move(c.lineage,33).status,'allowed')
        self.assertEqual(v.move(c.lineage,self.ids['MOVE_HARDEN']).status,'blocked')
        self.assertEqual(v.move(c.lineage,self.ids['MOVE_HARDEN'],'level_up',level=14).status,'blocked')
        self.assertEqual(v.move(c.lineage,self.ids['MOVE_CONFUSION'],'level_up',level=10).code,'already_known_not_new_acquisition')
    def test_history_forgery(self):
        c=butterfly(self.cat)
        with self.assertRaises(ValueError):self.cat.bind(context(self.cat,companions=(replace(c,history=c.history+(Step('level_move',12,13,self.ids['MOVE_SURF'],3),)),)))
        with self.assertRaises(ValueError):self.cat.bind(context(self.cat,companions=(replace(c,history=(Step('evolution',12,6),)),)))
    def test_tm_stock_and_permission(self):
        c=butterfly(self.cat);tm=self.ids['ITEM_TM06'];move=self.ids['MOVE_TOXIC']
        for stock,permissions,code in [(1,frozenset(),'machine_permission_missing'),(0,frozenset({'learn:tm'}),'resource_deficit'),(1,frozenset({'learn:tm'}),'machine_acquisition')]:
            v=self.fixture(companions=(c,),inventory=((tm,stock),),permissions=permissions);self.assertEqual(v.move(c.lineage,move,'tm',item=tm).code,code)
        self.assertEqual(self.fixture(companions=(c,),inventory=((tm,1),),permissions=frozenset({'learn:tm'})).move(c.lineage,self.ids['MOVE_FLAMETHROWER'],'tm',item=tm).code,'wrong_machine')
    def test_machine_incompatible_and_unsupported(self):
        v=self.fixture();c=v.ctx.companions[0]
        self.assertEqual(v.move(c.lineage,self.ids['MOVE_TOXIC'],'tm',item=self.ids['ITEM_TM06']).code,'machine_incompatible')
        for method in ('tutor','relearner','breeding'):self.assertEqual(v.move(c.lineage,33,method).status,'unqualified')
    def test_evolution_threshold_growth(self):
        v=self.fixture(milestones=frozenset({'badge.boulder'}),earned_epochs=('e1',),permissions=frozenset({'evolve:level'}));c=v.ctx.companions[1]
        self.assertEqual(v.evolution(c.lineage,11,level=6).status,'blocked');self.assertEqual(v.evolution(c.lineage,11,level=7).status,'allowed');self.assertEqual(v.evolution(c.lineage,12,level=10).code,'not_direct_evolution')
    def test_evolution_item_gate_and_everstone(self):
        # Existing source-authored Pikachu is not a Forest acquisition permission.
        t=next(t for t in self.data['trainers'] if any(p['species']==25 for p in t['party']));companions=baseline(self.cat,t['actorID'],t['id']);c=next(c for c in companions if c.species==25)
        p=copy.deepcopy(self.p);p['fixtureOnly']=True;p['actors'][t['actorID']]={'regions':{},'stages':[{'requires':[],'target':50,'cap':50}],'signatureLineages':[],'theme':None};cat=Catalog(self.data,p)
        ctx=context(cat,scope=replace(context(cat).scope,actor=t['actorID']),companions=companions,permissions=frozenset({'evolve:item'}))
        self.assertEqual(cat.bind(ctx).evolution(c.lineage,26).code,'resource_deficit')
        self.assertEqual(cat.bind(replace(ctx,inventory=((self.ids['ITEM_THUNDER_STONE'],1),))).evolution(c.lineage,26).status,'allowed')
        held=tuple(replace(x,held_item=self.ids['ITEM_EVERSTONE']) if x==c else x for x in companions)
        self.assertEqual(cat.bind(replace(ctx,companions=held)).evolution(c.lineage,26).code,'everstone')
        # Cross-generation gate checked before unsupported friendship/trade method.
        golbat=next(t for t in self.data['trainers'] if any(p['species']==42 for p in t['party']));g=baseline(self.cat,golbat['actorID'],golbat['id']);q=next(x for x in g if x.species==42)
        v=self.cat.bind(context(self.cat,scope=replace(ctx.scope,actor=golbat['actorID']),companions=g));self.assertEqual(v.evolution(q.lineage,169,level=50).code,'national_dex_gate')
    def test_finite_duplicate_allocation(self):
        tm=self.ids['ITEM_TM06'];v=self.fixture(inventory=((tm,1),),permissions=frozenset({'allocate:teaching'}));self.assertEqual(v.allocations((('teaching',tm,1),)).status,'allowed');self.assertEqual(v.allocations((('teaching',tm,1),('teaching',tm,1))).status,'blocked')
    def test_held_bag_categories(self):
        potion=self.ids['ITEM_POTION'];v=self.fixture(inventory=((potion,2),),permissions=frozenset({'allocate:held','allocate:battle_bag'}))
        self.assertEqual(v.allocations((('held',potion,1),)).code,'not_supported_held_effect');self.assertEqual(v.allocations((('battle_bag',potion,1),)).code,'NPC_item_execution_not_qualified')
    def test_moveset_slots_and_edit_budget(self):
        v=self.fixture();c=v.ctx.companions[1]
        self.assertEqual(validate_moveset(v,c.lineage,c.moves,{}).status,'allowed')
        self.assertEqual(validate_moveset(v,c.lineage,(33,33,0,0),{}).code,'duplicate_moves')
        self.assertEqual(validate_moveset(v,c.lineage,(1,2,3,4),{}).code,'move_change_budget')
    def test_identity_retention(self):
        v=self.fixture();cs=v.ctx.companions
        self.assertEqual(v.identity(tuple(c.lineage for c in cs),tuple(c.species for c in cs)).status,'allowed');self.assertEqual(v.identity((cs[0].lineage,),(cs[0].species,)).code,'original_lineage_removal')
    def test_gym_unknown_vs_bounded_mixed_fixture(self):
        actor='trainer:fr:trainer:0414';cs=baseline(self.cat,actor,414);ctx=context(self.cat,scope=replace(context(self.cat).scope,actor=actor),companions=cs)
        self.assertEqual(self.cat.bind(ctx).identity(tuple(c.lineage for c in cs),tuple(c.species for c in cs)).code,'missing_gym_support_bounds')
        p=copy.deepcopy(self.p);p['fixtureOnly']=True;p['actors'][actor]['theme']['mixedSupportLimit']=1;p['actors'][actor]['signatureLineages']=[cs[1].lineage];v=Catalog(self.data,p).bind(ctx)
        # Identity check reports lawful theme feasibility but new acquisition remains unqualified.
        self.assertEqual(v.identity(tuple(c.lineage for c in cs)+('support',),tuple(c.species for c in cs)+(12,)).code,'new_lineage_requires_acquisition_and_PREP_validation')
        self.assertEqual(v.identity(tuple(c.lineage for c in cs)+('a','b'),tuple(c.species for c in cs)+(12,25)).code,'gym_theme_support_limit')
    def test_bad_ids_scope_and_stock(self):
        for n in [True,-1,99999,'12']:
            with self.assertRaises(ValueError):self.cat.lookup('species',n)
        for kw in [dict(inventory=((4,-1),)),dict(earned_epochs=('a','a')),dict(applied_epochs=('fake',))]:
            with self.assertRaises(ValueError):self.cat.bind(context(self.cat,**kw))
        with self.assertRaises(ValueError):self.cat.bind(context(self.cat,scope=replace(context(self.cat).scope,branch='')))
    def test_fixture_cannot_be_live(self):
        cat=Catalog(self.data,policy(self.p,self.cat))
        with self.assertRaises(ValueError):cat.bind(replace(context(cat),fixture=False))
    def test_old_restore_changes_results_no_cache(self):
        c=Catalog(self.data,policy(self.p,self.cat));early=context(c);late=replace(early,milestones=frozenset({'badge.boulder'}),earned_epochs=('e1','e2'),permissions=frozenset({'capture:land'}),inventory=((4,1),),scope=replace(early.scope,restore_epoch=1,cutoff=100));r=self.route('CATERPIE')
        self.assertEqual(c.bind(late).acquisition(r).status,'allowed');self.assertNotEqual(c.bind(early).acquisition(r).status,'allowed')
        self.assertNotEqual(c.bind(late).acquisition(r).provenance['contextSHA256'],c.bind(early).acquisition(r).provenance['contextSHA256'])
    def test_query_no_database_or_hidden_state(self):
        v=self.fixture();before=digest(self.data);ctx=v.ctx
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'untouched.sqlite3';db=sqlite3.connect(path);db.execute('create table sentinel(value)');db.execute('insert into sentinel values(1)');db.commit();db.close();raw=path.read_bytes()
            for c in ctx.companions:v.move_paths(c.lineage);v.growth(c.lineage,10)
            v.acquisition_routes(10)
            self.assertEqual(path.read_bytes(),raw)
        self.assertEqual(v.ctx,ctx);self.assertEqual(digest(self.data),before)
        # There is no opponent/memory/post/RNG/hidden-party input field.
        self.assertNotIn('player',ctx.__dataclass_fields__)
    def test_preparation_consumer_contract(self):
        v=self.fixture(milestones=frozenset({'badge.boulder'}),earned_epochs=('e1',),permissions=frozenset({'evolve:level'}));r=v.evolution(v.ctx.companions[1].lineage,11,level=7).packet()
        self.assertEqual(r['status'],'allowed');self.assertFalse(r['fully_legal']);self.assertEqual(r['provenance']['scope']['actor'],RICK);self.assertEqual(r['provenance']['catalogSHA256'],self.cat.hash)
        import jsonschema
        jsonschema.validate(r,json.loads((ROOT/'schemas/roster/eligibility.schema.json').read_text()))
    def mirror(self,tmp):
        root=Path(tmp);paths=set(INPUTS+['config/phase0.lock.json'])|{str(p.relative_to(ROOT)) for p in (ROOT/'include/constants').glob('*.h')}
        (root/'.git').symlink_to(ROOT/'.git',target_is_directory=True)
        for path in paths:
            target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(ROOT/path)
        return root
    def test_ui_unrelated_and_mechanics_freshness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.mirror(tmp);(root/'src/pi_pokebook.c').write_text('unrelated UI change')
            self.assertEqual(extract(root)['catalogSHA256'],self.cat.hash)
            path=root/'src/data/pokemon/level_up_learnsets.h';source=path.read_text();path.unlink();path.write_text(source.replace('LEVEL_UP_MOVE(14, MOVE_STUN_SPORE)','LEVEL_UP_MOVE(16, MOVE_STUN_SPORE)'))
            changed=extract(root);self.assertNotEqual(changed['catalogSHA256'],self.cat.hash);self.assertIn([16,self.ids['MOVE_STUN_SPORE']],changed['species'][12]['learnset'])
        p=copy.deepcopy(self.p);p['version']=2;self.assertNotEqual(Catalog(self.data,p).policy_hash,self.cat.policy_hash)
    def test_unresolved_syntax_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.mirror(tmp);path=root/'src/data/pokemon/tmhm_learnsets.h';text=path.read_text();path.unlink();path.write_text(text.replace('TMHM(TM06_TOXIC)','TMHM(NOT_A_MACHINE)',1))
            with self.assertRaises(subprocess.CalledProcessError):extract(root)
    def test_unknown_generator_change_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.mirror(tmp);path=root/'src/data/wild_encounters.json.txt';text=path.read_text();path.unlink();path.write_text(text+'\n// unreviewed generator\n')
            with self.assertRaisesRegex(ValueError,'generator/config'):extract(root)
    def test_unknown_acquisition_history_is_not_unlimited(self):
        v=self.fixture(milestones=frozenset({'badge.boulder'}),earned_epochs=('e1','e2'),permissions=frozenset({'capture:land'}),inventory=((4,1),),acquisitions=None)
        self.assertEqual(v.acquisition(self.route('CATERPIE')).code,'missing_acquisition_history')
    def test_hm_reusable_and_move_proof_id_not_grant(self):
        hm=self.ids['ITEM_HM05'];v=self.fixture(inventory=((hm,1),),permissions=frozenset({'allocate:teaching'}))
        self.assertEqual(v.allocations((('teaching',hm,1),('teaching',hm,1))).status,'allowed')
        c=butterfly(self.cat);v=self.fixture(companions=(c,))
        self.assertEqual(validate_moveset(v,c.lineage,(33,81,93,self.ids['MOVE_TOXIC']),{self.ids['MOVE_TOXIC']:{'method':'tm','item':self.ids['ITEM_TM06'],'witness':'fake'}}).code,'missing_or_unknown_move_path')
    def test_two_actors_information_has_no_feasibility_input(self):
        # Social exposure cannot widen territory/inventory/epochs: only the trusted
        # preparation snapshot is an input; no belief/post selector exists here.
        c=self.fixture();before=[r.packet() for r in c.acquisition_routes(10)]
        unrelated_social_fixture={'janiceSawRick':True,'reportedPlayerSpecies':4}
        self.assertTrue(unrelated_social_fixture['janiceSawRick'])
        self.assertEqual(before,[r.packet() for r in c.acquisition_routes(10)])

    def test_theme_only_partial_proof(self):
        p=copy.deepcopy(self.p);p['fixtureOnly']=True;p['actors']['trainer:fr:trainer:0414']['theme']['mixedSupportLimit']=1
        cat=Catalog(self.data,p);ctx=context(cat,scope=replace(context(cat).scope,actor='trainer:fr:trainer:0414'),companions=baseline(cat,'trainer:fr:trainer:0414',414));v=cat.bind(ctx)
        self.assertEqual(v.theme((74,95,12)).status,'allowed');self.assertFalse(v.theme((74,95,12)).fully_legal)
        self.assertEqual(v.theme((74,95,12,25)).status,'blocked')

    def test_missing_array_terminator_fails_without_overread(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.mirror(tmp);path=root/'src/data/pokemon/level_up_learnsets.h';text=path.read_text();path.unlink();path.write_text(text.replace('    LEVEL_UP_END','',1))
            with self.assertRaises(subprocess.CalledProcessError):extract(root)
    def test_unknown_effective_conditional_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.mirror(tmp);path=root/'src/data/pokemon/level_up_learnsets.h';text=path.read_text();path.unlink();path.write_text('#if defined(UNREVIEWED_GAME_RULE)\n#error unsupported\n#endif\n'+text)
            with self.assertRaisesRegex(ValueError,'table condition'):extract(root)

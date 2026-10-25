#!/usr/bin/env python3
"""Auditable host-only qualification cases; never imports a live campaign."""
import json,sys
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from roster.extract import file_hash,digest
from roster.domain import Catalog,asdict_context
from roster.fixtures import context,policy,baseline,butterfly,RICK

def generate():
    data=json.loads((ROOT/'config/roster_catalog.json').read_text());p=json.loads((ROOT/'config/roster_policy.json').read_text());cat=Catalog(data,p);s=cat.constants
    v=cat.bind(context(cat));c=v.ctx.companions[1]
    reports={'A_rick_baseline':{'label':'source-authored baseline, no native party mutation','trainer':v.baseline(102)},'production_growth_gap':v.growth(c.lineage,7).packet()}
    qualified=Catalog(data,policy(p,cat,target=10,cap=14));q=qualified.bind(context(qualified,milestones=frozenset({'badge.boulder'}),earned_epochs=('boulder-fixture-epoch',),permissions=frozenset({'evolve:level','learn:level'})))
    reports['B_fixture_level_evolution']=q.evolution(c.lineage,s['SPECIES_METAPOD'],level=7).packet()
    reports['B_fixture_growth']=q.growth(c.lineage,10).packet()
    reports['C_dramatic_counter_rejected']=q.acquisition('unqualified:starter:squirtle').packet()
    bp=policy(p,cat,target=21,cap=21,stage='cascade');bc=Catalog(data,bp);b=butterfly(bc,13)
    bv=bc.bind(context(bc,companions=(b,),milestones=frozenset({'badge.cascade'}),earned_epochs=('cascade-fixture-epoch',),permissions=frozenset({'learn:level','learn:tm','allocate:teaching'}),inventory=((s['ITEM_TM06'],1),)))
    reports['D_sleep_powder_below']=bv.move(b.lineage,s['MOVE_SLEEP_POWDER'],'level_up',level=14).packet()
    reports['D_sleep_powder_at_15']=bv.move(b.lineage,s['MOVE_SLEEP_POWDER'],'level_up',level=15).packet()
    reports['D_retained_pre_evolution_tackle']=bv.move(b.lineage,s['MOVE_TACKLE']).packet()
    reports['E_owned_TM06']=bv.move(b.lineage,s['MOVE_TOXIC'],'tm',item=s['ITEM_TM06']).packet()
    reports['E_zero_TM06']=bc.bind(replace(bv.ctx,inventory=())).move(b.lineage,s['MOVE_TOXIC'],'tm',item=s['ITEM_TM06']).packet()
    reports['E_duplicate_TM06']=bv.allocations((('teaching',s['ITEM_TM06'],1),('teaching',s['ITEM_TM06'],1))).packet()
    catch=qualified.bind(context(qualified,milestones=frozenset({'badge.boulder','permission.rick.route2'}),earned_epochs=('fixture-1','fixture-2'),permissions=frozenset({'capture:land'}),inventory=((s['ITEM_POKE_BALL'],1),)))
    for tier,mapname in [('native','MAP_VIRIDIAN_FOREST'),('nearby','MAP_ROUTE2')]:
        r=next(r for r in data['encounters'] if r['species']==10 and r['map']==mapname)
        reports['B_fixture_'+tier+'_attempt']=catch.acquisition(r['routeID']).packet()
    brock='trainer:fr:trainer:0414';cs=baseline(cat,brock,414);scope=replace(v.ctx.scope,actor=brock)
    gv=cat.bind(context(cat,scope=scope,companions=cs));reports['F_brock_baseline']=gv.baseline(414);reports['F_gym_bounds_missing']=gv.identity(tuple(c.lineage for c in cs),tuple(c.species for c in cs)).packet()
    discrepancies=[]
    for t in data['trainers']:
        for mon in t['party']:
            if mon['moveMode']!='authored':continue
            at_level={m for l,m in data['species'][mon['species']]['learnset'] if l<=mon['level']}
            for slot,move in enumerate(mon['moves']):
                if move and move not in at_level:discrepancies.append({'trainer':t['id'],'actor':t['actorID'],'baselineKey':mon['baselineKey'],'species':mon['species'],'moveSlot':slot,'move':move,'level':mon['level'],'handling':'retain exact authored baseline only; no general learning/acquisition grant','note':'not necessarily mechanically illegal; TM/tutor or other authored source may explain it'})
    report={'schemaVersion':1,'fixtureOnly':True,'catalogSHA256':cat.hash,'productionPolicySHA256':cat.policy_hash,'reports':reports,'fixturePolicies':{q.cat.policy_hash:q.cat.policy,bv.cat.policy_hash:bv.cat.policy},'trustedFixtureContexts':{k:asdict_context(view.ctx) for k,view in [('baseline',v),('boulder',q),('cascade',bv),('capture',catch),('gym',gv)]},'baselineRetentionDiagnostics':discrepancies,'noMutation':True,'noInference':True}
    import jsonschema
    schema=json.loads((ROOT/'schemas/roster/eligibility.schema.json').read_text())
    for r in reports.values():
        if 'status' in r:jsonschema.validate(r,schema)
    return report
if __name__=='__main__':
    target=ROOT/'evidence/phase3/roster01/examples.json';data=generate();target.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'reports':len(data['reports']),'baselinePropertiesNotInAtLevelLearnset':len(data['baselineRetentionDiagnostics'])}))

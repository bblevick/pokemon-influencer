#!/usr/bin/env python3
"""Verify recorded VIRALITY host evidence; never invokes models/emulator."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from world.store import dump
from virality import policy
import jsonschema


def main():
    e=ROOT/'evidence/phase4/virality01';checks=[]
    def read(name):return json.loads((e/(name+'.json')).read_text())
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    config=json.loads((ROOT/'config/virality_policy.json').read_text());registry=json.loads((ROOT/'config/trainer_registry.json').read_text());policy.validate(config,registry);checks.append('source-bound versioned policy')
    p=read('brock-production');ctx=p['brockStrategyContext'];post=p['publicPost'];packet=ctx['authorizedFacts']
    check('two published claims exactly',len(packet)==2 and sorted(dump(x['claim']) for x in packet)==sorted(map(dump,post['claims'])))
    check('private Tackle excluded','moveID' not in dump(ctx));check('actor-only scoped Brock',ctx['actorID']=='trainer:fr:trainer:0414')
    check('unread delivery retained as evidence',all(not f['seen'] for f in p['unreadBrockFeed']))
    schema=json.loads((ROOT/'schemas/social/evidence_quality.schema.json').read_text())
    for r in packet:
        jsonschema.validate(r['evidenceQuality'],schema)
        check('public original source '+r['claim']['type'],r['mode']=='delivered' and r['attribution']['kind']=='published_post' and r['evidenceQuality']['sourceQuality']=='HIGH' and r['evidenceQuality']['originalSourceActor']==post['author'])
    check('no strategic conclusion',ctx['strategicInterpretation'] is None and ctx['strategyMemoSubjective'] is None)
    fixtures=read('follower-fixtures');audiences=[{r['recipient'] for r in f['deliveries']} for f in fixtures]
    check('labeled follower fixtures',all(f['fixture'] for f in fixtures));check('0/5/20 counts',[f['followerCount'] for f in fixtures]==[0,5,20]);check('monotonic audiences',audiences[0]<=audiences[1]<=audiences[2]);check('near Doug low reach','trainer:fr:trainer:0103' in audiences[0]);check('far Sally excluded low included high','trainer:fr:trainer:0117' not in audiences[0] and 'trainer:fr:trainer:0117' in audiences[2])
    check('no quota fill',[sum(r['reason']=='ordinary_discovery' for r in f['deliveries']) for f in fixtures]==[2,12,25])
    prominence=read('prominence-fixtures');check('all native prominent classes at zero followers',{x['prominence'] for x in prominence}=={'ordinary','gym','rival','elite_four','champion','rocket_leader'} and all(x['followerCount']==0 for x in prominence));check('high-profile broader than low-fame ordinary',all(len(x['deliveries'])>len(prominence[0]['deliveries']) for x in prominence[1:]))
    check('accepted native writer composition preserved',read('battle-composition')['sourceUnchanged'] and read('battle-composition')['viralityInitiallyInactive'])
    rocket=read('rocket-fixture');check('Rocket explicitly fixture',rocket['fixture'] and not rocket['nativeItemObservationExportQualified']);check('complete four observed internal claims',[x['claim'] for x in rocket['internalIntelligence']]==[x['claim'] for x in rocket['observations']] and len(rocket['observations'])==4);check('public only Bulbasaur',rocket['publicClaims']==[rocket['observations'][0]['claim']]);check('private channel fidelity',all(x['channel']=='ROCKET_INTEL' for x in rocket['internalIntelligence']))
    production=read('production-checks');check('21 production assertions',production['count']==21 and len(production['checks'])==21);check('no live expansion',production['hostedCalls']==production['newEmulatorRuns']==production['newROMSaves']==0)
    check('all prior protected inputs unchanged',read('protected-verification')['passed']);check('accepted native ROM unchanged',read('native-protection')['unchanged'])
    text=(e/'focused-tests.log').read_text();check('30 focused zero-skip tests','Ran 30 tests' in text and text.rstrip().endswith('OK') and 'skipped' not in text)
    result={'checks':checks,'count':len(checks),'passed':True,'hostOnly':True};(e/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'artifactChecks':len(checks),'passed':True}))

if __name__=='__main__':main()

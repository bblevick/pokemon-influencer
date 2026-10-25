#!/usr/bin/env python3
"""Retained NEW MEMORY live evidence checks, not a new emulator playthrough."""
import hashlib
import json
from pathlib import Path
from memory01 import ROOT, E, manifest, offline_store, snapshot, save_identity


def main():
    checks = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)
    def read(name):
        return json.loads((E / name).read_text())
    m = manifest()
    a = read('rick-live.json'); restart = read('host-reopen.json')
    d = read('targeted-delivery.json'); b = read('divergent-branch.json')
    restored = read('restored-s1-field.json'); final = read('s2-positive-reload.json')
    check('unchanged accepted B3 ROM', m['rom_sha256'] == '739bd3eebb91aaa5210f8f8cd1f357a8272dc98db7060356c649b4c38a0dbc2d')
    check('new live launch origin', a['rick']['directObservations'][0]['claim']['battleID'] != '71dee5f7568b6181f2fc3db02014db08a6ed7fde6ee790cc21f45452c2a87e9f')
    check('Rick stable registry identity', a['rick']['actor']['actorID'] == 'trainer:fr:trainer:0102')
    check('Janice actual source family', a['janice']['actor']['primarySourceID'] == 116)
    check('Janice zero direct and delivered before fixture', not a['janice']['directObservations'] and not a['janice']['deliveries'])
    claims = {r['claim']['type']: r['claim'] for r in a['rick']['directObservations']}
    check('four whitelisted compact Rick claims', set(claims) == {'BATTLE_PARTICIPATION','TRAINER_BATTLE_RESULT','POKEMON_SEEN','MOVE_REVEALED'})
    check('actual trainer loss', claims['TRAINER_BATTLE_RESULT']['nativeOutcome'] == 1)
    check('only revealed Bulbasaur', claims['POKEMON_SEEN']['speciesID'] == 1)
    check('only revealed Tackle', claims['MOVE_REVEALED']['moveID'] == 33)
    check('canonical/raw/evidence separation', a['counts'] == dict(events=27, observations=8, memory_evidence=25))
    check('new host restart identical', a == restart)
    check('one delivered claim only', len(d['snapshot']['janice']['deliveries']) == 1 and not d['snapshot']['janice']['directObservations'])
    check('delivered result matches source', d['snapshot']['janice']['deliveries'][0]['claim'] == claims['TRAINER_BATTLE_RESULT'])
    check('delivery distinct from firsthand', [r['mode'] for r in d['provenance']] == ['delivered','direct'])
    check('delivery origin same single claim', all(r['claim'] == claims['TRAINER_BATTLE_RESULT'] for r in d['provenance']))
    check('fixture duplicate idempotent', d == read('duplicate-delivery.json'))
    check('restored S1 exact cursor and deferred fork', restored['campaign']['cursor'] == 0 and restored['campaign']['pending_fork'] == 1)
    check('Rick future inactive after native S1 Continue', not restored['rick']['directObservations'])
    check('Janice future delivery inactive after S1 Continue', not restored['janice']['deliveries'])
    check('live new canonical branch', b['campaign']['active_branch'] != a['campaign']['active_branch'] and b['campaign']['cursor'] == 1)
    check('divergent B no inherited Rick or Janice evidence', not b['rick']['directObservations'] and not b['janice']['deliveries'])
    audit = read('branch-audit.json')
    check('A retained historical memory and B empty', audit['inactiveARecords'] == 26 and audit['BRecords'] == 0)
    check('B subjective parent cutoff zero', audit['memoryForkCutoffs'][1]['parent_cutoff'] == 0)
    check('positive native S2 reload same Rick context', final['rick'] == d['snapshot']['rick'])
    check('positive native S2 reload only delivered Janice result', final['janice'] == d['snapshot']['janice'])
    for name in ('offline-fixture-replay.json','divergent-offline-replay.json','final-offline-replay.json'):
        check(name, read(name)['passed'])
    check('legacy migration canonical schema preserved', read('legacy-migration.json')['canonicalSchema'] == 1)
    with offline_store(ROOT / '.local/memory01/world.sqlite3') as w:
        check('final authoritative database matches snapshot', snapshot(w) == final)
        check('canonical one Rick defeat', w.state()['trainers']['fr:trainer:0102']['defeats'] == 1)
        check('both histories retained', len(w.db.execute('SELECT * FROM branches').fetchall()) == 2)
        check('no pending save operation', w.pending_save() is None)
        check('subjective schema/reducer pins', [tuple(r) for r in w.db.execute('SELECT * FROM memory_version')] == [(1,1)])
        for label, counter, cursor, cutoff in [('S1',6,0,0),('S2',7,27,26)]:
            identity = save_identity(ROOT / ('.local/memory01/'+label+'.sav'))
            cp = w.get_save_checkpoint(identity.fingerprint)
            check(label+' native validated counter/checkpoint', identity.counter == counter and cp['cursor'] == cursor and cp['kind'] == 'normal_save')
            check(label+' subjective checkpoint cutoff', w._one('SELECT cutoff FROM memory_checkpoints WHERE checkpoint=?',(cp['id'],))['cutoff'] == cutoff)
        rick = w.for_actor('trainer:fr:trainer:0102'); janice = w.for_actor('trainer:fr:trainer:0116')
        for record in rick.records()['records']:
            table = 'events' if record['source']['kind'] == 'event' else 'observations'
            source = w._one('SELECT * FROM '+table+' WHERE id=?',(record['source']['id'],))
            check('resolvable direct source '+record['memoryID'], source is not None)
            raw = json.loads(source['record']); claim = record['claim']; p = raw['payload']
            if claim['type'] == 'POKEMON_SEEN':
                check('actually seen species '+record['memoryID'], claim['speciesID'] == p['opponentActive']['revealedSpeciesID'])
            elif claim['type'] == 'MOVE_REVEALED':
                permitted = p['opponentActive']['revealedMoveIDs'] if table == 'observations' else [p['announcedMoveID']] if p['actorSide'] == 0 and p['resolutionKind'] == 'announced_move' else []
                check('actually revealed move '+record['memoryID'], claim['moveID'] in permitted)
            check('actor evidence minimal fields '+record['memoryID'], set(claim) <= {'type','battleID','trainerID','nativeOutcome','speciesID','moveID'})
        private_move = next(r for r in rick.records()['records'] if r['claim']['type']=='MOVE_REVEALED')
        try:
            janice.provenance(private_move['memoryID'])
        except ValueError:
            check('Janice cannot retrieve unrelated Rick provenance', True)
        else:
            check('Janice cannot retrieve unrelated Rick provenance', False)
    launches = [json.loads(x) for x in (E/'launches.jsonl').read_text().splitlines()]
    check('three fresh process battery launches', len(launches)==3 and len({x['origin'] for x in launches})==3)
    check('no inference credentials in launch reports', all(x['credentialsUsed'] is False for x in launches))
    receipts = [json.loads(x) for x in (E/'save-receipts.jsonl').read_text().splitlines()]
    check('new native save lifecycle receipts', [r['counter'] for r in receipts]==[6,7] and all(r['drops']==r['depth']==r['state']==0 and r['ack']==r['eventCounter'] for r in receipts))
    shots = ('fresh-field','memory-s1-prompt-reviewed','rick-battle-ready','battle-reviewed','rick-victory-field','memory-s2-complete','s1-restored-field','divergent-wild-walk-12','s2-reviewed-field')
    check('actual private screenshot artifacts', all((ROOT/'evidence/private/memory01'/(s+'.png')).is_file() for s in shots))
    check('final prior regressions passed', read('regressions/results.json')['passed'])
    report = {'ticket':'MEMORY-01','passed':True,'assertions':len(checks),'checks':checks,'romSHA256':m['rom_sha256'],'classification':'retained NEW MEMORY live play/host fixture and source evidence, not a new playthrough'}
    (E/'emulator-integration.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':True,'assertions':len(checks),'report':str(E/'emulator-integration.json')},indent=2))


if __name__ == '__main__':
    main()

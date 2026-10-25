#!/usr/bin/env python3
"""Read-only closeout of retained Rocket history and discard-only qualification."""
import json
import subprocess
import sys
import sqlite3
import copy
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from rocket01_hermes_qualify import sha, logical_database_hash

E = ROOT / 'evidence/phase7/rocket01'
D = E / 'hermes-disposition'
def read(path):
    return json.loads(path.read_text())

def main():
    before = read(E / 'hermes-disposition-before.json')
    after = read(E / 'hermes-disposition-after.json')
    restart = read(E / 'disposition-verified-restored.json')
    stable = ('campaign', 'checkpoint', 'save', 'hashes', 'world', 'social',
              'puppeteer', 'virality', 'memos', 'decisions', 'actors',
              'actorRecords', 'audit', 'lifecycle', 'leadershipStrategyKnowledgePreview')
    qualification_unchanged = {k: before[k] == after[k] for k in stable}
    normalized = copy.deepcopy(restart)
    for actor in normalized['actors']:
        for key in ('socialEpoch', 'puppeteerEpoch'):
            assert normalized['actors'][actor]['cutoffs'][key] == before['actors'][actor]['cutoffs'][key] + 2
            normalized['actors'][actor]['cutoffs'][key] = before['actors'][actor]['cutoffs'][key]
    assert normalized['leadershipStrategyKnowledgePreview']['scope']['restoreEpoch'] == before['leadershipStrategyKnowledgePreview']['scope']['restoreEpoch'] + 2
    normalized['leadershipStrategyKnowledgePreview']['scope']['restoreEpoch'] = before['leadershipStrategyKnowledgePreview']['scope']['restoreEpoch']
    restart_unchanged = {k: before[k] == normalized[k] for k in stable}
    assert all(qualification_unchanged.values()) and all(restart_unchanged.values())
    qualified = read(D / 'qualification.json')
    assert qualified['valid'] and not qualified['committed']
    assert qualified['workingDatabaseBytesUnchangedDuringQualification']
    assert qualified['fixtureProjectionHashesUnchanged']
    assert not Path(qualified['record']['runtimeHome']).exists()
    ledger = read(E / 'requests.json')
    prior = read(D / 'prior-requests.json')
    assert ledger['closed'] and len(ledger['attempts']) == 20
    assert ledger['attempts'][:16] == prior['attempts']
    new = ledger['attempts'][16:]
    assert all(r['role'] == 'puppeteer' and r['jobID'].startswith('qualification:')
               and r['verifiedFree'] and r['outcome']['committed'] is False
               and r['outcome']['usage']['cost'] == 0 for r in new)
    verification = read(D / 'verification.json')
    assert verification['directReceiptCount'] == verification['privateReceiptCount'] == 47
    assert verification['publicClaimCount'] == 2
    assert verification['automaticRetryNoDuplicate'] and verification['postRestoreSevenHashesExact']
    assert all(r['futureObservationsPostIntelAbsent'] and r['lateDeliveryScopeDenied']
               for r in verification['rollback'])
    memory = read(E / 'native-memory.json')
    assert memory['nativeDeltaBytes'] == 0 and memory['afterRemaining'] >= 4
    assert read(ROOT / 'config/model_profiles.yaml')['hosted_inference_enabled'] is False
    processes = subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True)
    owned = [line for line in processes.splitlines()
             if ('tools/rocket01.py host' in line or '.local/mGBA.app/Contents/MacOS/mGBA' in line
                 or str(qualified['record']['runtimeHome']) in line)]
    assert not owned, owned
    expected = read(D / 'preserved-files.json')
    preserved = {p: sha(ROOT / p) == h for p, h in expected.items()
                 if p not in ('.local/rocket01/world.sqlite3', 'evidence/phase7/rocket01/requests.json')}
    assert all(preserved.values())
    changed = {}
    permitted = {'launches', 'social_view', 'puppeteer_view', 'prep_view',
                 'strategy_view', 'preparation_decision_view', 'virality_view'}
    with closing(sqlite3.connect('file:' + str(ROOT / '.local/rocket01/post-rocket-pair.sqlite3') + '?mode=ro', uri=True)) as b, closing(sqlite3.connect('file:' + str(ROOT / '.local/rocket01/world.sqlite3') + '?mode=ro', uri=True)) as a:
        assert a.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall() == b.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()
        for name, in b.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            x = b.execute('SELECT * FROM "' + name + '" ORDER BY rowid').fetchall()
            y = a.execute('SELECT * FROM "' + name + '" ORDER BY rowid').fetchall()
            if x != y:
                assert name in permitted, name
                if name == 'launches':
                    assert len(y) == len(x) + 2
                    assert all(p == q or (p[:-1] == q[:-1] and p[-1] == 'active' and q[-1] == 'inactive') for p, q in zip(x, y))
                    assert all(r[2:4] == x[-1][2:4] for r in y[len(x):])
                else:
                    assert len(x) == len(y) == 1 and x[0][:-1] == y[0][:-1] and y[0][-1] == x[0][-1] + 2
                changed[name] = {'before': len(x), 'after': len(y), 'kind': 'fresh offline restore launch/epoch only'}
    shots = ['disposition-verified-field', 'disposition-pokebook-home',
             'disposition-pokebook-last-page', 'disposition-pokebook-grunt',
             'disposition-pokebook-followers', 'disposition-verified-final-field']
    assert all((ROOT / 'evidence/private/rocket01' / (s + '.png')).is_file() for s in shots)
    tests = {'envelope-tests.log': 9, 'runtime-regressions.log': 11,
             'domain-regressions.log': 15, 'rocket-regressions.log': 12,
             'virality-regressions.log': 30, 'pokebook-regressions.log': 16,
             'legacy-budget-regressions.log': 4}
    for name, count in tests.items():
        log = (D / name).read_text()
        assert f'Ran {count} tests' in log and log.rstrip().endswith('OK'), name
    result = dict(status='ROCKET-01 ACCEPTED', decision='D50',
        historicalRocketLiveHermesAccepted=False, historicalPublicProducer='deterministic_fallback',
        historicalRecapReplaced=False, battleReplayed=False, qualificationValid=True,
        qualificationCommitted=False, qualifier=qualified['record']['model'],
        qualificationCampaignUnchanged=qualification_unchanged, offlineRestartUnchanged=restart_unchanged,
        preservedFiles=preserved, allProductionDomainRowsUnchanged=True,
        offlineRestartMetadataChanges=changed, freshRestoreEpochIncrement=2,
        logicalDatabaseSHA256=logical_database_hash(ROOT / '.local/rocket01/world.sqlite3'),
        directReceipts=47, privateReceipts=47, publicClaims=2,
        rollbackProof='hermes-disposition/verification.json',
        nativeScreenshots=[f'evidence/private/rocket01/{s}.png' for s in shots],
        nativeViewerVisualReview='actual grunt fallback and followers; final panel exits to Start menu',
        expiredHostViewerNotAccepted='disposition-viewer-proof.json only proves hash immutability',
        checkpoint=restart['checkpoint'], projectionHashes=restart['hashes'],
        requests=dict(previous=16, newHermes=4, total=20, historicalCeiling=50,
                      closed=True, incrementalCost=0, first16Unchanged=True,
                      rejectedFifthFinishRequest='before hosted POST/ledger charge'),
        tests=tests, hostTestCount=sum(tests.values()), workersStopped=True,
        runtimeHomeCleaned=True, hostedInferenceEnabled=False,
        permanentEWRAMGrowth=0, permanentEWRAMHeadroom=4,
        nextRecommendation='RIVAL-01; planning only, separate authorization required', endgameDeferred=True)
    (D / 'disposition.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'calls': 20, 'tests': sum(tests.values()),
                      'workersStopped': True, 'projectionsUnchanged': True}))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""One bounded, discard-only actual Hermes qualification; never gameplay."""
import argparse, hashlib, json, sys, uuid, sqlite3
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.budget import CampaignBudget
from puppeteer.qualification import open_qualification
from puppeteer.runtime import run_job,cleanup
from hermes_qualification_fixture import create_fixture
from rocket01_preflight import hermes_route

E=ROOT/'evidence/phase7/rocket01';D=E/'hermes-disposition';LEDGER=E/'requests.json'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def logical_database_hash(path):
    with closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)) as db:
        schema=list(db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name'))
        tables={row[0]:list(db.execute('SELECT * FROM "'+row[0]+'" ORDER BY rowid')) for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")}
    return hashlib.sha256(json.dumps([schema,tables],sort_keys=True,default=lambda v:v.hex() if isinstance(v,bytes) else str(v)).encode()).hexdigest()
def preserve():
    expected=json.loads((D/'preserved-files.json').read_text())
    result={p:sha(ROOT/p)==h for p,h in expected.items() if p not in ('evidence/phase7/rocket01/requests.json','.local/rocket01/world.sqlite3')}
    # Existing composed writer constructors run idempotent transactions: SQLite
    # physical change counters can differ with every schema/value unchanged.
    # Compare every schema definition/table row against the byte-preserved pair.
    result['workingDatabaseAllSchemaAndRowsUnchanged']=logical_database_hash(ROOT/'.local/rocket01/world.sqlite3')==logical_database_hash(ROOT/'.local/rocket01/post-rocket-pair.sqlite3')
    if not all(result.values()):raise ValueError('retained campaign/evidence file changed; qualification refused')
    return result
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    if not args.live:raise ValueError('explicit bounded --live required')
    if (D/'qualification.json').exists():raise ValueError('one disposition qualification only; refuse reroll')
    for log in ('envelope-tests.log','runtime-regressions.log','domain-regressions.log'):
        if not (D/log).read_text().rstrip().endswith('OK'):raise ValueError('local qualification gates must pass first')
    before=preserve();before_physical=sha(ROOT/'.local/rocket01/world.sqlite3')
    try:route=hermes_route()
    except Exception as error:
        (D/'preflight.json').write_text(json.dumps({'qualified':False,'generationCalls':0,'error':type(error).__name__+': '+str(error)},indent=2)+'\n');raise
    (D/'preflight.json').write_text(json.dumps({'qualified':True,'generationCalls':0,'route':route},indent=2)+'\n')
    private=ROOT/'.local/hermes-qualification'/str(uuid.uuid4());fixture=create_fixture(private/'fixture.sqlite3')
    (D/'synthetic-fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
    def charge(job,model,request_hash):
        if job!=fixture['jobID'] or model!=route['model']:raise ValueError('qualification job/model scope')
        with CampaignBudget(LEDGER) as budget:
            n=budget.charge('puppeteer','qualification:'+fixture['namespace']+':'+job,model,request_hash)
            state=budget.read();state['attempts'][n-1].update(verifiedFree=True,qualificationNamespace=fixture['namespace'],domainJobID=job);budget.write(state);return n
    with CampaignBudget(LEDGER) as budget:budget.authorize_rocket_qualification()
    try:
        record=run_job(fixture['database'],fixture['jobID'],transport='live',live=True,experiment='closeout',store_factory=open_qualification,charge_request=charge,audit_directory=D/'jobs')
        with open_qualification(fixture['database']) as w:
            after_hashes={k:getattr(w,k)() for k in fixture['hashes']}
            assert after_hashes==fixture['hashes'] and not w.social_state()['posts'] and not w.puppeteer_state()['episodes']
        after=preserve();valid=record.get('outcome',{}).get('qualificationValid') is True
        with CampaignBudget(LEDGER) as budget:
            for request in record['requests']:
                n=request.get('liveAttempt')
                if not n:continue
                response=request.get('response',{})
                budget.finish(n,{'status':'qualification_response_archived' if response else 'qualification_provider_failure','qualifiedJob':valid,'committed':False,'namespace':fixture['namespace'],'model':response.get('model'),'provider':response.get('provider'),'usage':response.get('usage'),'evidence':'hermes-disposition/qualification.json'})
        result={'valid':valid,'committed':False,'stage':'production-shaped synthetic fixture','beforeCampaignFiles':before,'afterCampaignFiles':after,'workingDatabaseBytesUnchangedDuringQualification':before_physical==sha(ROOT/'.local/rocket01/world.sqlite3'),'fixtureProjectionHashesUnchanged':True,'fixture':fixture,'record':record,'historicalRocketPublicProducer':'deterministic_fallback','historicalPostReplaced':False,'shadowStageSkipped':'synthetic fixture exercises production prompt/parser/adapter/strict validator and actual Hermes process; no second stage needed' if valid else None}
        if record.get('runtimeHome'):result['cleanup']=cleanup(Path(record['runtimeHome']),False)
        (D/'qualification.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'qualified':valid,'newCalls':len([r for r in record['requests'] if r.get('liveAttempt')]),'campaignFilesUnchanged':all(after.values()),'historicalRecapReplaced':False}))
        if not valid:raise ValueError('live Hermes qualification failed; historical world preserved')
    finally:
        with CampaignBudget(LEDGER) as budget:budget.close()
if __name__=='__main__':main()

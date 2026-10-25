"""Clearly synthetic typed battle fixture, never copied campaign history."""
import json, struct, sys, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_world01 import BUILD,TAG,SIZES,flash,msg
from test_memory01 import visible
from bridge.events_wire import Message
from puppeteer.store import PuppeteerStore
from puppeteer.qualification import open_qualification
from world.saves import fingerprint

def create_fixture(path):
    path=Path(path).resolve()
    if path.exists():raise ValueError('qualification fixture refuses overwrite')
    path.parent.mkdir(parents=True,exist_ok=True)
    namespace='hermes-qualification:'+str(uuid.uuid4())
    with PuppeteerStore(path,BUILD,TAG) as w:
        identity=fingerprint(flash(),SIZES);w.import_save(identity);w.authorize_launch(100,identity);w.activate_puppeteer()
        own=msg(4,3);own=Message(own.kind,own.nonce,own.generation,own.sequence,own.tag,own.typ,own.payload[:24]+struct.pack('<BBHH',1,1,81,13))
        for event in (msg(1),msg(2,2),visible(3),own,msg(5,4),msg(6,5)):w.ingest(event)
        w.db.execute('CREATE TABLE hermes_qualification_owner(namespace TEXT,database_path TEXT,campaign TEXT)')
        w.db.execute('INSERT INTO hermes_qualification_owner VALUES (?,?,?)',(namespace,str(path),w.campaign()['id']))
        job=w.begin_job(next(iter(w.puppeteer_state()['obligations'])),'enabled-test')
    with open_qualification(path) as w:
        evidence=w.job_tools(job['jobID']).get_battle_evidence()
        hashes={k:getattr(w,k)() for k in ('verify_replay','verify_memory_replay','verify_social_replay','verify_puppeteer_replay')}
    return {'namespace':namespace,'jobID':job['jobID'],'database':str(path),'hashes':hashes,'evidence':evidence,'fixtureKind':'synthetic typed protocol events, not live or historical campaign','campaign':job['scope']['campaignID']}

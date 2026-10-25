#!/usr/bin/env python3
"""Audit recorded HERMES evidence offline; does not regenerate model decisions."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jsonschema import Draft202012Validator
from puppeteer.runtime import ROOT,open_store,NAMES,PIN
E=ROOT/'evidence/phase2/hermes01';checks=[]
def check(value,name):
    if not value:raise AssertionError(name)
    checks.append(name)
def validate_snapshot(snapshot):
    for episode in snapshot['puppeteer']['episodes'].values():
        Draft202012Validator(json.loads((ROOT/'schemas/puppeteer_episode_v1.json').read_text())).validate(episode)
    for packet in snapshot['trainerPackets'].values():
        Draft202012Validator(json.loads((ROOT/'schemas/trainer_knowledge_v1.json').read_text())).validate(packet)
    check(True,'schemas: episodes and actor packets')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--database',type=Path,default=ROOT/'.local/hermes01/world.sqlite3');a=p.parse_args()
    from hermes01 import snapshot,RICK,JANICE,DOUG
    with open_store(a.database) as w:
        s=snapshot(w);validate_snapshot(s)
        check(len(s['puppeteer']['obligations'])==1,'one active native obligation')
        check(len(s['puppeteer']['episodes'])==1,'one active private episode')
        check(len(s['social']['posts'])==1,'one active mandatory recap')
        check(s['playerFollowerCount']==1,'one first-win follow')
        check(not w._one("SELECT 1 FROM puppeteer_jobs WHERE status='active'"),'no active grants')
        check(not w.pending_save(),'no pending save')
        check(len(s['trainerPackets'][JANICE]['reportedClaims'])==2,'Janice has exactly exposed claims')
        check('moveID' not in json.dumps(s['trainerPackets'][JANICE]),'Janice excludes private Tackle')
        check(not s['trainerPackets'][DOUG]['reportedClaims'] and not s['trainerPackets'][DOUG]['directObservations'],'Doug has no observations/receipts')
        check(s['trainerPackets'][RICK]['retainedEpisodes'][0]['summary']['observedPlayerMoves']==[[1,33]],'Rick remembers observed Tackle')
        check(bool(s['trainerPackets'][RICK]['retainedEpisodes'][0]['summary']['ownAnnouncedMoves']),'Rick remembers announced own actions')
        hashes={k:s[k] for k in ('canonicalSHA256','memorySHA256','socialSHA256','puppeteerSHA256')}
    audits=[json.loads(f.read_text()) for f in (E/'jobs').glob('*.json')]
    live=[r for r in audits if r.get('transport')=='live' and r.get('requests')]
    attempts=[q['liveAttempt'] for r in live for q in r['requests'] if 'liveAttempt' in q]
    check(len(attempts)==len(set(attempts))<=10,'unique live attempts within total cap')
    check(all(len(r['requests'])<=3 and len(r['tools'])<=6 for r in live),'per-job request/tool bounds')
    check(all(r['hermesRevision']==PIN for r in live),'actual Hermes pin')
    check(all({t['name'] for t in r['tools']}<=set(NAMES) for r in live),'scoped tool allowlist')
    check(all(not any(v in json.dumps(q['request']) for v in ('/Users/','/home/','OPENROUTER_KEY','PI_PRIVATE_CANARY','pokefirered.gba')) for r in live for q in r['requests']),'minimized cloud inputs')
    native=json.loads((E/'live-native.json').read_text())
    check(native['outcome']['producer']=='deterministic_fallback' and len(native['requests'])==3 and len(native['tools'])==3,'enabled native bounded failure records fallback honestly')
    check(any(r.get('outcome',{}).get('producer')=='hermes_memory_retrieval' for r in live),'fresh live durable-memory retrieval')
    check(any(r.get('outcome',{}).get('fallbackReason')=='shadow_policy' and len(r['tools'])==4 for r in live),'live shadow validates but fallback commits')
    restored=json.loads((E/'restored-S1.json').read_text())
    check(not restored['puppeteer']['episodes'] and not restored['janice']['reportedClaims'],'native paired S1 excludes future memory/receipts')
    check(bool(restored['staleGrantRejected']),'native restore revokes delayed grant')
    positive=json.loads((E/'positive-reload.json').read_text())
    check(positive['passed'] and positive['hashes']==hashes and positive['samePostIDs'] and positive['sameEpisodeIDs'],'fresh native S3 Continue preserves all four hashes and outcome IDs')
    result={'passed':True,'assertions':len(checks),'checks':checks,'activeHashes':hashes,'liveAttempts':len(attempts)}
    (E/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

#!/usr/bin/env python3
"""Offline closeout audit. No provider calls, outcome regeneration or emulator work."""
import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jsonschema import Draft202012Validator
from puppeteer.runtime import ROOT,open_store,PIN
from world.store import dump
E=ROOT/'evidence/phase2/hermes01/closeout';checks=[]
def read(name):return json.loads((E/name).read_text())
def check(value,name):
    if not value:raise AssertionError(name)
    checks.append(name)
def main():
    from hermes01 import snapshot,RICK,JANICE,DOUG,save_identity
    native=read('native-job.json');recall=read('fresh-recall.json');out=native['outcome']
    check(out['producer']=='hermes' and out['fallbackReason'] is None,'native authoritative outcome is actual Hermes, no fallback')
    check(native['experiment']=='closeout' and native['transport']=='live','explicit renewed enabled native transport')
    check(native['hermesRevision']==PIN and recall['hermesRevision']==PIN,'same actual pinned Hermes runtime')
    check(len(native['requests'])==3 and len(native['tools'])==3,'native retrieval, rejected extra field, corrected submit within caps')
    submitted=[t for t in native['tools'] if t['name']=='submit_recap_and_memory_result']
    check('maxItems' in submitted[0]['arguments']['result'] and 'output' not in submitted[0],'strict extra-field rejection preserved')
    check(submitted[-1]['output']==out,'validated tool commit owns recorded outcome')
    check(hashlib.sha256(dump(submitted[-1]['arguments']['result']).encode()).hexdigest()==out['resultSHA256'],'actual model proposal hash matches committed decision')
    bundle=native['tools'][0]['output']
    check(all(k in bundle for k in ('evidence','actorContext','priorMemory')) and bundle['actorID']==RICK,'registered retrieval bundle retains actor context and prior memory')
    check(bundle['priorMemory']['episodes']==[],'pre-Rick restored scope does not inherit future episodes')
    for audit in (native,recall):
        check(len(audit['requests'])<=4 and len(audit['tools'])<=6,'per-job bounds '+audit['jobID'])
        check(all(q['request']['max_tokens']<=1200 and len(dump(q['request']).encode())<=48000 for q in audit['requests']),'bounded requests '+audit['jobID'])
        check(all(q['response']['usage']['cost']==0 for q in audit['requests']),'reported zero cost '+audit['jobID'])
        check(all(q['response']['model']==audit['model'] for q in audit['requests']),'actual response model matches selection '+audit['jobID'])
        check(not any(v in json.dumps(audit['requests']) for v in ('PI_PRIVATE_CANARY','/Users/','OPENROUTER_KEY','pokefirered.gba')),'private input exclusion '+audit['jobID'])
    check(not Path(native['runtimeHome']).exists() and not Path(recall['runtimeHome']).exists(),'both disposable homes removed')
    check(native['runtimeHome']!=recall['runtimeHome'],'fresh distinct runtime home')
    episodes=recall['tools'][0]['output']['episodes']
    check(recall['outcome']['producer']=='hermes_memory_retrieval' and any(e['episodeID']==out['episodeID'] for e in episodes),'fresh live durable retrieval of newly model-produced episode')
    check(out['episodeID'] in json.dumps(recall['requests']) and 'observedPlayerMoves' in json.dumps(recall['requests']),'durable meaningful information reaches fresh live model')
    unread=read('unread.json');exposed=read('exposed.json')['snapshot']
    check(bool(unread['janiceFeedMetadata']) and not unread['trainerPackets'][JANICE]['reportedClaims'],'unread delivery creates no knowledge')
    check(len(exposed['trainerPackets'][JANICE]['reportedClaims'])==2 and 'moveID' not in json.dumps(exposed['trainerPackets'][JANICE]),'exposure only public claims, private Tackle omitted')
    check(not exposed['trainerPackets'][DOUG]['directObservations'] and not exposed['trainerPackets'][DOUG]['reportedClaims'] and not exposed['trainerPackets'][DOUG]['retainedEpisodes'],'Doug receives no battle knowledge')
    restored=read('restored-S1.json');check(not restored['puppeteer']['episodes'] and not restored['social']['posts'] and bool(restored['staleGrantRejected']),'native S1 rewind excludes future outcomes and rejects delayed grant')
    saved=read('saved.json');positive=read('positive-reload.json');keys=('canonicalSHA256','memorySHA256','socialSHA256','puppeteerSHA256')
    check(all(saved[k]==positive['hashes'][k] for k in keys),'native positive Continue preserves four defined hashes')
    with open_store(ROOT/'.local/hermes01/world.sqlite3') as w:
        s=snapshot(w);check(all(saved[k]==s[k] for k in keys),'final offline replay matches paired save after fresh recall')
        check(len(s['social']['posts'])==len(s['puppeteer']['episodes'])==len(s['puppeteer']['obligations'])==1,'exactly one active native obligation/post/episode')
        check(s['playerFollowerCount']==1,'first-win follow still once-only')
        check(not w.pending_save() and not w._one("SELECT 1 FROM puppeteer_jobs WHERE status='active'"),'no pending save or model grant')
        ep=s['puppeteer']['episodes'][out['episodeID']]
        check(ep['summary']['observedPlayerMoves']==[[1,33]] and ep['summary']['ownAnnouncedMoves']==[[10,33],[10,81],[13,81]],'actual run player and NPC actions retained')
        check(ep['sourceEvidenceIDs']==submitted[-1]['arguments']['result']['privateEvidenceIDs'],'private source references are model-selected committed refs')
        for e in s['puppeteer']['episodes'].values():Draft202012Validator(json.loads((ROOT/'schemas/puppeteer_episode_v1.json').read_text())).validate(e)
        for packet in s['trainerPackets'].values():Draft202012Validator(json.loads((ROOT/'schemas/trainer_knowledge_v1.json').read_text())).validate(packet)
        check(True,'existing episode/trainer schemas remain enforced')
        cp=w.get_save_checkpoint(save_identity(ROOT/'.local/hermes01/closeout-S2.sav').fingerprint)
        check(cp['id']==read('checkpoint-S2.json')['id'] and cp['kind']=='normal_save','actual native save remains paired to correct checkpoint')
    budget=json.loads((ROOT/'.local/hermes01/closeout-live-budget.json').read_text());old=json.loads((ROOT/'.local/hermes01/live-budget.json').read_text())
    attempts=[q['liveAttempt'] for a in (native,recall) for q in a['requests']]
    check(sorted(attempts)==list(range(1,6)) and budget['attempts']==5 and budget['closed'] and old['attempts']==10,'five additional attempts, separate persistent closed ledger; original ten preserved')
    check(not json.loads((ROOT/'config/model_profiles.yaml').read_text())['hosted_inference_enabled'],'normal hosted inference disabled')
    check(hashlib.sha256((ROOT/'.local/phase1-ui-enabled/pokefirered.gba').read_bytes()).hexdigest()=='739bd3eebb91aaa5210f8f8cd1f357a8272dc98db7060356c649b4c38a0dbc2d','ROM unchanged')
    report={'passed':True,'assertions':len(checks),'checks':checks,'additionalAttempts':5,'nativeJobID':native['jobID'],'postID':out['postID'],'episodeID':out['episodeID'],'hashes':positive['hashes']}
    (E/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()

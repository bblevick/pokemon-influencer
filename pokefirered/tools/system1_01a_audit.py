#!/usr/bin/env python3
"""Offline actual-artifact closeout. Restores only a disposable SQLite backup."""
import hashlib,json,re,socket,sqlite3,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from system1.native import NativePreparationStore,verify_build
from world.saves import fingerprint
from roster.extract import digest
E=ROOT/'evidence/phase3/system1_01a';P=ROOT/'.local/system1_01a'
def read(name):return json.loads((E/name).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    checks=[]
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    decision=read('selection.json');commitment=read('commitment.json');installation=read('native-installation.json')['installation']
    check('actual configured model decision',decision['source']=='model' and decision['result']['diagnostics']['requestedModel']=='inception/mercury-decide:free')
    request=decision['request'];check('sixteen bounded legal choices',len(request['choices'])==16 and decision['result']['choiceID'] in request['choices'])
    accepted_memo=json.loads((ROOT/'evidence/phase3/strategy01/memo/generate.json').read_text())
    check('exact accepted imperfect StrategyMemo retained',request['memo']==accepted_memo and accepted_memo['strategyText'] in request['state'])
    check('selected actual candidate locked',commitment['candidate']['candidateID']==decision['result']['choiceID'] and commitment['locked'])
    check('full probabilities retained',set(decision['result']['probabilities'])==set(request['choices']))
    check('selection did not mutate trainer state',read('selection-purity.json')['trainerStateUnchanged'])
    budget=read('closed-budget.json');check('closed exactly two zero cost native requests',budget['closed'] and len(budget['attempts'])==2 and all(a['response']['result']['usage']['cost']==0 for a in budget['attempts']))
    proof,manifest=verify_build(E/'manifest-native.json');check('all catalog sources and allocation verified',proof['catalogSourcesVerified']==41 and manifest['preparation_checks']['priorRAMSymbolsUnchanged'] and manifest['preparation_checks']['ewramRemaining']==52)
    check('actual native constructor installed exact selected party',installation['receipt']['nativeConstructorCount']==1 and installation['receipt']['party']==[{k:p[k] for k in ('species','level','moves','heldItem')} for lineage in commitment['candidate']['order'] for p in commitment['candidate']['party'] if p['lineage']==lineage])
    layout=json.loads((ROOT/'config/prep_save_layout.json').read_text())
    def identity(path):return fingerprint(Path(path).read_bytes(),layout['sectionSizes'])
    saves={17:ROOT/'.local/strategy01-memo/after-live-memo.sav',18:P/'locked-save18.sav',19:P/'installed-save19.sav'}
    ids={n:identity(p) for n,p in saves.items()}
    check('three checksum-valid real batteries',all(i.counter==n for n,i in ids.items()))
    check('current battery is exact final pair',identity(P/'pokefirered.sav')==ids[19])
    with NativePreparationStore(P/'world.sqlite3',E/'manifest-native.json') as w:
        state=w.decision_state();check('fresh runtime exact stored model and lock',list(state['decisions'].values())==[decision] and list(state['commitments'].values())==[commitment] and list(state['installations'].values())==[installation])
        check('no pending save or active selection job',not w.pending_save() and not w._one("SELECT 1 FROM preparation_decision_jobs WHERE status='active'"))
        cp=w.get_save_checkpoint(ids[19].fingerprint);check('normal Save19 selected at saved cursor',cp['kind']=='normal_save' and cp['cursor']==w.campaign()['cursor']==162)
        ended=json.loads(w._one('SELECT record FROM events WHERE branch=? AND cursor=?',(cp['branch'],cp['cursor']))['record'])
        check('installed ordinary Rick battle actually completed',ended['eventType']=='BATTLE_ENDED' and ended['payload']=={'outcome':1,'previouslyUndefeated':False,'trainerID':102} and ended['session']==installation['receipt']['nonce'] and not ended['streamIncomplete'])
        replay={'campaign':w.campaign(),'pairedSave':ids[19].as_dict(),'checkpointID':cp['id'],'decisionSHA256':digest(decision),'commitmentSHA256':digest(commitment),'installationSHA256':digest(installation),'stateSHA256':w.verify_decision_replay(),'modelRequests':0}
    (E/'fresh-runtime-replay.json').write_text(json.dumps(replay,indent=2)+'\n')
    audit=P/'restore-audit.sqlite3'
    source=sqlite3.connect(P/'world.sqlite3');target=sqlite3.connect(audit);source.backup(target);source.close();target.close()
    restored={}
    with NativePreparationStore(audit,E/'manifest-native.json') as w:
        for n in (17,18,19):
            cp=w.restore(ids[n]);s=w.decision_state()
            if n==17:
                check('Save17 excludes future decision commitment installation',not any(s[k] for k in ('decisions','commitments','installations')))
                check('Save17 opportunity and stock restored',w.preparation_state()['opportunities'][commitment['opportunityID']]['status']!='committed' and w.preparation_state()['actors'][commitment['actor']]['resources']['stock']==[])
                for label,call in [('stale result',lambda:w.finish_selection(request,decision['result'],'model')),('future commit',lambda:w.commit_preparation(decision['decisionID']))]:
                    rejected=False
                    try:call()
                    except ValueError:rejected=True
                    check('Save17 rejects '+label,rejected)
            else:
                check('Save'+str(n)+' retrieves exact choice and lock',list(s['decisions'].values())==[decision] and list(s['commitments'].values())==[commitment])
                check('Save'+str(n)+' installation cutoff',list(s['installations'].values())==([] if n==18 else [installation]))
            restored[str(n)]={'checkpointID':cp['id'],'cursor':cp['cursor'],'decisionCount':len(s['decisions']),'commitmentCount':len(s['commitments']),'installationCount':len(s['installations']),'stateSHA256':w.verify_decision_replay(),'modelRequests':0}
    (E/'paired-restore-audit.json').write_text(json.dumps(restored,indent=2)+'\n')
    # Read the native trainer flag from source-indexed, checksum-valid SaveBlock1.
    flag_source=(ROOT/'include/constants/flags.h').read_text()
    check('source trainer flag indexing expression',bool(re.search(r'#define\s+TRAINER_FLAGS_START\s+\(FLAG_0x4FF \+ 1\)',flag_source)))
    start=int(re.search(r'#define\s+FLAG_0x4FF\s+(0x[0-9A-Fa-f]+)',flag_source).group(1),0)+1
    flags={}
    for n,path in saves.items():
        data=path.read_bytes();sections={}
        for index in range(ids[n].slot*14,(ids[n].slot+1)*14):
            sector=data[index*4096:(index+1)*4096];sid=struct.unpack_from('<H',sector,4084)[0];sections[sid]=sector[:layout['sectionSizes'][sid]]
        block=b''.join(sections[i] for i in (1,2,3,4));flag=start+102;flags[str(n)]=bool(block[layout['flagsOffset']+flag//8]&(1<<(flag&7)))
    check('Rick defeated flag retained across ordinary saves',all(flags.values()))
    protected=read('protected-before.json');bad=[p for p,h in protected.items() if sha(ROOT/p)!=h];check('historical protected inputs unchanged',not bad)
    check('local user dump unchanged',sha(ROOT/'pokefirered.gba')=='3d0c79f1627022e18765766f6cb5ea067f6b5bf7dca115552189ad65a5c3a8ac')
    log=(E/'emulator.jsonl').read_text();check('actual Save19 field reload',bool(re.search(r'counter=19 partycount=1 level=14 hp=15 x=6 y=7 mapgroup=6 mapnum=2',log)))
    names=set()
    for file in ('host-tests-final.txt','native-host-tests-final.txt','foundation-regressions.txt','provider-regressions-final.txt'):
        text=(E/file).read_text();check(file+' successful zero skips',text.rstrip().endswith('OK') and 'skipped' not in text.lower());names.update(re.findall(r'^(test_\S+) \(([^)]+)\)',text,re.M))
    check('57 unique focused cases',len(names)==57)
    for port in (18782,18783):
        sock=socket.socket();sock.settimeout(.2);closed=sock.connect_ex(('127.0.0.1',port))!=0;sock.close();check('task listener '+str(port)+' closed',closed)
    processes=subprocess.check_output(['ps','-Ao','pid,command'],text=True);remaining=[line for line in processes.splitlines() if ('MacOS/mGBA' in line and '/.local/system1-01a-native-' in line) or ('MacOS/Python tools/system1_01a_host.py' in line)]
    check('task workers stopped',not remaining)
    config=json.loads((ROOT/'config/model_profiles.yaml').read_text());check('hosted inference remains offline by default',not config['hosted_inference_enabled'] and config['default_profile']=='offline')
    report={'status':'passed','checks':checks,'count':len(checks),'uniqueFocusedTests':len(names),'protectedInputs':len(protected),'rickDefeatedNativeFlag':flags,'freshRuntime':replay,'remainingProcesses':remaining,'modelRequestsDuringAudit':0,'scope':'Controlled opening Rick installation; no live tactics, acquisitions or full rematch UX'}
    (E/'artifact-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','checks':len(checks),'uniqueFocusedTests':len(names),'protectedInputs':len(protected)},indent=2))
if __name__=='__main__':main()

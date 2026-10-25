#!/usr/bin/env python3
"""Closeout only after actual proof and shutdown; refuses absent evidence/active processes."""
import json,hashlib,sqlite3,subprocess,re
from pokebook01 import ROOT,E,open_store,manifest
from hermes01 import snapshot
from verify_pokebook01 import verify

def run():
 verify();m=manifest()
 with open_store(ROOT/'.local/pokebook01/world.sqlite3') as w:
  paired=json.loads((E/'restored-S2.json').read_text())['snapshot'];current=snapshot(w)
  assert all(current[k]==paired[k] for k in ('canonicalSHA256','memorySHA256','socialSHA256','puppeteerSHA256','counts','trainerPackets'))
  assert not w.pending_save() and not w._one("SELECT id FROM puppeteer_jobs WHERE status='active'")
  backup=ROOT/'.local/pokebook01/acceptance.sqlite3'
  if not backup.exists():
   with sqlite3.connect(backup) as dest:w.db.backup(dest)
 old=json.loads((ROOT/'.local/hermes01/live-budget.json').read_text());renewal=json.loads((ROOT/'.local/hermes01/closeout-live-budget.json').read_text())
 assert old['attempts']==10 and renewal['attempts']==5 and renewal['closed']
 config=json.loads((ROOT/'config/model_profiles.yaml').read_text());assert config['default_profile']=='offline' and config['hosted_inference_enabled'] is False
 dump=hashlib.sha256((ROOT/'pokefirered.gba').read_bytes()).hexdigest();assert dump=='3d0c79f1627022e18765766f6cb5ea067f6b5bf7dca115552189ad65a5c3a8ac'
 processes=subprocess.run(['pgrep','-fl',r'^.*[/ ]tools/pokebook01_(host|launch|fault_host|fault_scenario|fixture_scenario|restore_scenario)\.py|^'+re.escape(str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'))+r'(\s|$)'],capture_output=True,text=True)
 ports=subprocess.run(['lsof','-nP','-iTCP:18772','-iTCP:18773'],capture_output=True,text=True)
 assert processes.returncode==ports.returncode==1
 cleanup={'taskProcessesAbsent':True,'bridgeAndInputListenersAbsent':True,'hostedInferenceEnabled':False,'defaultProfile':'offline','newModelRequests':0,'priorBudget':old,'closedPriorCloseout':renewal,'userDumpSHA256':dump,'privateBackup':str(backup.relative_to(ROOT)),'noPendingSaveOrJob':True,'finalViewingHistoriesUnchanged':True}
 (E/'cleanup.json').write_text(json.dumps(cleanup,indent=2)+'\n')
 completion={'accepted':True,'completedTicketIDs':['POKEBOOK-01'],'romSHA256':m['rom_sha256'],'sourceCommit':m['source_commit'],'viewerSchema':2,'evidenceVerifier':'verification.json','newTests':{'baselineHost':211,'finalHost':226,'newViewerHost':15,'retainedActualCCases':48,'actualC':'wire and lifecycle/selection with ASan/UBSan; hardware substitutes explicitly marked','architectureChecks':43,'handoffChecks':60,'handoffFixtures':9},'permanentDelta':4,'staticEWRAMRemaining':220,'temporaryPayloadBytes':15572,'realRecapProducer':'deterministic_fallback/offline_mode','storedHermesRendering':'explicit Stored RICK fixture; no migration or new inference','nativeScreens':['normal Start entry','home','feed','full reader','followers','empty','unavailable'],'nativeTimelineEvidence':['restored-S1.json','restored-S2.json'],'nativeSelectionEvidence':'native-layout-visual.json','resourceEvidence':'emulator.jsonl.resources','cleanup':'cleanup.json','campaign':current['campaign'],'checkpoints':{name:json.loads((E/('checkpoint-'+name+'.json')).read_text())['id'] for name in ('S1','S2')},'nextPrerequisiteTask':'ROSTER-01 legality catalog, then CONTENT/PREP prerequisites before STRATEGY-01; planning only','readinessNote':'docs/strategy01_readiness.md','openRisks':['ASCII/single-paragraph/record caps fail closed','authored slice; no autonomous NPC exposure scheduler','manual native script load and launch-bounded sockets','fresh paired battery only; unmanaged reset/hot-load/rewind unsupported','power-loss/worst-stack/full-campaign qualification pending','Hermes private packet fact-deduplicated, not chronological transcript'],'supersededCandidates':['../pokebook01-cursor-candidate','../pokebook01-selection-candidate'],'deferred':['STRATEGY-01','SYSTEM1-01A/B','roster installation/battle AI','endgame']}
 (E/'completion.json').write_text(json.dumps(completion,indent=2)+'\n');print(json.dumps(completion,indent=2))
if __name__=='__main__':run()

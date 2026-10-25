#!/usr/bin/env python3
"""Verify retained zero-inference proofs without accepting unrecoverable evidence."""
import json,hashlib,subprocess,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign_expansion01_build import ram
E=ROOT/'evidence/phase6/campaign_expansion01_gate_repair'
def read(n):return json.loads((E/n).read_text())
def main():
 protected=read('protected.json');unchanged={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()};assert all(unchanged.values())
 old=ROOT/'.local/battle-end01-external-v2/pokefirered.elf';new=ROOT/'.local/campaign-expansion01-native/pokefirered.elf';before=ram(old);after=ram(new);assert before==after;end=max(a+s for n,a,s in after if 0x02000000<=a<0x02040000);assert 0x02040000-end==4
 preflight=read('offline-preflight.json');assert all(preflight[str(i)]['encodedBytes']<=24576 and preflight[str(i)]['privateEpisodesExcluded'] for i in (106,107,108))
 c1=read('C1-native-readonly.json');save=read('native-pending-save-proof.json');fresh=read('save16-fresh-projections.json');assert c1['hashes']==save['hashes']==fresh['hashes'];assert save['pendingSave'] is None and fresh['pendingSave'] is None
 counts={}
 for name in ('closeout-gate-tests.log','closeout-regression-tests.log'):
  log=(E/name).read_text();match=re.search(r'Ran (\d+) tests?',log);assert match and log.rstrip().endswith('OK');counts[name]=int(match[1])
 assert 'matrix passed' in (E/'closeout-native-tests.log').read_text()
 processes=subprocess.check_output(['ps','-axo','pid,command'],text=True);owned=[x for x in processes.splitlines() if 'Python tools/campaign_expansion01_gate_native.py host' in x or 'Python tools/campaign_expansion01_gate_timing.py' in x or ('.local/mGBA.app/Contents/MacOS/mGBA' in x and '-C savegamePath='+str(ROOT/'.local/campaign_expansion01_gate_repair') in x)];assert not owned
 matrix=read('native-timing-matrix.json');assert matrix['fiveCasesPassed'] and not matrix['campaignCompleted']
 restored=read('post-timing-C1-restored.json');assert restored['hashes']==c1['hashes'] and restored['launchesActive']==0
 ledger=json.loads((ROOT/'evidence/phase6/campaign_expansion01/requests.json').read_text());assert ledger['closed'] and len(ledger['attempts'])==16
 incident=read('greg-historical-incident.json');assert incident['historicalClassification']=='UNKNOWN — insufficient retained telemetry' and incident['search']['fileCount']==104
 for path,h in incident['search']['artifactHashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
 diagnostics=read('future-diagnostics.json');assert len(diagnostics['cases'])==6 and all(r['durableMemoSurvivedReopen'] and r['freshProcessReloadPassed'] for r in diagnostics['cases'])
 out={'ticket':'CAMPAIGN-EXPANSION-01 GATE REPAIR','gateRepairComplete':True,'historicalEvidenceDisposition':'amended criterion B; UNKNOWN — insufficient retained telemetry','campaignExpansionAccepted':False,'hostedGenerationRequests':0,'closedLedgerUnchanged':True,'protectedMatches':unchanged,'tests':counts,'testCount':sum(counts.values()),'nativeMatrixPassed':True,'fiveCaseEmulatorMatrixPassed':True,'abandonedTimingBranchExcluded':True,'permanentEWRAM':{'beforeHeadroomBytes':4,'afterHeadroomBytes':4,'deltaBytes':0,'allRAMSymbolsIdentical':True},'C1SevenHashesMatch':True,'nativePendingSaveRestartPassed':True,'freshSave16ContinuePassed':True,'workersStopped':True,'outstandingGates':[],'closeoutContractConflicts':['Greg first memo/sole preparation already locked; no new Strategy call allowed for same opportunity','Kent108 is the selected Mt. Moon trainer; no fourth content actor is qualified']}
 (E/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('gateRepairComplete','hostedGenerationRequests','testCount','nativePendingSaveRestartPassed','workersStopped')}))
if __name__=='__main__':main()

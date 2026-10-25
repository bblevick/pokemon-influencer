#!/usr/bin/env python3
"""Read-only historical analysis. No credentials, generation or ledger writes."""
import json,statistics,hashlib,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
E=ROOT/'evidence/phase6/campaign_expansion01_gate_repair'
from roster.hashes import digest
def rows(path):return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
def distribution(v):
 v=sorted(v)
 if not v:return {'count':0}
 def percentile(p):
  k=(len(v)-1)*p;i=int(k);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(k-i)
 return {'count':len(v),'minimum':min(v),'median':statistics.median(v),'p90':percentile(.9) if len(v)>=10 else None,'p95':percentile(.95) if len(v)>=20 else None,'maximum':max(v),'quantileMethod':'linear interpolation; p90 requires10 and p95 requires20 samples'}
def main():
 E.mkdir(parents=True,exist_ok=True);out={'mode':'historical read-only; no model calls','groups':{}}
 for name,folder in [('Rick','evidence/phase4/system1_01b'),('Brock-slice','evidence/phase4/vertical_slice01'),('Sally','evidence/phase6/campaign_expansion01')]:
  p=ROOT/folder;ledger=json.loads((p/'requests.json').read_text());audit=rows(p/'battle-audit.jsonl');correlated=[]
  for a in ledger['attempts']:
   if a.get('role')!='battle' and not (name=='Rick' and a.get('jobID','').startswith('battle:')):continue
   scope=a.get('scope',{});job=a.get('jobID')
   def matching(r):
    packet=r.get('request',{})
    if packet.get('requestID')==job or (scope and all(packet.get('nativeState',{}).get(k)==scope.get(k) for k in ('nonce','generation','battle','request'))):return True
    if not all(k in packet for k in ('state','question','choices')):return False
    body={'model':a['requestedModel'],'state':packet['state'],'questions':{'preparation':{'type':'choice','instructions':packet['question'],'criteria':packet['choices']}}}
    return digest(body)==a.get('requestSHA256')
   matched=[r for r in audit if matching(r)]
   selection=next((r for r in matched if r.get('event')=='selection'),{});scope=scope or selection.get('request',{}).get('scope',{});response=a.get('response',{});native=[r for r in audit if scope and (r.get('session'),r.get('generation'),r.get('nativeRequest'))==(scope.get('nonce'),scope.get('generation'),scope.get('request')) and r.get('event')=='native-terminal']
   correlated.append({'attempt':a.get('attempt',ledger['attempts'].index(a)+1),'jobID':job,'scope':scope,'dispatchAtUnix':a.get('startedAtUnix'),'remoteRoundTripSeconds':response.get('latencySeconds'),'httpStatus':response.get('httpStatus'),'selectedExternal':selection.get('nativeSelected') is not None,'hostPacketReceivedMonotonic':selection.get('receivedMonotonic'),'hostRoundTripSeconds':selection.get('hostLatencySeconds'),'nativeTerminals':[{k:r.get(k) for k in ('session','battle','turn','source','fallbackReason','nativeSelected')} for r in native],'recordedOutcome':a.get('outcome'),'retrospectiveErrorEvidence':a.get('retrospectiveErrorEvidence')})
  remote=[r['remoteRoundTripSeconds'] for r in correlated if r['httpStatus']==200 and r['remoteRoundTripSeconds'] is not None];host=[r['hostRoundTripSeconds'] for r in correlated if r['hostRoundTripSeconds'] is not None and r['selectedExternal']]
  overhead=[r['hostRoundTripSeconds']-r['remoteRoundTripSeconds'] for r in correlated if r['selectedExternal'] and r['hostRoundTripSeconds'] is not None and r['remoteRoundTripSeconds'] is not None]
  out['groups'][name]={'ledgerSHA256':hashlib.sha256((p/'requests.json').read_bytes()).hexdigest(),'requests':correlated,'remoteDistribution':distribution(remote),'hostDistribution':distribution(host),'hostMinusHTTPDistribution':distribution(overhead),'missingResponseCount':sum(not a.get('response') for a in ledger['attempts'] if a.get('role')=='battle' or (name=='Rick' and a.get('jobID','').startswith('battle:'))),'recordedLateDiscardCount':sum(r.get('event')=='late-result-discarded' for r in audit),'missingTimestamps':['provider acceptance','remote first-byte arrival','wall-clock native action execution'],'warning':'HTTP roundtrip includes network, request setup, ledger I/O and response parsing; not pure inference. Historical scopes may be absent; unmatched records are not fabricated.'}
 out['SallyClassification']={'request14':'fresh worker system1_request_deadline at2.35s; no response receipt. Remote/network/worker roundtrip did not finish; provider acceptance not recorded. Cannot isolate remote inference from network delay.','turn14and15':'no additional POST; encounter failure latch suppressed retries after turn13 timeout','policy':{'providerSeconds':2.35,'workerSeconds':2.55,'hostSeconds':2.75,'nativeFrames':180,'nativeAt60fpsSeconds':3,'change':'none; preserve bounded fallback. Maximum nominal native wait3s; fast-forward shortens wall time.'}}
 from campaign_expansion01_build import ram
 before=ram(ROOT/'.local/battle-end01-external-v2/pokefirered.elf');after=ram(ROOT/'.local/campaign-expansion01-native/pokefirered.elf');end=max(a+s for n,a,s in after if 0x02000000<=a<0x02040000)
 out['memory']={'allRAMSymbolsIdentical':before==after,'permanentEWRAMEnd':hex(end),'headroomBytes':0x02040000-end,'deltaBytes':0,'nativeSourceChangedByRepair':False}
 protected=json.loads((E/'protected.json').read_text());out['protectedMatches']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()};assert all(out['protectedMatches'].values())
 (E/'historical-analysis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({n:{'remote':g['remoteDistribution'],'host':g['hostDistribution'],'missingResponse':g['missingResponseCount']} for n,g in out['groups'].items()},indent=2));print(out['memory'])
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Retained-evidence disposition only. No network, credentials or inference."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
E=ROOT/'evidence/phase6/campaign_expansion01_gate_repair'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 search=json.loads((E/'historical-error-search.json').read_text());paths=search['examinedFiles'];assert len(paths)==104
 manifest={p:sha(ROOT/p) for p in paths};assert all(c=='ProviderError' for f in search['findings'] for c in f['codes'])
 source=ROOT/'evidence/phase6/campaign_expansion01/causal-trace.jsonl'
 records=[json.loads(s) for s in source.read_text().splitlines()]
 context=next(r for r in records if r.get('event')=='trainer-context' and r.get('actor')=='trainer:fr:trainer:0106')
 memo=next(r['memo'] for r in records if r.get('event')=='strategy-committed' and r.get('memo',{}).get('jobID')==context['jobID'])
 assert memo['source']=='fallback' and memo['diagnostics']['failure']=='ProviderError'
 assert not any(a['jobID']==context['jobID'] for a in json.loads((ROOT/'evidence/phase6/campaign_expansion01/requests.json').read_text())['attempts'])
 diagnostics=json.loads((E/'future-diagnostics.json').read_text());assert {r['category'] for r in diagnostics['cases']}=={'http_rejection','rate_limit','timeout','transport','malformed_response','preflight_rejection'}
 assert all(r['durableMemoSurvivedReopen'] and r['evidenceCollectionSurvived'] and r['freshProcessReloadPassed'] for r in diagnostics['cases'])
 pre=json.loads((E/'offline-preflight.json').read_text());assert all(pre[str(i)]['privateEpisodesExcluded'] and pre[str(i)]['encodedBytes']<=24576 for i in (106,107,108))
 incident={'schemaVersion':1,'incident':'Greg-original-Strategy-preflight','actor':'trainer:fr:trainer:0106','jobID':context['jobID'],'contextID':context['context']['contextID'],'fallbackStrategyID':memo['strategyID'],'historicalStatus':'failed; immutable factual fallback committed','recordedErrorClass':'ProviderError','historicalClassification':'UNKNOWN — insufficient retained telemetry','exactRemoteCause':None,'recoverability':'irrecoverable_from_retained_artifacts','reason':'Old parent failure persisted the generic class without exact symbolic code or failed metadata. The retained search contains no correlated primary copy. Irrecoverability is bounded to the enumerated retained artifacts, not a claim about external provider logs.','known':['Production context constructed','Failure recorded before worker dispatch; no charged Greg POST in closed ledger','Fallback memo and preparation retained; no live model memo from the failed attempt'],'unknown':['HTTP status','error body','provider request ID','failed serving metadata','exact failure subtype'],'search':{'roots':sorted(set(str(Path(p).parent) for p in paths)),'fileCount':len(paths),'types':['JSON projections, contexts, reports and ledgers','JSONL host, worker, causal, native audit, delivery, pairing and save logs','text/log transcripts and worker logs'],'searchedSymbols':['ProviderError','symbolic adapter/preflight failure codes','Greg logical job/context identities'],'artifactHashes':manifest,'searchEvidence':'historical-error-search.json'},'primaryEvidence':{'path':str(source.relative_to(ROOT)),'sha256':sha(source)},'currentPathStatus':'passes_local_production_preflight; saved Greg context reused because first opportunity is consumed','instrumentationStatus':'six representative mocked categories distinguished and persisted through real memo commit/reopen; worker boundary preserves scope','acceptanceDisposition':'historical evidence gap closed under amended OR criterion B, without fabricated root cause','hostedGenerationRequests':0,'packActors':[106,107,108],'selectedMtMoonActor':108}
 (E/'greg-historical-incident.json').write_text(json.dumps(incident,indent=2)+'\n');print(json.dumps({'classification':incident['historicalClassification'],'artifacts':len(paths),'generation':0,'disposition':incident['acceptanceDisposition']}))
if __name__=='__main__':main()

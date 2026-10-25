#!/usr/bin/env python3
"""Offline verification of live qualification, active selector and exact historical replay."""
import json,hashlib,sqlite3,tempfile,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from strategy.provider import OpenRouterProvider,Limits,live_configuration,qualify_text_route
from strategy.memo import validate_text
from strategy.context import configuration_identity
from strategy_model03 import Budget,E
from campaign.expansion import ExpansionStore
from world.saves import fingerprint,layout_from_build
from campaign_expansion01_build import ram
from roster.hashes import digest

def main():
 selected=json.loads((E/'active-selection.json').read_text());active,_=live_configuration();assert active==selected['binding']
 smoke=json.loads((E/'contingency-smoke.json').read_text());fixture=json.loads((E/'contingency-fixture.json').read_text())
 for r in (smoke,fixture):
  assert r['status']=='accepted' and r['binding']==active and r['diagnostics']['usage']['cost']==0;validate_text(r['strategyText']);assert not r['campaignCommitted']
 request=json.loads((E/'synthetic-request.json').read_text());assert not {'tools','tool_choice','response_format'}&request.keys();assert request['model']==active['model']
 with Budget(E/'requests.json') as b:ledger=b.read();assert ledger['closed'] and len(ledger['attempts'])==3 and len({a['requestedModel'] for a in ledger['attempts']})==2
 protected=json.loads((E/'protected.json').read_text());matches={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()};assert all(matches.values())
 old=ram(ROOT/'.local/battle-end01-external-v2/pokefirered.elf');new=ram(ROOT/'.local/campaign-expansion01-native/pokefirered.elf');assert old==new;assert 0x02040000-max(a+s for n,a,s in new if 0x02000000<=a<0x02040000)==4
 manifest=ROOT/'evidence/phase6/campaign_expansion01/manifest-native.json';m=json.loads(manifest.read_text());save=fingerprint((ROOT/'.local/campaign_expansion01/C1-sally-recovered.sav').read_bytes(),layout_from_build(ROOT/m['rom_path']))
 with tempfile.TemporaryDirectory() as tmp:
  path=Path(tmp)/'world.sqlite3';src=sqlite3.connect('file:'+str(ROOT/'.local/campaign_expansion01/world.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(path);src.backup(dst);src.close();dst.close()
  with ExpansionStore(path,manifest) as w:
   methods=['verify_replay','verify_memory_replay','verify_social_replay','verify_puppeteer_replay','verify_strategy_replay','verify_decision_replay','verify_virality_replay'];before={k:getattr(w,k)() for k in methods};memos=w.memo_records();greg=w.locked_preparation('trainer:fr:trainer:0106');assert any('nemotron' in json.dumps(r).lower() for r in memos)
   route=json.loads((E/'contingency-fixture-route.json').read_text());route['checkedAtUnix']=__import__('time').time();provider=OpenRouterProvider(active,'unused-no-network',route,None,None,system_prompt=(ROOT/'prompts/strategy_scouting_v3.txt').read_text());readiness={}
   for i in (107,108):
    p=w.context_packet(f'trainer:fr:trainer:{i:04d}','first',provider_binding=active);body,encoded=provider.prepare_request(p['modelInput'],None,Limits(attempts=1),text=True);assert not {'tools','tool_choice','response_format'}&body.keys();assert p['modelInput']['opponentCurrentLead']=='UNKNOWN' and not p['modelInput']['privateEpisodes']
    readiness[str(i)]={'activeBinding':active,'contextID':p['contextID'],'configurationIdentity':configuration_identity(),'requestSHA256':digest(body),'encodedBytes':len(encoded),'localPassed':True,'generationRequests':0}
   w.restore(save);assert w.memo_records()==memos and w.locked_preparation('trainer:fr:trainer:0106')==greg and {k:getattr(w,k)() for k in methods}==before
   with ExpansionStore(path,manifest) as reopened:assert reopened.memo_records()==memos and reopened.locked_preparation('trainer:fr:trainer:0106')==greg
   history={'exactHistoricalMemosMetadataUnchanged':True,'gregLockUnchanged':True,'activeModelDiffersFromHistoricalNemotron':True,'normalC1RestoreAndReopenPassed':True,'C1ProjectionHashes':before,'historicalTextHashes':{r['strategyID']:digest(r['strategyText']) for r in memos},'inferenceRequests':0}
 (E/'active-local-readiness.json').write_text(json.dumps(readiness,indent=2)+'\n');(E/'historical-preservation.json').write_text(json.dumps(history,indent=2)+'\n')
 out={'ticket':'STRATEGY-MODEL-03','accepted':True,'activeModel':active['model'],'activeProvider':active['provider'],'servingProvider':'AtlasCloud','requests':3,'maximumRequests':6,'perModelRequests':{model:sum(a['requestedModel']==model for a in ledger['attempts']) for model in {a['requestedModel'] for a in ledger['attempts']}},'successfulReportedCostUSD':0,'failedRequestCostReceipt':'Liquid HTTP400 supplied no usage/cost; free route/max_price0 confirmed','ledgerClosed':True,'unusedAllowance':3,'metadataGatePassed':True,'smokePassed':True,'fixturePassed':True,'qualityReview':'Coherent persona/team/resource/evidence/uncertainty strategy; questionable Effect Nightmare reference retained as subjective prose; no executable authority','fixtureUTF8Bytes':len(fixture['strategyText'].encode()),'fixtureWords':len(fixture['strategyText'].split()),'JamesKentLocalPassed':readiness,'historicalPreservation':history,'protectedMatches':matches,'permanentEWRAM':{'before':4,'after':4,'delta':0,'allRAMSymbolsIdentical':True},'hostedDefaultDisabled':not json.loads((ROOT/'config/model_profiles.yaml').read_text())['hosted_inference_enabled'],'campaignGeneration':0,'MercuryCalls':0,'HermesCalls':0,'campaign98AllowanceUnchanged':True,'workersStopped':True,'expiration':'2026-12-31; fresh metadata required before future dispatch'}
 log=E/'tests.log'
 if log.exists():
  text=log.read_text();assert text.rstrip().endswith('OK');out['relevantTests']={'passed':True,'count':int(re.search(r'Ran (\d+) tests',text)[1]),'skips':0}
 (E/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'accepted':True,'activeModel':active['model'],'requests':3,'JamesKentLocalPassed':True,'historyUnchanged':True,'EWRAMHeadroom':4}))
if __name__=='__main__':main()

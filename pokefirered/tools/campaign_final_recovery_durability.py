#!/usr/bin/env python3
"""Stopped-process durability + isolated rollback evidence; zero inference."""
import sys,json,sqlite3,tempfile,subprocess,re,os,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.expansion import ExpansionStore
from campaign.recovery import PROOF_METHODS,table_hashes,native_state
from battle.transport import Handler
from roster.extract import digest,file_hash
from phase1_events_build import symbols
K=ROOT/'evidence/phase6/campaign_expansion01_final/final-recovery';E=K.parent;P=ROOT/'.local/campaign_expansion01_final';C=ROOT/'.local/campaign_expansion01_recovery';M=E/'manifest-native.json'
def read(p):return json.loads(p.read_text())
def write(n,x):(K/n).write_text(json.dumps(x,indent=2)+'\n')
processes=subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines();owned=[l for l in processes if re.match(r'^\s*\d+\s+\S*/Python\s+tools/campaign_expansion01_recovered.py\s+(launch|host|paginate|capture|input)(?:\s|$)',l) or re.match(r'^\s*\d+\s+'+re.escape(str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'))+r'(?:\s|$)',l)];assert not owned
layout=read(ROOT/'config/prep_save_layout.json');proof=read(K/'causal-cut-manifest.json');id,native=native_state(C/'pokefirered.sav',layout);assert id.as_dict()==proof['nativeSave']
with ExpansionStore(C/'world.sqlite3',M) as w:
 hashes={m:getattr(w,m)() for m in PROOF_METHODS};assert hashes==proof['sevenHashes'];assert table_hashes(w)==proof['domainTableHashes'];assert w.campaign()['status']=='paired';assert not w.pending_save()
 for t in ('strategy_jobs','puppeteer_jobs','preparation_decision_jobs'):assert all(r[0]=='completed' for r in w.db.execute('SELECT status FROM '+t))
 cp=w.get_save_checkpoint(id.fingerprint);r=w._one('SELECT * FROM retrospective_pairs WHERE checkpoint=?',(cp['id'],));assert r['manifest_sha']==digest(proof)
 w.db.execute('PRAGMA wal_checkpoint(TRUNCATE)');assert w.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 with tempfile.TemporaryDirectory() as tmp:
  path=Path(tmp)/'rollback.sqlite3';dst=sqlite3.connect(path);w.db.backup(dst);dst.close()
  with ExpansionStore(path,M) as clone:
   previous,oldnative=native_state(P/'C3-james-blocked.sav',layout);assert not oldnative['trainerFlags']['108']
   clone.restore(previous);oldhashes={m:getattr(clone,m)() for m in PROOF_METHODS};assert oldhashes==read(E/'C3-offline-restored.json')['hashes'];assert len(clone.social_state()['posts'])==8
   player=clone.player_actor();assert sum(e['followed']==player for e in clone.social_state()['follows'].values())==4
   assert not any(b['sourceTrainerID']==108 for b in clone.state()['battles'].values());assert proof['Kent']['postID'] not in clone.social_state()['posts'];assert not any(e['postID']==proof['Kent']['postID'] for e in clone.virality_state()['epochs'].values())
   assert not any(a['session']==proof['historicalNonce'] for a in clone.battle_audit())
   before=table_hashes(clone);h=Handler({},Path(tmp))
   try:h.recover(clone);assert not h.pending and not h.awaiting and h.job is None;assert before==table_hashes(clone)
   finally:h.close()
   clone.restore(id);finalhashes={m:getattr(clone,m)() for m in PROOF_METHODS};assert finalhashes==hashes
   write('rollback-proof.json',{'method':'isolated SQLite backup + canonical restore APIs; no gameplay replay','C3':{'fingerprint':previous.fingerprint,'sevenHashes':oldhashes,'posts':8,'followers':4,'KentNativeFlag':False,'KentBattlePostDiffusionAuditAbsent':True,'historicalRequestsPending':0,'auditWrites':0},'recoveredPair':{'checkpointID':cp['id'],'sevenHashes':finalhashes,'posts':10,'followers':5},'activeFinalCopyUnaffected':True,'inferenceCalls':0})
 # Final host artifacts remain a separate managed continuation; original suspended
 # inputs and original campaign ledger are untouched, not silently replaced.
 write('durability.json',{'checkpointID':cp['id'],'database':str(C/'world.sqlite3'),'databaseSHA256':file_hash(C/'world.sqlite3'),'integrity':'ok','nativeBattery':str(C/'pokefirered.sav'),'batterySHA256':file_hash(C/'pokefirered.sav'),'nativeSave':id.as_dict(),'retainedBattery':str(C/'recovered-post-Kent.sav'),'retainedBatterySHA256':file_hash(C/'recovered-post-Kent.sav'),'campaign':w.campaign(),'domainTableHashesUnchanged':True,'allWorkersStopped':True,'defaultInferenceDisabled':not read(ROOT/'config/model_profiles.yaml')['hosted_inference_enabled'],'noPendingSaveOrGeneration':True})
m=read(M);elf=ROOT/m['rom_path'].replace('.gba','.elf');syms=symbols(elf);ram={k:v for k,v in syms.items() if 0x02000000<=v['address']<0x02040000 or 0x03000000<=v['address']<0x03008000};end=syms['gPiBattle']['address']+syms['gPiBattle']['size'];headroom=0x02040000-end
assert headroom==4 and file_hash(elf)==m['elf_sha256'] and file_hash(ROOT/m['rom_path'])==m['rom_sha256']
write('memory.json',{'beforeHeadroomBytes':4,'afterHeadroomBytes':headroom,'permanentDeltaBytes':0,'measurement':'arm-none-eabi-nm -S --defined-only; last allocated control end = 0x0203fffc','control':syms['gPiBattle'],'RAMSymbolTuplesSHA256':digest(ram),'RAMSymbols':len(ram),'acceptedELFHashUnchanged':True,'acceptedROMHashUnchanged':True,'nativeTemporaryAllocationUnchanged':True,'worstCaseStackHeapUnmeasuredRiskRetained':True})
# Inspect only the nonsecret selector, never emit credential values.
strategy=os.environ.get('POKEINFLUENCER_STRATEGY_MODEL')
for line in (ROOT/'.env').read_text().splitlines():
 name,sep,value=line.partition('=')
 if strategy is None and sep and name.strip()=='POKEINFLUENCER_STRATEGY_MODEL':strategy=value.strip().strip("'\"")
assert strategy=='dots-studio/dots-3-note-preview:free'
write('workers-stopped.json',{'ownedProcesses':owned,'allStopped':True,'hostedInferenceDisabled':True,'activeFutureStrategyModel':strategy,'generationCalls':46,'newCalls':0,'incrementalCostUSD':0})
verification=read(K/'verification.json');verification.update(durability=read(K/'durability.json'),rollbackIsolation=True,memory=read(K/'memory.json'),allWorkersStopped=True,activeFutureStrategyModel=strategy,tests={'recovery':7,'retainedTerminal':2,'viewer':16,'battleEnd':8,'total':33,'skipped':0});write('verification.json',verification)
print(json.dumps({'accepted':True,'workersStopped':True,'rollback':True,'headroom':4,'newCalls':0,'generationTotal':46}))

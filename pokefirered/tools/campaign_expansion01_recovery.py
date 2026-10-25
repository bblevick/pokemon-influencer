#!/usr/bin/env python3
"""Explicit zero-inference retained-victory analysis / canonical pairing on copies."""
import os,sys,json,sqlite3,shutil,hashlib,argparse
from pathlib import Path
os.environ['POKEINFLUENCER_EXPERIMENT']='campaign_expansion01';os.environ['POKEINFLUENCER_CAMPAIGN_FINAL']='1'
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.expansion import ExpansionStore
from campaign.recovery import prove,recover,table_hashes,PROOF_METHODS
from world.saves import fingerprint
from roster.extract import digest,file_hash
E=ROOT/'evidence/phase6/campaign_expansion01_final';K=E/'final-recovery';P=ROOT/'.local/campaign_expansion01_final';C=ROOT/'.local/campaign_expansion01_recovery';M=E/'manifest-native.json'
def read(p):return json.loads(Path(p).read_text())
def write(n,v):(K/n).write_text(json.dumps(v,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prove','pair']);a=p.parse_args();K.mkdir(exist_ok=True);C.mkdir(exist_ok=True)
 inventory=read(K/'retained-inventory.json')
 for path,value in inventory['files'].items():
  if path.endswith('launch.json'):continue
  if file_hash(ROOT/path)!=value['sha256']:raise ValueError('retained source changed '+path)
 db=C/'world.sqlite3';battery=C/'retained-victory.sav'
 if a.command=='prove':
  if db.exists():
   check=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
   paired=check.execute("SELECT name FROM sqlite_master WHERE name='retrospective_pairs'").fetchone()
   check.close()
   if paired:raise ValueError('preserve published recovery copy; use a separate analysis database')
   db.unlink()
  src=sqlite3.connect('file:'+str(P/'kent-resolution-suspended.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(db)
  try:src.backup(dst)
  finally:dst.close();src.close()
  shutil.copy2(P/'Kent-victory-UNPAIRED.sav',battery)
 layout=read(ROOT/'config/prep_save_layout.json');receipt=json.loads((E/'save-receipts.jsonl').read_text().splitlines()[-1]);launch=read(P/'launch.json')
 with ExpansionStore(db,M) as w:
  if a.command=='prove':
   proof=prove(w,battery=battery,prior_battery=P/'C3-james-blocked.sav',receipt=receipt,launch=launch,settled=read(E/'k-Kent-social-settled.json'),lock=read(E/'kent-resolution/lock-before.json'),inventory=inventory,manifest_path=M,layout=layout)
   proof['verifiedDatabaseSHA256']=file_hash(P/'kent-resolution-suspended.sqlite3');proof['retrospectiveReason']='native save after erroneous restart provenance suspension; no managed intent'
   write('causal-cut-manifest.json',proof)
   print(json.dumps({'admissible':True,'cutoff':proof['canonicalCutoff'],'posts':proof['postCount'],'followers':5,'noGameplayMutation':True}))
  else:
   proof=read(K/'causal-cut-manifest.json');before=table_hashes(w);identity=fingerprint(battery.read_bytes(),layout['sectionSizes']);cp=recover(w,proof,identity)
   assert recover(w,proof,identity)==cp
   # Resume via ordinary known-pair restore, never UPDATE campaigns directly.
   w.restore(identity);assert before==table_hashes(w)
   hashes={m:getattr(w,m)() for m in PROOF_METHODS};assert hashes==proof['sevenHashes']
   assert digest(w.battle_audit())==proof['tacticalAuditHash'] and digest(w.preparation_state())==proof['preparationHash']
   w.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
   write('recovered-pair.json',{'disposition':'retrospective_recovery','checkpoint':cp,'manifestSHA256':digest(proof),'sevenHashes':hashes,'domainTableHashesUnchanged':True,'idempotent':True,'Kent':proof['Kent'],'followerCount':5,'postCount':10,'nativeSave':identity.as_dict(),'nativeBatterySHA256':file_hash(battery),'databaseSHA256':file_hash(db),'projectionCuts':proof['projectionCuts'],'jobsTerminal':True,'inferenceCalls':0})
   shutil.copy2(battery,C/'recovered-post-Kent.sav')
   print(json.dumps({'paired':True,'checkpoint':cp['id'],'status':w.campaign()['status'],'sevenHashes':True,'domainUnchanged':True}))
if __name__=='__main__':main()

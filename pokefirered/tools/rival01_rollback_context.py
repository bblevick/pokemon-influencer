#!/usr/bin/env python3
"""Current Save24 isolated qualification; no generation or active-world mutation."""
import os,sys,json,sqlite3,struct,hashlib,copy
from pathlib import Path
os.environ['POKEINFLUENCER_EXPERIMENT']='rival01';os.environ['POKEINFLUENCER_RIVAL_ROLLBACK']='1'
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from rival01 import E,PRIVATE,open_store,manifest,save_identity
from rival01_prerequisites import METHODS,history
from strategy.selection import public_candidates
from strategy.provider import live_configuration
from prep.domain import resolve_preparation_bundle
from world.saves import layout_from_build
from world.store import dump
from roster.hashes import digest
ACTOR='trainer:fr:trainer:0326'
def main():
 before=json.loads((E/'pre-rival-pair.json').read_text());after=json.loads((E/'pre-rival-reloaded.json').read_text())
 assert before['hashes']==after['hashes'] and before['checkpoint']==after['checkpoint']
 assert after['campaign']['cursor']==after['checkpoint']['cursor'] and not after['pendingSave']
 identity=save_identity(PRIVATE/'pre-rival-pair.sav');assert identity.as_dict()==after['save']
 data=(PRIVATE/'pre-rival-pair.sav').read_bytes();sizes=layout_from_build(ROOT/manifest()['rom_path']);sections={}
 for n in range(identity.slot*14,(identity.slot+1)*14):
  sec=data[n*4096:(n+1)*4096];sid=struct.unpack_from('<H',sec,4084)[0];sections[sid]=sec[:sizes[sid]]
 sb1=b''.join(sections[i] for i in range(1,5));x,y=struct.unpack_from('<hh',sb1);group,num=sb1[4:6]
 starter=struct.unpack_from('<H',sb1,0x1000+2*(0x4031-0x4000))[0];scene=struct.unpack_from('<H',sb1,0x1000+2*(0x4052-0x4000))[0]
 flag=lambda n:bool(sb1[0xee0+n//8]&(1<<(n%8)))
 flags={str(n):flag(0x500+n) for n in [91,120,170,351,334]}
 assert (group,num)==(3,3) and (x,y)==(22,8) and starter==scene==0
 assert all(flags[str(n)] for n in [91,120,170,351]) and not flags['334'] and flag(0x232)
 ledger=json.loads((E/'requests.json').read_text());assert ledger['closed'] and not ledger['attempts']
 native=json.loads((PRIVATE/'native-proof.json').read_text());health=json.loads((PRIVATE/'host-health.json').read_text())
 assert native['authenticated'] and native['eventCounter']==native['ack'] and native['drops']==native['depth']==0
 assert health['state']=='CONNECTED' and health['nonce']==native['nonce'] and health['cursor']==after['campaign']['cursor']
 out={'scope':'Normal pre-Rival Save24, real fresh offline Continue and isolated host-copy context qualification','checkpoint':after['checkpoint'],'save':after['save'],'hashesBefore':before['hashes'],'hashesAfter':after['hashes'],'allSevenProjectionsMatch':True,'nativePosition':[x,y],'nativeMap':[group,num],'starter':starter,'rivalScene':scene,'nativeTrainerDefeatedFlags':flags,'fossilGateComplete':flag(0x232),'native':native,'health':health,'hostedCalls':0,'activeCampaignMutated':False}
 target=PRIVATE/'current-context-qualification.sqlite3';assert not target.exists()
 src=sqlite3.connect('file:'+str(PRIVATE/'pre-rival-pair.sqlite3')+'?mode=ro',uri=True);dst=sqlite3.connect(target);src.backup(dst);dst.close();src.close()
 binding,_=live_configuration()
 with open_store(target) as w:
  initial={m:getattr(w,m)() for m in METHODS};jobs=history(w);mem=copy.deepcopy(w.for_actor(ACTOR).records(limit=256))
  adoption=w.adopt_content();rows=public_candidates(w,ACTOR);packet=w.context_packet(ACTOR,provider_binding=binding);audit=w.last_selection_audit
  assert dump(packet)==dump(w.context_packet(ACTOR,provider_binding=binding)) and history(w)==jobs
  assert w.for_actor(ACTOR).records(limit=256)==mem
  private={r['memoryID'] for r in w.virality_state()['intel'].values()}
  assert not private&{r['evidenceID'] for r in rows} and not private&set(audit['selectedEvidenceIDs'])
  assert len(dump(packet).encode())<=8192 and packet['modelInput']['opponentCurrentLead']=='UNKNOWN'
  cs=resolve_preparation_bundle(w,ACTOR,'first')['candidateSet']['candidates'];baseline=w.content.cat.own_baseline(ACTOR,334)['party'];assert len(cs)==1
  shape=lambda party:[(r['species'],r['level'],r['moves'],r['heldItem']) for r in party]
  assert shape(cs[0]['party'])==shape(baseline)
  out.update(isolatedContentAdoption=adoption,configuredStrategyBinding=binding,publicReceiptsRetained=len(rows),privateRocketReceiptsExcluded=len(private),memoryDeleted=False,strategyJobsUnchanged=True,contextBytes=len(dump(packet).encode()),contextID=packet['contextID'],contextHash=digest(packet),selectedEvidenceCount=len(audit['selectedEvidenceIDs']),selectedClaimCount=len(packet['modelInput']['authorizedSocialEvidence']['claims']),candidateCount=1,authoredParty=baseline,candidate=cs[0],isolatedBeforeHashes=initial)
  (E/'current-strategy-context.json').write_text(dump(packet)+'\n');(E/'current-selection-audit.json').write_text(json.dumps(audit,indent=2)+'\n');(E/'current-public-receipts.json').write_text(json.dumps(rows,indent=2)+'\n')
 with open_store(PRIVATE/'world.sqlite3') as w:
  assert {m:getattr(w,m)() for m in METHODS}==after['hashes'] and not w.pending_save()
  assert not any(not b['ended'] for b in w.state()['battles'].values()) and not any(m['actor']==ACTOR for m in w.memo_records())
 out['activeSevenHashesUnchanged']=True
 (E/'pre-rival-reload-context-proof.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({k:out[k] for k in ['contextBytes','publicReceiptsRetained','privateRocketReceiptsExcluded','selectedEvidenceCount','candidateCount','hostedCalls','activeSevenHashesUnchanged']}))
if __name__=='__main__':main()

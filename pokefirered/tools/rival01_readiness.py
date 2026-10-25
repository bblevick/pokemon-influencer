#!/usr/bin/env python3
"""Offline planning evidence only. Never adopts content or advances a save."""
import copy, hashlib, json, re, shutil, struct, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from campaign.rocket import RocketStore
from strategy.social_context import build_social_evidence
from world.saves import fingerprint,layout_from_build
from virality import policy
from roster.domain import Catalog
from roster.hashes import digest
from world.store import dump
E=ROOT/'evidence/phase8/rival01-readiness';PRIVATE=ROOT/'.local/rival01-readiness'
ACTOR='trainer:fr:trainer:0326';PIN='037335f4c725d7c9aecdac87066f2002b4bd7e14'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 E.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True)
 protected=[ROOT/'.local/rocket01/world.sqlite3',ROOT/'.local/rocket01/post-rocket-pair.sqlite3',ROOT/'.local/rocket01/post-rocket-pair.sav',ROOT/'.local/rocket01/pokefirered.sav',ROOT/'evidence/phase7/rocket01/requests.json']+list((ROOT/'config').glob('*.*'))
 before={str(p.relative_to(ROOT)):sha(p) for p in protected}
 reg=read('config/trainer_registry.json');catalog=read('config/roster_catalog.json');vp=read('config/virality_policy.json')
 cat=Catalog(catalog,read('config/roster_policy.json'));family=next(f for f in reg['families'] if f['kind']=='story_rival')
 assert len(family['sourceIDs'])==27 and all(reg['mapping'][str(i)]=='fr:trainer:0326' for i in family['sourceIDs'])
 parties={str(i):cat.own_baseline(ACTOR,i) for i in (332,333,334)}
 assert all(t['flags']==1 and not t['doubleBattle'] and not any(t['battleItems']) and not any(p['heldItem'] for p in t['party']) for t in parties.values())
 manifest=read('evidence/phase7/rocket01/manifest-native.json');sizes=layout_from_build(ROOT/manifest['rom_path'])
 data=(ROOT/'.local/rocket01/post-rocket-pair.sav').read_bytes();identity=fingerprint(data,sizes);sections={}
 for n in range(identity.slot*14,(identity.slot+1)*14):
  sector=data[n*4096:(n+1)*4096];sid,_,_,counter=struct.unpack_from('<HHII',sector,4084);assert counter==identity.counter;sections[sid]=sector[:sizes[sid]]
 sb1=b''.join(sections[i] for i in range(1,5));starter=struct.unpack_from('<H',sb1,0x1000+2*(0x4031-0x4000))[0];scene=struct.unpack_from('<H',sb1,0x1000+2*(0x4052-0x4000))[0]
 selected={0:334,1:333,2:332}[starter];assert starter==0 and selected==334 and scene==0
 clone=PRIVATE/'planning.sqlite3'
 if clone.exists():clone.unlink()
 shutil.copy2(ROOT/'.local/rocket01/post-rocket-pair.sqlite3',clone)
 methods=['verify_replay','verify_memory_replay','verify_social_replay','verify_puppeteer_replay','verify_strategy_replay','verify_decision_replay','verify_virality_replay']
 with RocketStore(clone,ROOT/'evidence/phase7/rocket01/manifest-native.json') as w:
  hashes={m:getattr(w,m)() for m in methods};social=w.social_state();viral=w.virality_state();packet=build_social_evidence(w,ACTOR);cp=w.get_save_checkpoint(identity.fingerprint)
  assert hashes==read('evidence/phase7/rocket01/hermes-disposition/disposition.json')['projectionHashes']
  assert {m:getattr(w,m)() for m in methods}==hashes
  assert all(r['evidenceQuality']['channel']=='pokebook' and r['mode']=='delivered' for r in packet['authorizedFacts'])
  posts=[]
  for p in social['posts'].values():
   feed=next(f for f in w.public_feed(ACTOR) if f['postID']==p['postID']);assert feed['seen']
   posts.append({'postID':p['postID'],'author':p['author'],'body':p['body'],'claims':p['claims'],'reason':feed['reason'],'publicationOrder':viral['epochs'][p['postID']]['publicationOrder']})
  grunt=next(p for p in posts if p['author']=='trainer:fr:trainer:0352');assert len(grunt['claims'])==2
  facts=[r for r in packet['authorizedFacts'] if r['attribution'].get('sender')=='trainer:fr:trainer:0352'];assert len(facts)==2 and {digest(r['claim']) for r in facts}=={digest(c) for c in grunt['claims']}
  private=viral['intel'];private_ids={v['memoryID'] for v in private.values()};assert len(private_ids)==47
  assert not private_ids&{r['evidenceID'] for r in packet['authorizedFacts']}
  frozen={k:copy.deepcopy(packet[k]) for k in ('schemaVersion','actorID','authorizedFacts','unknowns','truncated')}
  original_bytes=len(dump(frozen).encode());preview=copy.deepcopy(frozen)
  while len(dump(preview).encode())>8192 and preview['authorizedFacts']:
   preview['authorizedFacts'].pop();preview['truncated']=True
  assert len(dump(preview).encode())<=8192
  authored=parties[str(selected)];candidate={'visibility':'public','author':ACTOR,'sourceTrainerID':selected,'postID':'PLANNING_ONLY_NOT_PUBLISHED'}
  high=policy.plan(vp,player=w.player_actor(),post=candidate,edges=list(social['follows'].values()),known_actors=set(w.registry_actor_ids()),post_order=12)
  ordinary=viral['epochs'][grunt['postID']]
  assert high['prominence']=='rival' and high['reach']==vp['highProfile'] and ordinary['reach']['budget']==12
  eligible_downstream={a:next((f['reason'] for f in high['deliveries'] if f['recipient']==a),None) for a in ['trainer:fr:trainer:0415','trainer:fr:trainer:0150','trainer:fr:trainer:0234']}
  result={'status':'BLOCKED BEFORE IMPLEMENTATION','scope':'planning only; no production content/config/code adoption','sourceCommit':PIN,'acceptedCheckpoint':cp,'saveIdentity':identity.as_dict(),'sourceVars':{'saveBlock1VarsOffset':'0x1000','VAR_STARTER_MON':'0x4031','value':starter,'playerStarter':'Bulbasaur','rivalStarter':'Charmander','selectedNativeTrainerID':selected,'VAR_MAP_SCENE_CERULEAN_CITY_RIVAL':'0x4052','sceneValue':scene},'rivalFamily':family,'actorID':ACTOR,'partyVariants':parties,'publicPosts':posts,'publicProjection':packet,'privateRocketReceiptCount':47,'publicGruntClaims':2,'privateReceiptIDsAbsentFromRival':True,'highProfilePurePlanningPreview':high,'ordinaryComparison':{k:ordinary[k] for k in ['followerCount','reach','prominence','originStage']},'downstreamEligiblePreview':eligible_downstream,'projectionHashes':hashes,'blockers':['versioned campaign-distance/progression policy adoption retaining frozen old epochs','story no-intro content qualification and constructor receipt must resolve native334 to actor0326','18844-byte Rival frozen public projection exceeds8192-byte prebattle bound'],'prebattleBounds':{'actualFullPublicPacketBytes':len(dump(packet).encode()),'actualFrozenProjectionBytes':original_bytes,'acceptedFrozenMaximumBytes':8192,'currentlyWouldReject':original_bytes>8192,'pureRankedTailPreviewOnly':preview,'previewBytes':len(dump(preview).encode()),'previewFactCount':len(preview['authorizedFacts']),'durableEvidenceUnchanged':True},'configuredRivalProfile':vp['profiles'][ACTOR],'actualStrategyGenerated':False,'candidateSelected':False,'nativeBattleRun':False,'hostedCalls':0,'permanentEWRAMGrowth':0}
 sources=['data/maps/CeruleanCity/map.json','data/maps/CeruleanCity/scripts.inc','data/maps/CeruleanCity/text.inc','src/data/trainers.h','src/data/trainer_parties.h','src/battle_setup.c','src/save.c','include/global.h','include/constants/vars.h','asm/macros/event.inc','data/maps/MtMoon_B2F/scripts.inc','data/battle_scripts_1.s']
 result['inspectedSourceHashes']={p:sha(ROOT/p) for p in sources}
 result['pinnedSourceMatches']={p:hashlib.sha256(subprocess.check_output(['git','show',PIN+':'+p],cwd=ROOT)).hexdigest()==sha(ROOT/p) for p in sources}
 assert all(result['pinnedSourceMatches'].values())
 flags=(ROOT/'include/constants/flags.h').read_text();decoded={}
 for name in ['FLAG_GOT_FOSSIL_FROM_MT_MOON','FLAG_GOT_FAME_CHECKER','FLAG_DEFEATED_BROCK']:
  n=int(re.search(r'^#define '+name+r'\s+(0x[0-9A-Fa-f]+)',flags,re.M)[1],16);decoded[name]={'flag':n,'set':bool(sb1[0xEE0+n//8]&(1<<(n%8)))}
 for trainer in (170,332,333,334):
  n=0x500+trainer;decoded['trainerDefeated:'+str(trainer)]={'flag':n,'set':bool(sb1[0xEE0+n//8]&(1<<(n%8)))}
 assert not any(decoded['trainerDefeated:'+str(t)]['set'] for t in (170,332,333,334))
 result['nativeFlags']=decoded;result['nativeLocation']={'x':struct.unpack_from('<h',sb1,0)[0],'y':struct.unpack_from('<h',sb1,2)[0],'mapGroup':sb1[4],'mapNumber':sb1[5]}
 model=None
 for line in (ROOT/'.env').read_text().splitlines():
  name,sep,value=line.partition('=')
  if sep and name.strip()=='POKEINFLUENCER_STRATEGY_MODEL':model=value.strip().strip('\"').strip("'")
 result['configuredStrategySlotOnlyNoRouteCheck']=model
 after={str(p.relative_to(ROOT)):sha(p) for p in protected};assert before==after
 result['protectedFilesUnchanged']=before
 (E/'inspection.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'selected':selected,'playerStarter':starter,'rivalFamilySize':27,'posts':len(posts),'authorizedPublicFacts':len(packet['authorizedFacts']),'gruntPublicFacts':len(facts),'privateDenied':True,'protectedFilesUnchanged':True,'calls':0,'status':result['status']}))
if __name__=='__main__':main()

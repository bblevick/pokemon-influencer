"""Deterministic public opportunity context, never a memory mutation or inference."""
import copy,json
from jsonschema import Draft202012Validator
from world.store import ROOT,WorldError,dump
from roster.hashes import digest

PATH=ROOT/'config/context_selection_v1.json'
def load_policy():
 p=json.loads(PATH.read_text());base=json.loads((ROOT/'config/virality_policy.json').read_text())
 if p['version']!=1 or p['sourceCommit']!=base['sourceCommit'] or p['eligibleChannel']!='pokebook':raise WorldError('context selection policy identity')
 if not 0<p['maximumEvidenceBytes']<p['targetModelBytes']<p['maximumModelBytes']==8192:raise WorldError('context selection byte policy')
 for row in p['stageExtensions']:
  mp=json.loads((ROOT/row['source']).read_text());groups=json.loads((ROOT/'data/maps/map_groups.json').read_text())
  if mp['id']!=row['mapID'] or groups[groups['group_order'][row['mapGroup']]][row['mapNumber']]!=mp['name']:raise WorldError('context stage source')
 return p

def public_candidates(store,actor):
 """Filter actor grants and channel before descriptor/source/post lookup."""
 rows=[];after=0;social=store.social_state();epochs=store.virality_state()['epochs']
 while True:
  page=store.for_actor(actor).records(after=after,limit=256)
  for r in page['records']:
   source=r['source']
   if r['mode']!='delivered' or source.get('channel')!='pokebook':continue
   post=social['posts'].get(source.get('postID'))
   if not post or post['visibility']!='public' or r['claim'] not in post['claims'] or source.get('sender')!=post['author']:raise WorldError('public selection provenance')
   # This checks the existing recorded exposure, never causes exposure.
   store.read_public_post(actor,post['postID'])
   battle=store.get_battle(post['battleID']);epoch=epochs[post['postID']]
   labels={}
   for field,kind in [('speciesID','species'),('moveID','moves')]:
    if field in r['claim']:labels[field]=store.content.cat.lookup(kind,r['claim'][field])['symbols'][0].split('_',1)[1].replace('_',' ').title()
   rows.append({'labels':labels,'claim':copy.deepcopy(r['claim']),'evidenceID':r['memoryID'],'postID':post['postID'],'sourceActor':post['author'],'originalSourceActor':store._original_origin(r)[0],'channel':'pokebook','sourceTrainerID':battle['sourceTrainerID'],'publicationOrder':epoch['publicationOrder'],'originStage':epoch['originStage'],'prominence':epoch['prominence']})
  if not page['hasMore']:break
  after=page['records'][-1]['memoryCursor']
 return rows

def normalize(claim):
 # Observed capability claims may recur across battles; outcomes remain battle-specific.
 return {k:v for k,v in claim.items() if k not in ('trainerID',) and (k!='battleID' or claim['type']=='TRAINER_BATTLE_RESULT')}

def select(rows,base_model,*,actor,stage,opportunity,policy=None,evidence_budget=None):
 p=copy.deepcopy(policy or load_policy());budget=p['maximumEvidenceBytes'] if evidence_budget is None else evidence_budget
 if type(budget)!=int or not 0<budget<=p['maximumEvidenceBytes']:raise WorldError('context evidence budget')
 base=json.loads((ROOT/'config/virality_policy.json').read_text())
 orders={r['stageID']:r['order'] for r in base['progression']+p['stageExtensions']}
 if stage not in orders:raise WorldError('unqualified context stage')
 if any(r.get('channel')!='pokebook' for r in rows):raise WorldError('context selector public channel only')
 latest=max([r['publicationOrder'] for r in rows]+[0]);groups={};audit=[]
 for row in sorted(rows,key=lambda r:r['evidenceID']):
  if not row.get('evidenceID') or not row.get('postID') or not row.get('originalSourceActor'):raise WorldError('context reference required')
  claim=normalize(row['claim']);identity=digest(claim);origin=p['sourceEncounterStages'].get(str(row['sourceTrainerID']),row['originStage']);distance=abs(orders[stage]-orders[origin]) if origin in orders else None;lag=latest-row['publicationOrder']
  band='CURRENT' if distance is not None and distance<=1 and lag<=1 else 'RECENT' if distance is not None and distance<=3 and lag<=4 else 'OLDER'
  feature={'originStage':origin,'campaignDistance':distance,'publicationOrder':row['publicationOrder'],'publicationLag':lag,'currentRelevance':band,'sourceQuality':'HIGH','prominence':row['prominence']}
  r={**copy.deepcopy(row),'features':feature,'claimID':identity}
  groups.setdefault(identity,{'claimID':identity,'claim':claim,'rows':[]})['rows'].append(r)
 # Contradiction: incompatible terminal outcomes for the same battle. Other observations
 # (different species/moves) are coexisting facts, not assumed contradictions.
 conflicts={}
 for identity,g in groups.items():
  c=g['claim']
  if c['type']=='TRAINER_BATTLE_RESULT':conflicts.setdefault(c['battleID'],[]).append(identity)
 for identity,g in groups.items():
  origins={(r['originalSourceActor'],r['claim'].get('battleID')) for r in g['rows']};g['independentOriginCount']=len(origins)
  related=conflicts.get(g['claim'].get('battleID'),[]);g['conflicts']=sorted(i for i in related if i!=identity)
  def rank(r):
   f=r['features'];return (0 if f['prominence']!='ordinary' else 1,{'CURRENT':0,'RECENT':1,'OLDER':2}[f['currentRelevance']],-len(origins),0 if g['claim']['type'] in ('MOVE_REVEALED','ITEM_USE_OBSERVED','POKEMON_SEEN') else 1,-f['publicationOrder'],r['evidenceID'])
  g['rows'].sort(key=rank);g['rank']=rank(g['rows'][0])[:-1]+(identity,)
 ordered=sorted(groups.values(),key=lambda g:g['rank']);selected=[];selected_ids=set();handled=set()
 def compact(g):
  refs=[];seen=set()
  for r in g['rows']:
   origin=(r['originalSourceActor'],r['claim'].get('battleID'))
   if origin in seen:continue
   seen.add(origin);f=r['features'];refs.append({'evidenceID':r['evidenceID'],'postID':r['postID'],'sourceActor':r['sourceActor'],'originalSourceActor':r['originalSourceActor'],'originStage':f['originStage'],'publicationOrder':f['publicationOrder'],'currentRelevance':f['currentRelevance'],'campaignDistance':f['campaignDistance'],'prominence':f['prominence']})
   if len(refs)>=p['maximumReferencesPerClaim']:break
  return {'claimID':g['claimID'],'claim':g['claim'],'labels':g['rows'][0].get('labels',{}),'channel':'pokebook','attribution':'reported','sourceQuality':'HIGH','independentOriginCount':g['independentOriginCount'],'references':refs,'conflictingClaimIDs':g['conflicts']}
 out=copy.deepcopy(base_model);out['authorizedSocialEvidence']={'schemaVersion':4,'actorID':actor,'channel':'pokebook','claims':[],'truncated':False}
 out['contextSelection']={'policyID':p['policyID'],'version':p['version'],'policySHA256':digest(p),'opportunityID':opportunity,'campaignStage':stage,'eligibleReceiptCount':len(rows),'normalizedClaimCount':len(groups)}
 if len(dump(out).encode('utf-8'))>p['targetModelBytes']:raise WorldError('required non-evidence context exceeds target')
 for g in ordered:
  if g['claimID'] in handled:continue
  # Conflict groups are atomic: never select one side and hide the other.
  bundle=[g]+[groups[i] for i in g['conflicts']];handled.update(x['claimID'] for x in bundle)
  candidate=selected+[compact(x) for x in sorted(bundle,key=lambda x:x['rank'])]
  trial=copy.deepcopy(out);trial['authorizedSocialEvidence']['claims']=candidate
  if len(dump(candidate).encode())<=budget and len(dump(trial).encode('utf-8'))<=p['targetModelBytes']:
   selected=candidate;selected_ids.update(x['claimID'] for x in bundle)
 out['authorizedSocialEvidence']['claims']=selected;out['authorizedSocialEvidence']['truncated']=len(selected)<len(groups) or any(len(g['rows'])>p['maximumReferencesPerClaim'] for g in ordered)
 Draft202012Validator(json.loads((ROOT/'schemas/strategy/selected_public_context.schema.json').read_text())).validate({k:out[k] for k in ('authorizedSocialEvidence','contextSelection')})
 assert len(dump(out).encode('utf-8'))<=p['maximumModelBytes']
 references=[r['evidenceID'] for c in selected for r in c['references']]
 for g in ordered:
  for r in g['rows']:
   reason='selected_reference' if r['evidenceID'] in references else 'deduplicated_corroboration_reference_budget' if g['claimID'] in selected_ids else 'priority_byte_budget_omitted_from_context'
   audit.append({**r,'independentOriginCount':g['independentOriginCount'],'conflictingClaimIDs':g['conflicts'],'priority':g['rank'],'selectedClaim':g['claimID'] in selected_ids,'selectedReference':r['evidenceID'] in references,'reason':reason})
 return out,{'policy':p,'policySHA256':digest(p),'actorID':actor,'stage':stage,'opportunityID':opportunity,'eligible':audit,'groups':[{'claimID':g['claimID'],'claim':g['claim'],'evidenceIDs':[r['evidenceID'] for r in g['rows']],'independentOriginCount':g['independentOriginCount'],'conflicts':g['conflicts']} for g in ordered],'selectedClaimIDs':sorted(selected_ids),'selectedEvidenceIDs':references,'omittedClaimIDs':sorted(set(groups)-selected_ids),'bytesAfter':len(dump(out).encode('utf-8')),'memoryDeleted':False}

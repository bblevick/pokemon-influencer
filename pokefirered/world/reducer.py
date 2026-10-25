"""Pure canonical-fact reducer v1; observations and knowledge are not inputs."""
VERSION=1
def empty():return {'reducerVersion':VERSION,'trainers':{},'battles':{},'cursor':0}
def apply(state,event,registry):
 r=event['record'];t=r['eventType'];p=r['payload'];bid=event['battleID'];eid=event['eventID'];cursor=event['cursor']
 if r['recordClass']!='canonical_event':raise ValueError('observation is not canonical')
 if cursor!=state['cursor']+1:raise ValueError('canonical cursor discontinuity')
 if t=='BATTLE_STARTED':
  if bid in state['battles']:raise ValueError('world battle reused')
  if any(not b['ended'] for b in state['battles'].values()):raise ValueError('concurrent ordinary battle lifecycle')
  trainer=registry['mapping'].get(str(p['trainerID'])) if p['trainerID'] else None
  if p['trainerID'] and not trainer:raise ValueError('unknown trainer record')
  state['battles'][bid]={'battleID':bid,'trainerID':trainer,'sourceTrainerID':p['trainerID'],'startEvent':eid,'ended':False,'defeated':False,'turn':0,'outcome':None}
  if trainer:
   f=state['trainers'].setdefault(trainer,{'worldTrainerID':trainer,'encounters':0,'completedBattles':0,'defeats':0,'firstEncounterEvent':eid,'latestEncounterEvent':eid,'battleIDs':[]})
   f['encounters']+=1;f['latestEncounterEvent']=eid;f['battleIDs'].append(bid)
 else:
  b=state['battles'].get(bid)
  if not b or b['ended']:raise ValueError('canonical battle lifecycle')
  b['turn']=r['turnID']
  if t=='TRAINER_DEFEATED':
   if b['defeated'] or not b['trainerID']:raise ValueError('duplicate/missing trainer defeat')
   b['defeated']=True;state['trainers'][b['trainerID']]['defeats']+=1
  if t=='BATTLE_ENDED':
   if b['trainerID'] and (p['outcome']==1)!=b['defeated']:raise ValueError('missing/inconsistent defeat event')
   b['ended']=True;b['outcome']=p['outcome'];b['endEvent']=eid
   if b['trainerID']:state['trainers'][b['trainerID']]['completedBattles']+=1
 state['cursor']=cursor
 return state

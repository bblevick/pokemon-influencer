"""Source-qualified scripted singles content, independent of ordinary sight rules."""
import copy,json,re
from .rocket import RocketContent
from .policy import ROOT
from roster.hashes import digest,file_hash
from strategy.selection import load_policy

class ScriptedContent(RocketContent):
 @classmethod
 def load(cls,root=ROOT,starter=None):
  previous=RocketContent.load(root);config=json.loads((root/'config/scripted_encounters.json').read_text());starter=config['selectedStarter'] if starter is None else starter
  if type(starter)!=int or starter not in (0,1,2):raise ValueError('invalid source starter')
  if config['sourceCommit']!=previous.data['sourceCommit'] or config['parentContentSHA256']!=previous.hash or config['version']!=1:raise ValueError('scripted content version/parent')
  if any(file_hash(root/p)!=h for p,h in config['sourceEvidence'].items()):raise ValueError('scripted encounter source changed')
  obj=object.__new__(cls);obj.__dict__=copy.deepcopy(previous.__dict__);obj.previous=previous;obj.scripted=config
  additions={};participation={}
  for encounter in config['encounters']:
   actor=encounter['actor'];native=encounter['starterBranches'][str(starter)]['sourceTrainer'];baseline=obj.cat.own_baseline(actor,native)
   if baseline['doubleBattle'] or any(baseline['battleItems']) or any(p['heldItem'] for p in baseline['party']):raise ValueError('unsupported scripted battle mode/items')
   source=(root/encounter['scriptSource']).read_text();mp=json.loads((root/encounter['mapSource']).read_text());family=obj.registry['trainers'][actor[8:]]
   if encounter['sourceVariants']!=[r['sourceID'] for r in family['sourceRecords']]:raise ValueError('scripted persistent family')
   triggers=[r for r in mp['coord_events'] if r['var']==encounter['sceneVar']]
   if triggers!=encounter['triggers'] or mp['id']!=encounter['mapID']:raise ValueError('scripted trigger binding')
   for value,branch in encounter['starterBranches'].items():
    native_party=obj.cat.own_baseline(actor,branch['sourceTrainer']);symbol=native_party['symbols'][0]
    body=source.split(branch['script']+'::',1)[1].split('\n\n',1)[0]
    if 'trainerbattle_no_intro '+symbol not in body or 'call_if_eq VAR_STARTER_MON, '+value+', '+branch['script'] not in source:raise ValueError('scripted starter branch binding')
   social=json.loads((root/'config/virality_policy.json').read_text())
   if social['profiles'][actor]['rocketRole']!='none' or any(social['sourceActors'][str(b['sourceTrainer'])]!=actor or social['eventKinds'][str(b['sourceTrainer'])]!='rival' for b in encounter['starterBranches'].values()):raise ValueError('scripted trusted public event class')
   t=copy.deepcopy(previous.pack['trainers']['trainer:fr:trainer:0352']);t.update(displayName='Rival',worldTrainerID=actor[8:],sourceTrainer=native,qualifiedVariant=native,sourceVariants=encounter['sourceVariants'],homeMap=encounter['mapID'],mapEvidence=list(config['sourceEvidence']),regions={encounter['mapID']:{'tier':'native','requires':[]}},originals=baseline['party'],retainedOrigins=[p['baselineKey'] for p in baseline['party']],signatureOrigins=[baseline['party'][-1]['baselineKey']],designProvenance='Scripted source first encounter; authored custom moves, unchanged partners/levels/resources')
   t['stages']={'first':{'predicate':'boulder_required','targets':{p['baselineKey']:p['level'] for p in baseline['party']},'stageCeiling':max(p['level'] for p in baseline['party']),'gain':0}}
   t['resources'].update(owner=actor,initialBattleItems=baseline['battleItems'],initialHeldItems={p['baselineKey']:p['heldItem'] for p in baseline['party']})
   additions[actor]=t;participation[actor]={'sourceTrainer':native,'qualifiedSourceIDs':sorted(b['sourceTrainer'] for b in encounter['starterBranches'].values()),'stage':'first','battleProfile':'authored-single-no-items','strategy':True,'recap':True,'follow':'excluded-hostile','persona':encounter['persona'],'preparationSelection':'sole-choice-only','mapID':encounter['mapID'],'campaignStage':encounter['campaignStage'],'encounterID':encounter['encounterID'],'contextPolicy':'campaign-public-context-1'}
  obj.delta={'version':1,'packID':config['packID'],'trainers':additions,'participation':participation}
  obj.pack=copy.deepcopy(previous.pack);obj.pack['version']+=1;obj.pack['trainers'].update(additions)
  obj.extension=copy.deepcopy(previous.extension);obj.extension['trainers'].update(additions);obj.extension['participation'].update(participation);obj.extension.update(version=3,packID=config['packID']);obj.selection_policy=load_policy();obj.pack['scriptedQualification']={'configurationSHA256':digest(config),'selectedStarter':starter,'contextSelectionPolicySHA256':digest(obj.selection_policy)};obj.hash=digest(obj.pack);obj.selected_starter=starter
  return obj

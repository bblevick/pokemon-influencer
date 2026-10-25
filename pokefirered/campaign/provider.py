"""Shared budget adapter for existing guarded providers; no model substitution."""
import hashlib,json,subprocess,sys,time,os
from pathlib import Path
from .budget import CampaignBudget
from strategy.provider import ProviderError
ROOT=Path(__file__).resolve().parents[1]
EXPERIMENT=os.environ.get('POKEINFLUENCER_EXPERIMENT','vertical_slice01')
if EXPERIMENT not in ('vertical_slice01','campaign_expansion01','rocket01','rival01'):raise ValueError('unknown campaign experiment')
PRIVATE=ROOT/'.local'/EXPERIMENT
E=ROOT/('evidence/phase6/campaign_expansion01' if EXPERIMENT=='campaign_expansion01' else 'evidence/phase4/vertical_slice01')
if os.environ.get('POKEINFLUENCER_CAMPAIGN_FINAL')=='1':
    if EXPERIMENT!='campaign_expansion01':raise ValueError('final closeout requires expansion')
    PRIVATE=ROOT/'.local/campaign_expansion01_final'
    E=ROOT/'evidence/phase6/campaign_expansion01_final'
if EXPERIMENT=='rocket01':E=ROOT/'evidence/phase7/rocket01'
if EXPERIMENT=='rival01':E=ROOT/'evidence/phase8/rival01'
if os.environ.get('POKEINFLUENCER_RIVAL_ROLLBACK')=='1':
    if EXPERIMENT!='rival01':raise ValueError('rollback namespace requires Rival scope')
    PRIVATE=ROOT/'.local/rival01-rollback';E=ROOT/'evidence/phase8/rival01-rollback'
LEDGER=E/'requests.json'
class RoleBudget(CampaignBudget):
    role=None
    def charge(self,job,model):
        return super().charge(self.role,job,model,hashlib.sha256((self.role+':'+job).encode()).hexdigest())
class StrategyBudget(RoleBudget):
    role='strategy'
    def charge(self,job,model):
        n=super().charge(job,model)
        if EXPERIMENT=='rival01':
            value=self.read();value['attempts'][n-1].update(scope={'actor':'trainer:fr:trainer:0326','trainerID':334},verifiedFree=True);self.write(value)
        return n
class BattleBudget(RoleBudget):role='battle'

def scoped_battle_budget(scope):
    class ScopedBattleBudget(BattleBudget):
        def charge(self,job,model):
            if EXPERIMENT=='rocket01' and scope.get('trainerID') not in [p['sourceTrainer'] for p in json.loads((ROOT/'config/rocket_content.json').read_text())['participation'].values()]:raise ValueError('Rocket battle authorization scope')
            if EXPERIMENT=='rival01' and (scope.get('trainerID')!=334 or scope.get('actor')!='trainer:fr:trainer:0326'):raise ValueError('Rival battle authorization scope')
            n=super().charge(job,model);value=self.read()
            value['attempts'][n-1]['scope']=scope
            value['attempts'][n-1]['verifiedFree']=True
            self.write(value);return n
    return ScopedBattleBudget

class CampaignBattleProvider:
    def __init__(self,route,gym_closeout=False):self.route=route;self.failed=False;self.gym_closeout=gym_closeout;self.encounter_scope=None
    def decide_scoped(self,packet):
        native=packet['nativeState']
        if EXPERIMENT=='rocket01' and native['trainerID'] not in [p['sourceTrainer'] for p in json.loads((ROOT/'config/rocket_content.json').read_text())['participation'].values()]:return None
        if EXPERIMENT=='rival01' and native['trainerID']!=334:return None
        if self.gym_closeout and native['trainerID']!=414:return None
        # A provider failure degrades this encounter, never every future trainer
        # in a persistent campaign process. No retry within the failed battle.
        encounter=tuple(packet['scope'][k] for k in ('campaign','branch','nonce','generation','battle'))
        if encounter!=self.encounter_scope:
            self.encounter_scope=encounter;self.failed=False
        scope={**packet['scope'],'battle':native['battle'],'turn':native['turn'],'phase':native['phase'],'nonce':native['nonce'],'trainerID':native['trainerID'],'strategyID':packet['strategyID'],'commitmentID':packet['commitmentID']}
        if EXPERIMENT=='rival01':scope['actor']='trainer:fr:trainer:0326'
        return self.decide(packet['state'],packet['question'],packet['choices'],scope)
    def decide(self,state,question,choices,scope=None):
        if self.failed:return None
        job='battle:'+hashlib.sha256(json.dumps([state,question,choices],sort_keys=True).encode()).hexdigest()
        payload={'state':state,'question':question,'choices':choices,'jobID':job,'route':self.route(),'auditScope':scope}
        try:
            r=subprocess.run([sys.executable,str(ROOT/'tools/vertical_slice01_worker.py'),'battle'],input=json.dumps(payload),capture_output=True,text=True,timeout=2.55,cwd=ROOT)
            if r.returncode:raise ProviderError('campaign_battle_worker_failure')
            return json.loads(r.stdout)
        except (OSError,ValueError,subprocess.TimeoutExpired):
            self.failed=True
            return None

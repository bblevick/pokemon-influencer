"""One durable authorization ledger shared by all hosted campaign roles.

Charge immediately before each hosted POST, including failed/smoke requests.
The charge itself is short. Legacy adapter calls may retain the ledger lock
over HTTP; no SQLite transaction or emulator callback waits on that inference.
Unknown interrupted outcomes remain charged.
"""
import fcntl,json,os,time,hashlib
from pathlib import Path
from world.store import WorldError

RIVAL_LIMITS={'puppeteer':4,'strategy':1,'preparation':0,'battle':32}
ROCKET_LIMITS={'puppeteer':6,'strategy':4,'preparation':4,'battle':36}
EXPANSION_FINAL_ADDITIONAL={'puppeteer':12,'strategy':2,'preparation':0,'battle':84}
EXPANSION_LIMITS={'puppeteer':12,'strategy':10,'preparation':6,'battle':40}
LIMITS={'puppeteer':6,'strategy':4,'preparation':2,'battle':20}
CLOSEOUT_LIMITS={'puppeteer':10,'strategy':4,'preparation':2,'battle':16}
TACTICAL_LIMITS={'puppeteer':10,'strategy':2,'preparation':0,'battle':20}
GYM_LIMITS={'puppeteer':12,'strategy':2,'preparation':0,'battle':56}
FINAL_LIMITS={'puppeteer':12,'strategy':2,'preparation':0,'battle':136}
def attempts_hash(rows):return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
class CampaignBudget:
    def __init__(self,path):self.path=Path(path)
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=self.path.with_suffix('.lock').open('a')
        fcntl.flock(self.lock,fcntl.LOCK_EX)
        return self
    def __exit__(self,*args):self.lock.close()
    def read(self):
        value=json.loads(self.path.read_text()) if self.path.exists() else {'version':1,'maximumAttempts':30,'roleLimits':LIMITS,'closed':False,'attempts':[]}
        extension=value.get('gymCloseoutAuthorization');final=value.get('finalCloseoutAuthorization')
        final_pack=value.get('campaignExpansionFinalAuthorization')
        if value.get('rivalAuthorization'):
            if value.get('maximumAttempts')!=40 or value.get('roleLimits')!=RIVAL_LIMITS or value['rivalAuthorization'].get('source')!='c5a5c563-de12-4360-8918-e08aadc95b75' or any(value.get(k) for k in ('rocketAuthorization','campaignExpansionAuthorization','campaignExpansionFinalAuthorization','gymCloseoutAuthorization','finalCloseoutAuthorization')):raise WorldError('campaign_budget_configuration')
        elif value.get('rocketAuthorization'):
            qualification=value.get('rocketQualificationAuthorization')
            expected={**ROCKET_LIMITS,'puppeteer':8} if qualification else ROCKET_LIMITS
            if value.get('maximumAttempts')!=50 or value.get('roleLimits')!=expected or value['rocketAuthorization'].get('source')!='a0b57b8b-d8fe-43cf-9e1a-551e19afa986' or any(value.get(k) for k in ('campaignExpansionAuthorization','campaignExpansionFinalAuthorization','gymCloseoutAuthorization','finalCloseoutAuthorization')):raise WorldError('campaign_budget_configuration')
            if qualification and (qualification.get('source')!='bf5ff62a-082c-4461-87b5-fe26d207cbc1' or qualification.get('baseAttempts')!=16 or qualification.get('maximumAdditional')!=4 or attempts_hash(value['attempts'][:16])!=qualification.get('priorAttemptsSHA256')):raise WorldError('rocket_qualification_configuration')
        elif final_pack:
            base=final_pack.get('baseAttempts')
            if base!=16 or value.get('maximumAttempts')!=114 or final_pack.get('additionalLimits')!=EXPANSION_FINAL_ADDITIONAL or final_pack.get('source')!='41409a11-c0c0-42d7-b291-c9b5954edd9f' or attempts_hash(value['attempts'][:16])!=final_pack.get('originalAttemptsSHA256'):raise WorldError('campaign_budget_configuration')
            expected={r:sum(a['role']==r for a in value['attempts'][:16])+cap for r,cap in EXPANSION_FINAL_ADDITIONAL.items()}
            if value.get('roleLimits')!=expected:raise WorldError('campaign_budget_configuration')
        elif value.get('campaignExpansionAuthorization'):
            if value.get('maximumAttempts')!=60 or value.get('roleLimits')!=EXPANSION_LIMITS or extension or final or value['campaignExpansionAuthorization'].get('source')!='5eed1f3e-2320-4838-82ed-7cb5c3932b1c':raise WorldError('campaign_budget_configuration')
        elif final:
            if value.get('maximumAttempts')!=150 or value.get('roleLimits')!=FINAL_LIMITS or final.get('baseAttempts')!=66 or final.get('additionalLimits')!={'battle':80,'puppeteer':4,'strategy':0,'preparation':0} or attempts_hash(value['attempts'][:66])!=final.get('originalAttemptsSHA256'):raise WorldError('campaign_budget_configuration')
            if not extension or attempts_hash(value['attempts'][:30])!=extension.get('originalAttemptsSHA256'):raise WorldError('campaign_budget_configuration')
        elif extension:
            if value.get('maximumAttempts')!=70 or value.get('roleLimits')!=GYM_LIMITS or extension.get('baseAttempts')!=30 or extension.get('additionalLimits')!={'battle':36,'puppeteer':4,'strategy':0,'preparation':0} or attempts_hash(value['attempts'][:30])!=extension.get('originalAttemptsSHA256'):raise WorldError('campaign_budget_configuration')
        elif value.get('maximumAttempts')!=30 or value.get('roleLimits') not in (LIMITS,CLOSEOUT_LIMITS,TACTICAL_LIMITS):raise WorldError('campaign_budget_configuration')
        kent=value.get('kentResolutionAuthorization')
        if kent:
            if not final_pack or kent.get('source')!='58e9f038-4bd7-4968-9810-8099cda64055' or kent.get('baseAttempts')!=52 or kent.get('remainingLimits')!={'battle':53,'puppeteer':8,'strategy':0,'preparation':0} or attempts_hash(value['attempts'][:52])!=kent.get('priorAttemptsSHA256'):raise WorldError('campaign_kent_configuration')
        if value.get('version')!=1:raise WorldError('campaign_budget_configuration')
        return value
    def write(self,value):
        temp=self.path.with_suffix('.tmp')
        with temp.open('w') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        temp.chmod(0o600);os.replace(temp,self.path)
    def charge(self,role,job,model,request_hash):
        value=self.read()
        if role not in LIMITS or not all(isinstance(x,str) and x for x in (job,model,request_hash)):raise WorldError('campaign_budget_identity')
        attempts=value['attempts']
        qualification=value.get('rocketQualificationAuthorization')
        if qualification and (role!='puppeteer' or not job.startswith('qualification:') or len(attempts)>=20):raise WorldError('rocket_disposition_qualification_only')
        if value['closed'] or len(attempts)>=value['maximumAttempts'] or sum(a['role']==role for a in attempts)>=value['roleLimits'][role]:raise WorldError('campaign_budget_closed_or_exhausted')
        extension=value.get('campaignExpansionFinalAuthorization') or value.get('finalCloseoutAuthorization') or value.get('gymCloseoutAuthorization')
        if extension and sum(a['role']==role for a in attempts[extension['baseAttempts']:])>=extension['additionalLimits'][role]:raise WorldError('campaign_budget_closed_or_exhausted')
        if any(a['role']==role and a['requestHash']==request_hash and a['jobID']==job for a in attempts):raise WorldError('campaign_budget_duplicate')
        kent=value.get('kentResolutionAuthorization')
        if kent and sum(a['role']==role for a in attempts[kent['baseAttempts']:])>=kent['remainingLimits'][role]:raise WorldError('campaign_kent_role_closed_or_exhausted')
        # Models remain supplied by verified provider bindings, never chosen here.
        number=len(attempts)+1
        attempts.append({'attempt':number,'role':role,'jobID':job,'requestedModel':model,'requestHash':request_hash,'startedAtUnix':time.time(),'outcome':None})
        self.write(value);return number
    def finish(self,attempt,outcome):
        value=self.read()
        if type(attempt)!=int or not 1<=attempt<=len(value['attempts']):raise WorldError('campaign_budget_unknown_attempt')
        row=value['attempts'][attempt-1]
        if value.get('rocketQualificationAuthorization') and attempt<=16 and row['outcome']!=outcome:raise WorldError('rocket_prior_sixteen_immutable')
        if value.get('kentResolutionAuthorization') and attempt<=52 and row['outcome']!=outcome:raise WorldError('campaign_prior_fifty_two_immutable')
        if value.get('campaignExpansionFinalAuthorization') and attempt<=16 and row['outcome']!=outcome:raise WorldError('campaign_original_sixteen_immutable')
        frozen=66 if value.get('finalCloseoutAuthorization') else 30
        if value.get('gymCloseoutAuthorization') and attempt<=frozen and row['outcome']!=outcome:raise WorldError('campaign_original_thirty_immutable')
        if row['outcome'] is not None and row['outcome']!=outcome:raise WorldError('campaign_budget_conflicting_outcome')
        row['outcome']=outcome;self.write(value)
    def close(self):
        value=self.read();value['closed']=True;self.write(value)
    def continue_authorized_run(self):
        """Explicit managed continuation of D37, never a new request allowance."""
        value=self.read()
        if not value['closed'] or len(value['attempts'])>=value['maximumAttempts']:raise WorldError('campaign_continuation_not_closed_or_exhausted')
        value.setdefault('continuations',[]).append({'atUnix':time.time(),'priorAttempts':len(value['attempts']),'reason':('RIVAL-01 managed restart within original40 and lower readiness role caps' if value.get('rivalAuthorization') else 'ROCKET-01 managed restart within original50/nonfungible role caps' if value.get('rocketAuthorization') else 'CAMPAIGN-EXPANSION-01 final managed continuation within additional98/nonfungible role caps' if value.get('campaignExpansionFinalAuthorization') else 'CAMPAIGN-EXPANSION-01 managed restart within original60/role caps' if value.get('campaignExpansionAuthorization') else 'VERTICAL-SLICE-01 managed restart within the same authorization and aggregate caps')})
        value['closed']=False;self.write(value)

    def authorize_rival(self):
        if self.path.exists():raise WorldError('Rival requires new isolated ledger')
        self.write({'version':1,'maximumAttempts':40,'roleLimits':RIVAL_LIMITS,'closed':False,'attempts':[],'rivalAuthorization':{'source':'c5a5c563-de12-4360-8918-e08aadc95b75','scope':'Cerulean native334 actor0326 only; lower readiness caps win; no PREP inference','atUnix':time.time()}})

    def authorize_rocket(self):
        if self.path.exists():raise WorldError('Rocket requires new isolated ledger')
        self.write({'version':1,'maximumAttempts':50,'roleLimits':ROCKET_LIMITS,'closed':False,'attempts':[],'rocketAuthorization':{'source':'a0b57b8b-d8fe-43cf-9e1a-551e19afa986','scope':'selected MtMoon member only; no leader inference','atUnix':time.time()}})

    def authorize_rocket_qualification(self):
        value=self.read()
        if not value.get('rocketAuthorization') or value.get('rocketQualificationAuthorization') or not value['closed'] or len(value['attempts'])!=16:raise WorldError('qualification_requires_original_closed_sixteen')
        value['rocketQualificationAuthorization']={'source':'bf5ff62a-082c-4461-87b5-fe26d207cbc1','baseAttempts':16,'maximumAdditional':4,'priorAttemptsSHA256':attempts_hash(value['attempts']),'scope':'discard-only synthetic Hermes qualification; no gameplay/Strategy/PREP/Mercury','atUnix':time.time()}
        value['roleLimits']={**ROCKET_LIMITS,'puppeteer':8};value['closed']=False;self.write(value)

    def authorize_campaign_expansion(self):
        if self.path.exists():raise WorldError('expansion requires new isolated ledger')
        self.write({'version':1,'maximumAttempts':60,'roleLimits':EXPANSION_LIMITS,'closed':False,'attempts':[],'campaignExpansionAuthorization':{'source':'5eed1f3e-2320-4838-82ed-7cb5c3932b1c','scope':'selected ordinary Route3/MtMoon content pack only','atUnix':time.time()}})

    def authorize_gym_closeout(self):
        """User-authorized +40, one time; freeze all original thirty receipts."""
        value=self.read()
        if not value['closed'] or value['maximumAttempts']!=30 or len(value['attempts'])!=30 or value['roleLimits']!=TACTICAL_LIMITS:raise WorldError('gym_closeout_requires_closed_original_thirty')
        value['gymCloseoutAuthorization']={'baseAttempts':30,'additionalLimits':{'battle':36,'puppeteer':4,'strategy':0,'preparation':0},'originalAttemptsSHA256':attempts_hash(value['attempts']),'atUnix':time.time(),'source':'user VERTICAL-SLICE-01 CLOSEOUT 67416101-a9fb-4d41-93e4-7df652b90328','scope':'same pre-Brock accepted memo/lock; only Brock live battle and successful fully-live victory recap'}
        value['maximumAttempts']=70;value['roleLimits']=GYM_LIMITS;self.write(value)

    def authorize_final_closeout(self):
        """User54a7d48c: +80 battle, four unused recap slots; first66 immutable."""
        value=self.read()
        if not value['closed'] or value['maximumAttempts']!=70 or len(value['attempts'])!=66 or value['roleLimits']!=GYM_LIMITS:raise WorldError('final_closeout_requires_closed_sixty_six')
        value['finalCloseoutAuthorization']={'baseAttempts':66,'additionalLimits':{'battle':80,'puppeteer':4,'strategy':0,'preparation':0},'originalAttemptsSHA256':attempts_hash(value['attempts']),'atUnix':time.time(),'source':'user VERTICAL-SLICE-01 FINAL LIVE CLOSEOUT 54a7d48c-7c92-4e5b-98cf-021f5dd69a91','scope':'unchanged accepted pre-Brock memo/lock; Brock tactics and fully-live victory recap only'}
        value['maximumAttempts']=150;value['roleLimits']=FINAL_LIMITS;self.write(value)

    def rebalance_closeout(self):
        """Explicit reallocation of recommended role bounds; total remains thirty."""
        value=self.read()
        if not value['closed'] or value['roleLimits']!=LIMITS:raise WorldError('campaign_rebalance_requires_original_closed_ledger')
        if any(sum(a['role']==r for a in value['attempts'])>cap for r,cap in CLOSEOUT_LIMITS.items()):raise WorldError('campaign_rebalance_existing_charge_exceeds_bound')
        value.setdefault('rebalances',[]).append({'atUnix':time.time(),'priorAttempts':len(value['attempts']),'from':LIMITS,'to':CLOSEOUT_LIMITS,'reason':'VERTICAL-SLICE-01 live Strategy closeout; user total30 takes precedence over recommended role sub-bounds; no reset or model change'})
        value['roleLimits']=CLOSEOUT_LIMITS;self.write(value)

    def reallocate_remaining_to_tactics(self):
        """Freeze unused Strategy/preparation slots; aggregate remains thirty."""
        value=self.read()
        if not value['closed'] or value['roleLimits']!=CLOSEOUT_LIMITS:raise WorldError('campaign_tactical_reallocation_requires_closed_closeout')
        if any(sum(a['role']==r for a in value['attempts'])>cap for r,cap in TACTICAL_LIMITS.items()):raise WorldError('campaign_tactical_reallocation_exceeds_existing_charge')
        value.setdefault('rebalances',[]).append({'atUnix':time.time(),'priorAttempts':len(value['attempts']),'from':CLOSEOUT_LIMITS,'to':TACTICAL_LIMITS,'reason':'live memo already frozen and Brock has one authored candidate; reallocate unused Strategy/preparation slots to meaningful legal tactics, unchanged aggregate30'})
        value['roleLimits']=TACTICAL_LIMITS;self.write(value)

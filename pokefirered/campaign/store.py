"""Compose existing persistence services; no alternative projections or schemas."""
from virality.battle_store import ViralityBattleStore
from .context import ScoutingContextMixin
from battle.lifecycle import LifecycleMixin

class CampaignStore(ScoutingContextMixin,LifecycleMixin,ViralityBattleStore):
    def __init__(self,path,manifest):
        super().__init__(path,manifest)
        from pathlib import Path
        from world.store import ROOT
        from roster.extract import file_hash
        native=(ROOT/self.native_manifest['rom_path']).parent
        accepted=ROOT/'.local/battle01-native-v3'
        qualified=self.native_manifest.get('qualified_trainers')
        if self.native_manifest.get('campaign_profile') in ('data-driven-authored-singles-v1','data-driven-rocket-singles-v1','data-driven-scripted-singles-v1'):
            from content.campaign import CampaignContent
            content=CampaignContent.load()
            if self.native_manifest['campaign_profile'] in ('data-driven-rocket-singles-v1','data-driven-scripted-singles-v1'):
                from content.rocket import RocketContent
                content=RocketContent.load()
                if self.native_manifest.get('rocket_content_sha256')!=file_hash(ROOT/'config/rocket_content.json'):self.close();raise ValueError('unqualified Rocket native content')
            if self.native_manifest['campaign_profile']=='data-driven-scripted-singles-v1':
                from content.scripted import ScriptedContent
                content=ScriptedContent.load()
                if self.native_manifest.get('scripted_content_sha256')!=file_hash(ROOT/'config/scripted_encounters.json'):self.close();raise ValueError('unqualified scripted native content')
            expected=sorted([102,414]+[n for p in content.extension['participation'].values() for n in p.get('qualifiedSourceIDs',[p['sourceTrainer']])])
            if qualified!=expected or self.native_manifest.get('campaign_content_sha256')!=file_hash(ROOT/'config/campaign_content.json'):self.close();raise ValueError('unqualified campaign native content')
        elif qualified!=[102,414]:self.close();raise ValueError('unqualified campaign native profile')
        if '#define PI_CAMPAIGN_BROCK 1' not in (native/'include/pi_build.h').read_text():self.close();raise ValueError('unqualified campaign native profile')
        script='data/maps/PewterCity_Gym/scripts.inc'
        if file_hash(native/script)!=file_hash(accepted/script):self.close();raise ValueError('native Gym script changed')
        if (native/'src/battle_main.c').read_text().replace('    PiBattle_PartyConstructed(trainerNum);\n','')!=(accepted/'src/battle_main.c').read_text():self.close();raise ValueError('native party constructor changed')
    def observe_native_preparation(self,state):
        actor='trainer:fr:trainer:%04d'%state['trainerID']
        lock=self.locked_preparation(actor)
        if state['trainerID']!=414 or not lock:return
        if lock['encounterID'] in self.decision_state()['installations']:return
        counts=getattr(self,'native_constructions',{})
        count=counts.get((state['nonce'],state['generation']))
        if count!=1:raise ValueError('missing exact first Brock native constructor receipt')
        party=[{'species':p['species'],'level':p['level'],'moves':p['moves'],'heldItem':p['heldItem']} for p in state['own']]
        receipt={'nonce':state['nonce'],'generation':state['generation'],'commitmentDigest':lock['commitmentID'].split(':')[1],'nativeROM':self.compatibility['nativeROM'],'party':party,'nativeConstructorCount':count,'source':'native authored CreateNPCTrainerParty observation','battle':state['battle']}
        self.record_installation(lock['encounterID'],receipt)

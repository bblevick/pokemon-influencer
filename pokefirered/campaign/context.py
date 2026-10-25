"""Explicit adoption of attributed social evidence; old memo identities unchanged."""
import copy,json
from world.store import ROOT,WorldError,dump
from roster.extract import digest
from strategy.memo import memo_context,memo_configuration
from strategy.social_context import build_social_evidence

BROCK='trainer:fr:trainer:0414'
PROMPT=ROOT/'prompts/strategy_scouting_v3.txt'

def scouting_context(store,actor,stage='first',purpose='preparation',provider_binding=None):
    packet=memo_context(store,actor,stage,purpose,provider_binding)
    social=build_social_evidence(store,actor)
    # The durable receipt cutoffs are host scope, never model knowledge or tools.
    view={k:copy.deepcopy(social[k]) for k in ('schemaVersion','actorID','authorizedFacts','unknowns','truncated')}
    packet['modelInput']['authorizedSocialEvidence']=view
    packet['modelInput']['opponentCurrentLead']='UNKNOWN'
    configuration=json.loads((ROOT/'config/vertical_slice01.json').read_text())
    packet['modelInput']['campaignBehavior']=configuration['brockBehavior']
    version=digest([memo_configuration(),PROMPT.read_text(),configuration,'scouting-context-v3'])
    packet['scope'].update(configurationSHA256=version,promptVersion=3,socialContextVersion=3)
    packet['materialContextSHA256']=digest([packet['modelInput'],packet['scope']['opportunityID'],purpose,version,packet['scope']['providerConfiguration']])
    packet.pop('contextID');packet['contextID']='strategy-context:'+digest(packet)
    if len(dump(packet['modelInput']).encode('utf-8'))>24576:raise WorldError('scouting_strategy_input_bound')
    return packet

class ScoutingContextMixin:
    def battle_behavior(self,lock):
        # Read the exact stored Strategy grant, never mutable current content.
        memo=next((m for m in self.memo_records() if m['strategyID']==lock['strategyID']),None)
        if memo is None:raise WorldError('locked_strategy_missing')
        row=self._one('SELECT context FROM strategy_jobs WHERE id=?',(memo['jobID'],))
        packet=json.loads(row['context'])
        if packet['scope']['actor']!=lock['actor']:raise WorldError('locked_strategy_actor')
        behavior=copy.deepcopy(packet['modelInput'].get('campaignBehavior',{}))
        if len(dump(behavior).encode('utf-8'))>2048:raise WorldError('battle_behavior_bound')
        return behavior
    def context_packet(self,actor,stage='forest-post-boulder-1',purpose='preparation',provider_binding=None):
        if actor==BROCK and stage=='first':return scouting_context(self,actor,stage,purpose,provider_binding)
        return super().context_packet(actor,stage,purpose,provider_binding)
    def prebattle_facts(self,actor):
        # Frozen with commitment. Later public posts cannot enter this encounter.
        social=build_social_evidence(self,actor)
        packet={k:copy.deepcopy(social[k]) for k in ('schemaVersion','actorID','authorizedFacts','unknowns','truncated')}
        if len(dump(packet).encode('utf-8'))>8192:raise WorldError('prebattle_authorized_facts_bound')
        return packet

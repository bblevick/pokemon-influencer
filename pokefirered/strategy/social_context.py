"""Additive authorized social input for future StrategyContext v3.

Does not change v2 hashes, accepted memos or preparation locks. No inference.
The existing model adapter must explicitly adopt a new prompt/context version
before consuming this packet in a later separately authorized experiment.
"""
import json
import jsonschema
from world.store import ROOT, WorldError, dump


def build_social_evidence(store,actor):
    if not getattr(store,'_supports_virality',False):raise WorldError('versioned virality writer required')
    context=store.evidence_context(actor)
    quality_schema=json.loads((ROOT/'schemas/social/evidence_quality.schema.json').read_text())
    for r in context['authorizedEvidence']:jsonschema.validate(r['evidenceQuality'],quality_schema)
    packet={'schemaVersion':3,'actorID':actor,'scope':context['scope'],
            'authorizedFacts':[{'claim':r['claim'],'evidenceID':r['memoryID'],
                                'mode':r['mode'],'attribution':r['source'],
                                'evidenceQuality':r['evidenceQuality']}
                               for r in context['authorizedEvidence']],
            'unknowns':context['unknowns'],'truncated':context['truncated'],
            'strategyMemoSubjective':None,'strategicInterpretation':None}

    # Drop only the ranked projection tail; durable actor records stay intact.
    while len(dump(packet).encode('utf-8')) > 24576 and packet['authorizedFacts']:
        packet['authorizedFacts'].pop();packet['truncated']=True
    if len(dump(packet).encode('utf-8')) > 24576:raise WorldError('social StrategyContext byte bound')
    return packet

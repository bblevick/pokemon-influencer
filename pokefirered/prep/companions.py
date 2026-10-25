"""Source-authored companion identity constructor; no campaign development."""
from roster.domain import Companion

def authored_companions(catalog,actor,variant):
    return tuple(Companion(f'{actor}:baseline:{variant}:{p["slot"]}',actor,p['baselineKey'],'baseline',p['level'],p['species'],p['level'],tuple(p['moves']),held_item=p['heldItem']) for p in catalog.own_baseline(actor,variant)['party'])

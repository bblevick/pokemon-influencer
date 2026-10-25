"""Lifecycle contract. Commitment/consumption writers are deferred to SYSTEM1 A.

Pure fixtures can exercise future transitions without choosing/debiting a team.
Rewind revokes active capabilities and never edits the immutable earned receipt.
"""
from enum import Enum
class OpportunityStatus(str,Enum):
    UNAVAILABLE='unavailable'
    EARNED='earned'
    AVAILABLE='available'
    RESERVED='reserved'
    COMMITTED='committed'
    CONSUMED='consumed'
    INVALIDATED='invalidated'
    REWOUND='rewound'

TRANSITIONS={
    'earned':('unavailable','earned'), 'available':('earned','available'),
    'reserve':('available','reserved'), 'release':('reserved','available'),
    'commit':('reserved','committed'), 'consume':('committed','consumed')}
def transition(status,event):
    status=OpportunityStatus(status)
    if event in ('invalidate','rewind'):
        return OpportunityStatus.INVALIDATED if event=='invalidate' else OpportunityStatus.REWOUND
    before,after=TRANSITIONS[event]
    if status.value!=before:raise ValueError('invalid preparation opportunity transition')
    return OpportunityStatus(after)
def enumerable(status):return OpportunityStatus(status)==OpportunityStatus.AVAILABLE

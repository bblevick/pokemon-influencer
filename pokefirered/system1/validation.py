"""Shared fixed-choice response validation; no world or preparation imports."""
import math
def validate_decision(value,choices):
    if not isinstance(value,dict) or set(value)-{'choiceID','probabilities','confidence','diagnostics'}:raise ValueError('decision_shape')
    if value.get('choiceID') not in choices:raise ValueError('unknown_choice')
    probs=value.get('probabilities')
    if probs is not None:
        if not isinstance(probs,dict) or set(probs)!=set(choices):raise ValueError('probability_coverage')
        if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in probs.values()) or abs(sum(probs.values())-1)>1e-5:raise ValueError('invalid_distribution')
    conf=value.get('confidence')
    if conf is not None and (type(conf) not in (int,float) or not math.isfinite(conf) or not 0<=conf<=1):raise ValueError('confidence_bound')
    return value


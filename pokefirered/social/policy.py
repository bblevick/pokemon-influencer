"""Policy chooses allowed evidence; services retain all execution authority."""
VERSION = 1
TEMPLATE = 1


def propose(opportunity):
    results = [r for r in opportunity['evidence'] if r['claim']['type'] == 'TRAINER_BATTLE_RESULT' and r['claim']['nativeOutcome'] == 1]
    seen = [r for r in opportunity['evidence'] if r['claim']['type'] == 'POKEMON_SEEN']
    if not results:
        return None
    selected = [results[0]] + seen[:1]
    return {'battleID': opportunity['battleID'], 'evidenceIDs': [r['memoryID'] for r in selected], 'visibility': 'public', 'policyVersion': VERSION}


def render(claims, names):
    # No user/model supplied prose or author interpolation. All body facts come
    # solely from the validated small claim set.
    parts = []
    for claim in claims:
        if claim['type'] == 'TRAINER_BATTLE_RESULT' and claim['nativeOutcome'] in (1,2,3):
            parts.append({1:'I lost to the player.',2:'I won against the player.',3:'Our battle ended in a draw.'}[claim['nativeOutcome']])
        elif claim['type'] == 'POKEMON_SEEN':
            name = names.get(str(claim['speciesID']))
            if not name or len(name) > 12 or any(ord(c) < 32 for c in name):
                raise ValueError('unsupported species display name')
            parts.append('I saw ' + name + '.')
        else:
            raise ValueError('unsupported published claim')
    body = ' '.join(parts)
    if not 1 <= len(body.encode()) <= 160:
        raise ValueError('post body bounds')
    return body

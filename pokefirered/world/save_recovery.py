"""Classify callbacks before strict save finalization; never infer a checkpoint."""
def receipt_disposition(intent, receipt):
    if not intent:
        return 'no_intent'
    if (receipt.get('nonce'), receipt.get('run')) != (intent['nonce'], intent['run']):
        return 'unrelated_run'
    if receipt.get('event') != 'savedataUpdated':
        return 'invalid_callback'
    # A replay of the old battery callback cannot complete the new save intent.
    # Counter rollover is explicit; do not compare counters by magnitude.
    if receipt.get('counter') == intent['old_counter']:
        return 'historical_callback'
    if receipt.get('counter') != (intent['old_counter'] + 1) & 0xffffffff:
        return 'unexpected_counter'
    return 'candidate_requires_full_validation'

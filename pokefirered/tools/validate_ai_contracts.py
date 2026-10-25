#!/usr/bin/env python3
"""Offline static design checks only; no provider, .env, ROM or emulator access."""
import copy
import json
from pathlib import Path
from importlib.metadata import version
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
checks = []
def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)

def load(path):
    return json.loads((ROOT / path).read_text())

schemas = {p.stem.split('.')[0]: json.loads(p.read_text()) for p in (ROOT / 'schemas/ai').glob('*.schema.json')}
registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas.values())
validators = {}
for name, schema in schemas.items():
    Draft202012Validator.check_schema(schema)
    check(name + ' schema definition', True)
    validators[name] = Draft202012Validator(schema, registry=registry)
examples = {name: load('schemas/ai/examples/' + name + '.json') for name in schemas}
for name, example in examples.items():
    check(name + ' fictional positive fixture', validators[name].is_valid(example))

def reject(name, schema, value):
    check(name, not validators[schema].is_valid(value))

bad = copy.deepcopy(examples['battle_request']); bad['visibleState']['opponentActive']['privateParty'] = []
reject('hidden party field rejected', 'battle_request', bad)
bad = copy.deepcopy(examples['battle_request']); bad['schemaVersion'] = 2
reject('unknown request version rejected', 'battle_request', bad)
bad = copy.deepcopy(examples['battle_request']); bad['legalActions'] = []
reject('empty legal list rejected', 'battle_request', bad)
bad = copy.deepcopy(examples['battle_request']); bad['recentHistory'] = [{}] * 33
reject('history bounded', 'battle_request', bad)
bad = copy.deepcopy(examples['battle_request']); del bad['legalActions'][0]['moveID']
reject('move requires move ID', 'battle_request', bad)
bad = copy.deepcopy(examples['strategic_posture']); bad['aggression'] = 2
reject('posture bounded', 'strategic_posture', bad)
bad = copy.deepcopy(examples['strategic_posture']); bad['grantPokemon'] = 1
reject('posture cannot grant resources', 'strategic_posture', bad)
bad = copy.deepcopy(examples['battle_result']); bad['fallbackUsed'] = True
reject('success cannot conceal fallback', 'battle_result', bad)
bad = copy.deepcopy(examples['battle_result']); bad['probabilities']['action.fixture.1'] = 1.5
reject('probability bounded', 'battle_result', bad)
bad = copy.deepcopy(examples['battle_result']); bad.update(status='fallback', errorCode='timeout', fallbackUsed=True, provider='deterministic', model='heuristic-v1')
check('explicit timeout fallback fixture', validators['battle_result'].is_valid(bad))
for model in ['inception/mercury-decide:free', 'typesafe/jev-1.13', '~typesafe/jev-latest']:
    value = copy.deepcopy(examples['battle_result']); value['model'] = model
    check('model identifier representable: ' + model, validators['battle_result'].is_valid(value))

# Illustrative fixture assertions only; these are not the future authoritative
# domain validator or evidence that gameplay permissions have been enforced.
request = examples['battle_request']; result = examples['battle_result']
def fixture_membership(q, z):
    legal = {a['legalActionID'] for a in q['legalActions']}
    return (z['requestID'] == q['requestID'] and z['selectedLegalActionID'] in legal
            and all(set(z.get(k, {})) <= legal for k in ('probabilities', 'scores')))
check('fictional fixture correlation/membership', fixture_membership(request, result))
bad = copy.deepcopy(result); bad['selectedLegalActionID'] = 'invented'
check('illustrative illegal ID rejection', not fixture_membership(request, bad))
bad = copy.deepcopy(result); bad['requestID'] = 'stale'
check('illustrative stale request rejection', not fixture_membership(request, bad))

config = load('config/model_profiles.yaml') # JSON is a valid YAML subset.
check('offline default and hosted disabled', config['default_profile'] == 'offline' and config['hosted_inference_enabled'] is False)
check('credential is environment reference', config['credentials_env'] == 'OPENROUTER_KEY')
check('zero cost and no substitution', config['policy'] == {'free_only': True, 'max_cost_usd': 0, 'allow_paid_fallback': False, 'allow_model_substitution': False, 'require_current_zero_pricing': True, 'fail_closed_on_unknown_pricing': True})
expected = {'puppeteer': ('POKEINFLUENCER_PUPPETEER_MODEL','thinkingmachines/inkling:free','openrouter_chat'), 'strategy': ('POKEINFLUENCER_STRATEGY_MODEL','nvidia/nemotron-3.5-lightning:free','openrouter_chat'), 'system1': ('POKEINFLUENCER_SYSTEM1_MODEL','inception/mercury-decide:free','openrouter_systemone')}
for profile in ['development', 'experimental']:
    roles = config['profiles'][profile]['roles']
    check(profile + ' has exactly three roles', set(roles) == set(expected))
    for role, (env, model, provider) in expected.items():
        check(profile + ' ' + role + ' independent free selection', (roles[role]['model_env'],roles[role]['default_model'],roles[role]['provider']) == (env,model,provider))
check('development blocked pending pins', config['profiles']['development']['network_allowed_when_explicitly_enabled'] is False)
check('experimental is explicit alias profile', config['profiles']['experimental']['network_allowed_when_explicitly_enabled'] is True)
check('offline no network', config['profiles']['offline']['network_allowed_when_explicitly_enabled'] is False)
check('paid/floating Jev references disabled', config['regression_reference']['enabled'] is False and config['experimental_reference']['enabled'] is False)
catalog = load('evidence/architecture/model-catalog.json')
endpoints = load('evidence/architecture/decision-endpoints.json')
for role, (_, model, _) in expected.items():
    entry = next(m for m in catalog['models'] if m['requested_id'] == model)
    prices = [entry['pricing']] if entry['listed'] else [e['pricing'] for r in endpoints if r['model']==model for e in r['data']['data']['endpoints']]
    check(role + ' discovery snapshot zero token prices', bool(prices) and all(float(p['prompt'])==float(p['completion'])==0 for p in prices))
for folder in ['puppeteer', 'strategy', 'pokebook']:
    check(folder + ' prompt reservation exists', (ROOT / 'prompts' / folder / 'README.md').is_file())
report = {'scope': 'offline schemas/config and fictional fixtures only; no AI implementation or inference/emulator execution', 'command': '.venv/bin/python tools/validate_ai_contracts.py', 'jsonschema_version': version('jsonschema'), 'checks': checks, 'count': len(checks), 'passed': all(c['passed'] for c in checks), 'inference_calls': 0}
(ROOT / 'evidence/architecture/static-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(f"{len(checks)} static checks passed; no inference or emulator execution")

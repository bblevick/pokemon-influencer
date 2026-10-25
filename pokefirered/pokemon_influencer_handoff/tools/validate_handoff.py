#!/usr/bin/env python3
"""Validate this handoff package, NOT a game, ROM, emulator, or battle engine.

Run from any working directory. Requires the pinned jsonschema dependency in
requirements-handoff.txt. Writes evidence/handoff_validation.json.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    sys.exit('Missing dependency. Run: python -m pip install -r requirements-handoff.txt')

ROOT = Path(__file__).resolve().parents[1]
AGENT_FILE = ROOT.parent / 'AGENTS.md'
CHECKS: list[dict[str, Any]] = []

def check(name: str, condition: bool, detail: str = '') -> None:
    CHECKS.append({'check': name, 'passed': bool(condition), 'detail': detail})

def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def main() -> int:
    required = [
        'README.md', 'PLAN.md', 'agent.md', 'CODEX_START_HERE.md',
        'end_game_concept.md', 'docs/architecture.md', 'docs/memory_and_pokebook.md',
        'docs/roster_adaptation.md', 'docs/bridge_and_saves.md', 'docs/test_plan.md',
        'docs/backlog.md', 'docs/decision_log.md', 'docs/source_notes.md',
        'config/campaign_defaults.json', 'contracts/domain.schema.json',
        'prompts/puppeteer.md', 'prompts/npc_planner.md', 'prompts/social_writer.md',
        'requirements-handoff.txt', 'examples/README.md',
    ]
    check('required_files_exist', all((ROOT / p).is_file() for p in required))
    check('canonical_agent_file_exists_at_repository_root', AGENT_FILE.is_file())
    check('canonical_agent_file_under_32_kib', AGENT_FILE.is_file() and AGENT_FILE.stat().st_size < 32768)
    check('lowercase_agent_points_to_canonical', 'AGENTS.md' in (ROOT / 'agent.md').read_text())

    schema = load('contracts/domain.schema.json')
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        check('json_schema_is_well_formed', True)
    except jsonschema.SchemaError as exc:
        check('json_schema_is_well_formed', False, str(exc)[:500])
    validator = jsonschema.Draft202012Validator(schema)
    records: dict[str, Any] = {}
    for p in sorted((ROOT / 'examples').glob('*.json')):
        data = json.loads(p.read_text(encoding='utf-8'))
        records[p.stem] = data
        errors = list(validator.iter_errors(data))
        check('schema_example:' + p.name, not errors,
              '; '.join(e.message for e in errors)[:500])

    cfg = load('config/campaign_defaults.json')
    check('campaign_only_endgame_disabled', cfg['content_phase'] == 'campaign' and not cfg['endgame_enabled'])
    check('ordinary_trainers_follow_once', cfg['followers']['ordinary_first_win_policy'] == 'follow_once')
    check('friendship_not_identical_to_follow', cfg['followers']['friendship_is_separate'])
    check('cloud_model_disabled_by_default', not cfg['models']['enabled_by_default'])
    check('loss_streak_growth_disabled', not cfg['adaptation']['loss_streak_growth_enabled'])
    check('iv_nature_rerolls_disabled', not cfg['adaptation']['iv_nature_rerolls_enabled'])
    check('off_region_weights_disabled_without_grant',
          cfg['adaptation']['tier_weights']['accessible'] == 0 and
          cfg['adaptation']['tier_weights']['exceptional'] == 0 and
          cfg['adaptation']['off_region_requires_explicit_acquisition_grant'])
    check('capture_tier_weights_sum_to_one', abs(sum(cfg['adaptation']['tier_weights'].values()) - 1) < 1e-9)
    check('candidate_score_weights_sum_to_one', abs(sum(cfg['adaptation']['candidate_score_weights'].values()) - 1) < 1e-9)
    check('structural_budgets_do_not_accumulate', not cfg['adaptation']['structural_budgets_accumulate'])
    check('original_defeated_flag_preserved', cfg['rematches']['preserve_original_defeated_flag'])
    check('retry_plan_is_fixed', cfg['rematches']['loss_retry_uses_same_plan'])
    check('no_unpaired_rewind_claim', not cfg['saves']['rewind_supported_initially'] and not cfg['saves']['arbitrary_unpaired_savestates_supported'])

    events = {r['event_id']: r for r in records.values() if r['record_type'] == 'event'}
    profile = records['npc_profile']
    plan = records['roster_plan']
    memory = records['memory_record']
    observation = records['battle_observation']
    post = records['social_post']
    delivery = records['delivery']
    scoped_records = [r for r in records.values() if 'save_id' in r]
    check('examples_share_one_save_and_branch', len({(r['save_id'], r['branch_id']) for r in scoped_records}) == 1)
    check('example_event_sequences_are_unique', len({r['event_seq'] for r in events.values()}) == len(events))
    check('illustrative_profile_is_not_claimed_as_vanilla_binding', profile['binding'] == {'status': 'illustrative_unbound', 'rom_trainer_symbol': None})

    for label, data, field in [('memory', memory, 'source_event_ids'), ('plan', plan, 'evidence_ids'), ('post', post, 'source_event_ids')]:
        check(label + '_source_event_references_exist', all(i in events for i in data[field]))
    check('plan_evidence_precedes_cutoff', all(events[i]['event_seq'] <= plan['evidence_cutoff_seq'] for i in plan['evidence_ids']))
    check('memory_evidence_precedes_cutoff', all(events[i]['event_seq'] <= memory['knowledge_cutoff_seq'] for i in memory['source_event_ids']))
    check('plan_committed_after_evidence_cutoff', plan['prepared_at_seq'] > plan['evidence_cutoff_seq'])
    training = records['event_training_committed']
    check('training_event_matches_committed_plan', training['payload']['plan_id'] == plan['plan_id'] and training['event_seq'] == plan['prepared_at_seq'])
    check('post_follows_training_commit', post['published_at_seq'] > training['event_seq'])
    check('delivery_follows_publication', delivery['delivered_at_seq'] >= post['published_at_seq'] and delivery['post_id'] == post['post_id'])
    check('delivery_preserves_origin', delivery['origin_event_ids'] == post['origin_event_ids'])
    check('post_fits_configured_character_limit', len(post['body']) <= cfg['social']['post_body_max_characters'])
    check('example_has_no_accidental_rumor', post['claim_status'] == 'verified_fact')

    old = {m['lineage_id']: m for m in profile['baseline_party']}
    new = {m['lineage_id']: m for m in plan['party']}
    check('reference_original_lineages_retained', set(old) <= set(new))
    check('reference_signature_retained', profile['signature_lineage_id'] in new and plan['signature_lineage_id'] == profile['signature_lineage_id'])
    check('reference_first_epoch_has_no_catch', plan['epoch_index'] == 1 and not plan['changes']['new_acquisition_ids'])
    edits = sum(sum(a != b for a, b in zip(old[k]['moves'] + [None] * (4 - len(old[k]['moves'])), new[k]['moves'] + [None] * (4 - len(new[k]['moves'])))) for k in old)
    check('reference_move_edit_count_matches_record', edits == plan['changes']['move_slot_edits'])
    check('reference_move_edits_fit_budget', edits <= cfg['adaptation']['max_move_slot_changes_per_opportunity'])
    check('reference_level_growth_fits_one_epoch', all(0 <= new[k]['level'] - old[k]['level'] <= cfg['adaptation']['max_level_gain_per_earned_epoch_per_pokemon'] for k in old))
    check('reference_levels_fit_boulder_cap', all(m['level'] <= cfg['proposed_badge_stage_caps']['boulder'] for m in new.values()))
    check('battle_reference_uses_committed_party', observation['plan_id'] == plan['plan_id'] and observation['own_party'] == plan['party'])
    check('battle_reference_memory_exists', observation['known_memory_ids'] == [memory['memory_id']])
    valid_action_refs = all(
        (a['kind'] == 'move' and a['slot'] < len(observation['own_party'][observation['own_active_party_slot']]['moves'])) or
        (a['kind'] == 'switch' and a['slot'] < len(observation['own_party']) and a['slot'] != observation['own_active_party_slot'])
        for a in observation['legal_actions'])
    check('reference_action_slots_exist', valid_action_refs,
          'Checks slot references only; not a production battle legality engine.')

    # Negative schema checks are structural only, not emulator/game behavior.
    bad = copy.deepcopy(observation); bad['hidden_player_party'] = ['SPECIES_BLASTOISE']
    check('schema_rejects_hidden_party_field', not validator.is_valid(bad))
    bad = copy.deepcopy(memory); bad['confidence'] = 1.5
    check('schema_rejects_out_of_range_confidence', not validator.is_valid(bad))
    bad = copy.deepcopy(plan); bad['party'] = [copy.deepcopy(plan['party'][0]) for _ in range(7)]
    check('schema_rejects_oversized_party', not validator.is_valid(bad))
    bad = copy.deepcopy(plan); bad['party'][0]['level'] = 101
    check('schema_rejects_level_over_100', not validator.is_valid(bad))
    bad = copy.deepcopy(post); bad['body'] = 'x' * 97
    check('schema_rejects_oversized_post', not validator.is_valid(bad))
    bad = copy.deepcopy(records['event_badge_awarded']); bad['payload'] = {'pokemon': 'SPECIES_BLASTOISE'}
    check('schema_rejects_wrong_event_payload_shape', not validator.is_valid(bad))

    broken_links = []
    for p in ROOT.rglob('*.md'):
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            local = target.split('#', 1)[0]
            if local and not (p.parent / local).exists():
                broken_links.append(str(p.relative_to(ROOT)) + ':' + target)
    check('markdown_local_links_resolve', not broken_links, '; '.join(broken_links))
    nav_missing = []
    for target in re.findall(r'^\| `([^`]+)` \|', (ROOT / 'README.md').read_text(), re.MULTILINE):
        if target == 'AGENTS.md':
            target = '../AGENTS.md'
        if target == 'evidence/handoff_validation.json':
            continue  # This report is written by the current run.
        if not (ROOT / target).exists():
            nav_missing.append(target)
    check('readme_document_map_targets_exist', not nav_missing, '; '.join(nav_missing))

    report = {
        'scope': 'handoff_package_only',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'examples_validated': len(records),
        'checks_passed': sum(c['passed'] for c in CHECKS),
        'checks_failed': sum(not c['passed'] for c in CHECKS),
        'rom_modified': False, 'rom_built': False, 'emulator_tests_run': False,
        'gameplay_tested': False,
        'limitations': [
            'No game source, ROM, emulator integration, full legality catalog, or model inference was executed.',
            'Structural schema checks and illustrative fixture invariants are not production gameplay tests.',
            'Example NPC binding is intentionally unverified and must be resolved in implementation.',
        ],
        'checks': CHECKS,
    }
    outpath = ROOT / 'evidence/handoff_validation.json'
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['scope', 'examples_validated', 'checks_passed', 'checks_failed', 'rom_built', 'emulator_tests_run']}, indent=2))
    for c in CHECKS:
        if not c['passed']:
            print('FAILED: ' + c['check'] + ' ' + c['detail'], file=sys.stderr)
    return 1 if report['checks_failed'] else 0

if __name__ == '__main__':
    raise SystemExit(main())

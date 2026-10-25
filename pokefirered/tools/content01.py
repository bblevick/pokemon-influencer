#!/usr/bin/env python3
"""Validate the existing production pack and report pure hypothetical resolutions.

No catalog extraction, emulator access, SQLite connection or activation writer.
"""
from __future__ import annotations
import json
import sys
import subprocess
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content.policy import OpeningContent, TrustedState, ProgressionEvidence
from roster.domain import Scope, Context, Step
from roster.fixtures import baseline
from roster.extract import digest,file_hash
from jsonschema import Draft202012Validator
# v1 closeout evidence remains immutable; this authorization writes an addendum.
E=ROOT/'evidence/phase3/content01/addendum'

def scenario(content,number,stage):
    actor=f'trainer:fr:trainer:{number:04d}'
    scope=Scope('content01-scenario','opening-branch',actor,0,20)
    ctx=Context(scope,baseline(content.cat,actor,number),frozenset(),(),(),(),frozenset(),0,0,None,True)
    boulder=stage!='first' or number==116
    e=ProgressionEvidence(scope,content.pack['romSHA256'],content.pack['sourceCommit'],
        (('FLAG_DEFEATED_BROCK',boulder),('FLAG_BADGE01_GET',boulder)),
        ('scenario:native-flag-snapshot',),'scenario:paired-checkpoint','scenario:content-activation')
    return TrustedState(ctx,e,frozenset([actor]) if stage!='first' else frozenset(),frozenset(),True)

def reports(content):
    schema=json.loads((ROOT/'schemas/content/resolved.schema.json').read_text())
    rows=[]
    for actor,t in content.pack['trainers'].items():
        for stage in t['stages']:
            state=scenario(content,t['sourceTrainer'],stage)
            packet=content.resolve(state,stage)
            Draft202012Validator(schema).validate(packet)
            if packet['status']!='permitted':raise ValueError('incomplete production binding')
            c=state.context.companions[0]
            view=content.roster_view(state,stage,c.lineage)
            retained=view.move(c.lineage,next(m for m in c.moves if m)).packet()
            denied=view.growth(c.lineage,packet['levels'][c.lineage]['maximum']+1).packet()
            development=None
            if stage!='first':
                if t['sourceTrainer']==102:
                    c=state.context.companions[1]
                    path=[Step('level',10,7),Step('evolution',11,7),Step('level',11,10),Step('evolution',12,10),Step('level_move',12,10,93,2)]
                else:
                    c=state.context.companions[1]
                    path=[Step('level',14,10),Step('evolution',15,10),Step('level_move',15,10,31,1)]
                development={'label':'hypothetical partial path, not a selected team','lineage':c.lineage,
                             'steps':[s.__dict__ for s in path], 'result':content.development(state,stage,{c.lineage:path})}
                if development['result']['status']!='permitted':raise ValueError('forest path not feasible')
            rows.append({'trainer':t['displayName'],'sourceTrainer':t['sourceTrainer'],'stage':stage,
                         'scenario':True,'trustedInput':{'scope':state.context.scope.__dict__,'flags':dict(state.progression.flags),
                          'defeatedActors':sorted(state.defeated_actors),'inventory':[], 'consumedOpportunities':[]},
                         'policy':packet,'permittedElement':retained,'deniedElement':denied,
                         'developmentExample':development})
    return {'schemaVersion':1,'classification':'pure hypothetical trusted-state scenarios over actual production pack',
            'packSHA256':content.hash,'catalogSHA256':content.cat.hash,'rows':rows,
            'liveProgressionVerified':False,'teamsSelected':0,'inventoryInitialized':False}

def balance(report,content):
    lines=['# CONTENT-01 opening balance sheet','',
           'Authored playtest values, not proven difficulty balance. These six resolutions use the production pack with hypothetical trusted snapshots; no live grants or teams were created.','',
           '| Trainer / stage | Original species IDs @ levels | Targets / ceiling | Eligibility | Retention / signature |',
           '| --- | --- | --- | --- | --- |']
    for row in report['rows']:
        t=content.pack['trainers'][row['policy']['scope']['actor']]
        originals=', '.join(f"{p['species']}@{p['level']} ({content.cat.lookup('species',p['species'])['symbols'][0]})" for p in t['originals'])
        targets=', '.join(str(x['target']) for x in row['policy']['levels'].values())
        lines.append(f"| {row['trainer']} / {row['stage']} | {originals} | {targets} / {t['stages'][row['stage']]['stageCeiling']} | {t['stages'][row['stage']]['predicate']} | All originals; signature {','.join(t['signatureOrigins']) or 'none authored'} |")
    lines += ['', 'Every row: two aggregate elective move-slot changes, including evolution learning; zero catches/additions/reserves/replacements; all battle/held/teaching/evolution/capture/tutor/exceptional stocks or entitlements zero; no extra healing or restock. Growth is zero on first encounters and at most four levels once on the named forest opportunity. Existing higher levels are retained on forest preparation, never lowered. Source custom moves remain individual retention facts.', '',
              'Rick/Doug: Forest native, Route2 explicitly nearby with actor-bound travel.forest.route2 evidence; land only. Nearby access is not granted by habitat or player visits, and even valid travel does not overcome zero catches. Janice: Route3 native, no nearby maps; Brock: Pewter Gym home, no catch habitat or nearby maps. Accessible/exceptional maps are empty. Surf/fishing/Rock Smash and gift/trade/fossil routes have no opening authorization.', '',
              'Brock: Rock theme, Onix signature and Geodude thematic core, minimum two core companions, maximum two active, zero mixed support, support species/acquisition lists empty, support ceiling14. This opening bound does not forbid future approved mixed-type Gym content. No unowned support or extra item is permitted.', '',
              'Permitted in every row: retain a verified original move and reorder the original party. Denied: growth above that individual target (or any first-encounter growth), teaching from an unowned TM, free relearning, new capture, third Brock companion. With zero teaching stock and first growth, first-encounter move alternatives can collapse to retained moves; no forced diversity or grant is invented.', '',
              'Post-Boulder Rick feasibility: Caterpie6 → Metapod7 → Butterfree10, optionally learn Confusion10 in one slot. Post-Boulder Doug feasibility: his original Kakuna7 → Beedrill10, optionally learn Fury Attack10 in one slot. These are source-supported partial alternatives, not selected preparations; both leave other legal growth/order/retention choices open. Rick Stun Spore14, Sleep Powder15 and Gust28 remain above his opening target10.', '',
              'Machine-readable exact policies, positive/negative ROSTER element proofs and development paths: evidence/phase3/content01/resolved-content.json. PREP must supply trusted active state, generate complete alternatives and validate the aggregate envelope before any selection.']
    lines += ['', 'CONTENT-01 addendum: these zero acquisition values are opening overrides only. Shared configurable mechanics and inactive later balance decisions are documented in content01_addendum.md. No later production content or origin sampler is activated.']
    return '\n'.join(lines)+'\n'

def run():
    E.mkdir(parents=True,exist_ok=True)
    content=OpeningContent.load()
    report=reports(content)
    (E/'resolved-content.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'docs/content01_balance.md').write_text(balance(report,content))
    before=json.loads((E/'protected-before.json').read_text())
    after={p:file_hash(ROOT/p) for p in before}
    if before!=after:raise ValueError('protected foundation files changed')
    overlay=json.loads((ROOT/'evidence/phase2/pokebook01/manifest-enabled.json').read_text())['overlay_sha256']
    if any(after[p]!=sha for p,sha in overlay.items()):raise ValueError('accepted source overlay changed')
    if after['.local/pokebook01-enabled/pokefirered.gba']!=content.pack['romSHA256']:raise ValueError('ROM changed')
    source=[]
    for path,current in content.pack['sourceEvidence'].items():
        pinned=subprocess.run(['git','show',content.pack['sourceCommit']+':'+path],cwd=ROOT,check=True,capture_output=True).stdout
        import hashlib
        pinned_sha=hashlib.sha256(pinned).hexdigest()
        if pinned_sha!=current:raise ValueError('progression binding differs from pinned source')
        source.append({'path':path,'currentSHA256':current,'pinnedSHA256':pinned_sha})
    profiles=json.loads((ROOT/'config/model_profiles.yaml').read_text())
    if profiles['hosted_inference_enabled'] or profiles['default_profile']!='offline':raise ValueError('provider activation changed')
    (E/'preservation.json').write_text(json.dumps({'passed':True,'before':before,'after':after,
        'sourceBindings':source,'sourceOverlayUnchanged':True,'newEmulatorRuns':0,'newROMBuilds':0,
        'newInferenceRequests':0,'credentialReads':0,'existingDatabaseOpened':False},indent=2)+'\n')
    manifest={'schemaVersion':1,'ticket':'CONTENT-01','sourceCommit':content.pack['sourceCommit'],
        'packID':content.pack['packID'],'packVersion':content.pack['version'],
        'packCanonicalSHA256':content.hash,'adaptationRulesSHA256':content.adaptation.hash,'catalogSHA256':content.cat.hash,
        'files':{p:file_hash(ROOT/p) for p in ['config/opening_content.json','config/adaptation_rules.json','content/adaptation.py','schemas/content/adaptation.schema.json','schemas/content/adaptation-profile.schema.json','tests/test_content01_addendum.py','schemas/content/pack.schema.json','schemas/content/resolved.schema.json','content/policy.py','tools/content01.py','tests/test_content01.py']},
        'qualifiedResolutions':len(report['rows']),'liveProgressionExporterImplemented':False,
        'progressionInput':{'script':content.pack['milestone']['script'],'requiredFlags':content.pack['milestone']['flags'],
                            'binding':'exact active paired scope/build/checkpoint/cutoff; trusted native evidence, never a post'},
        'noSelectionInstallationOrSpending':True,'nextTask':'PREP-01','endgameEnabled':False}
    (E/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'productionPackSHA256':content.hash,'qualifiedResolutions':len(report['rows']),'preservationPassed':True}))

if __name__=='__main__':run()

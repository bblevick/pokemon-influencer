#!/usr/bin/env python3
"""Read-only closeout over actual artifacts and protected prior foundation files."""
import json,sys,re,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from roster.extract import digest,file_hash
from tools.roster01_examples import generate
E=ROOT/'evidence/phase3/roster01'
def run():
    catalog=json.loads((ROOT/'config/roster_catalog.json').read_text());policy=json.loads((ROOT/'config/roster_policy.json').read_text());manifest=json.loads((E/'extraction-manifest.json').read_text())
    assert digest({k:v for k,v in catalog.items() if k!='catalogSHA256'})==catalog['catalogSHA256']==manifest['catalogSHA256']
    assert digest(policy)==manifest['policySHA256']
    prior=json.loads((ROOT/'evidence/phase2/pokebook01/manifest-enabled.json').read_text())
    overlay={p:file_hash(ROOT/p)==sha for p,sha in prior['overlay_sha256'].items()}
    assert all(overlay.values()),'source overlay differs from accepted PokeBook'
    protected=['.local/pokebook01-enabled/pokefirered.gba','pokefirered.gba','.local/pokebook01/world.sqlite3','.local/pokebook01/acceptance.sqlite3','.local/pokebook01/S1.sav','.local/pokebook01/S2.sav','config/model_profiles.yaml','.local/hermes01/live-budget.json','.local/hermes01/closeout-live-budget.json']
    before={p:file_hash(ROOT/p) for p in protected}
    # Exercise the actual pure services while protecting actual campaign artifacts.
    examples=generate()
    after={p:file_hash(ROOT/p) for p in protected}
    assert before==after,'query side effects'
    assert after['.local/pokebook01-enabled/pokefirered.gba']=='bec6245f354e0846a9e606ba0665d9dabc2e4f9825ba278342755143de56e829'
    assert after['pokefirered.gba']=='3d0c79f1627022e18765766f6cb5ea067f6b5bf7dca115552189ad65a5c3a8ac'
    profile=json.loads((ROOT/'config/model_profiles.yaml').read_text());assert profile['default_profile']=='offline' and profile['hosted_inference_enabled'] is False
    budget=json.loads((ROOT/'.local/hermes01/live-budget.json').read_text());closed=json.loads((ROOT/'.local/hermes01/closeout-live-budget.json').read_text());assert budget['attempts']==10 and closed['attempts']==5 and closed['closed'] is True
    preservation={'passed':True,'acceptedSourceOverlayMatches':overlay,'protectedBefore':before,'protectedAfter':after,'newModelRequests':0,'hostedInferenceEnabled':False,'defaultProfile':'offline','priorHermesAttempts':10,'closedCloseoutAttempts':5,'noROMBuildOrEmulatorRun':True,'noCredentialReadOrNetwork':True,'gameplayWriterImplemented':False}
    (E/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    log=(E/'host-tests.log').read_text();count=int(re.search(r'Ran (\d+) tests',log)[1]);assert log.rstrip().endswith('OK')
    agreement=json.loads((E/'source-agreement.json').read_text());native=json.loads((E/'native-default-moves.json').read_text());assert agreement['passed'] and native['passed']
    result={'accepted':True,'completedTicketIDs':['ROSTER-01'],'catalogSHA256':catalog['catalogSHA256'],'policySHA256':digest(policy),'romSHA256':after['.local/pokebook01-enabled/pokefirered.gba'],'hostTests':count,'newHostTests':count-226,'independentARMChecks':agreement['checks'],'nativeFunctionCases':native['cases'],'sourceCommit':catalog['sourceCommit'],'qualifiedSlice':'Rick baseline and pure early mechanics; explicit fixture-only development. Production stage/resource/Gym gaps block changes.','newInferenceRequests':0,'noGameplayMutation':True,'newEmulatorRuns':0,'nextTask':'CONTENT-01','openRisks':['missing actual stage/opportunity/inventory/travel/signature/Gym bindings','no durable companion/resource issuer or complete package/envelope/commit/installation','unsupported special acquisition/history/evolution methods and NPC item execution','deduplicated Hermes facts do not establish action frequency/order/timing','catalog internal: future model tools must bind actor and active branch','current live legal-action exporter/executor incomplete; endgame deferred']}
    (E/'completion.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':
    if sys.flags.optimize:raise RuntimeError('verification requires assertions')
    run()

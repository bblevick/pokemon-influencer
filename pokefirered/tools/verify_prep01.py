#!/usr/bin/env python3
"""Closeout assertions over actual saved PREP evidence; never run a fake game."""
import json,re,hashlib,sys
from pathlib import Path
from prep01 import ROOT,E,manifest
from prep.domain import schema_validate,validator_identity

def verify():
    checks=[]
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:raise ValueError(name)
    read=lambda name:json.loads((E/name).read_text())
    before=read('native-before-brock.json');after=read('native-after-boulder.json')
    check('native milestone absent before',not any(before['preparation']['progression']['flags'].values()))
    check('Rick unavailable before',before['rick']['result']['status']=='blocked' and before['rick']['opportunity'] is None)
    check('Brock first source-bound',before['brock']['result']['envelope']['identityPolicy']['theme']['maximumSupport']==0)
    check('native milestone both flags after',all(after['preparation']['progression']['flags'].values()))
    check('actual completed Brock battle',any(b['trainerID']=='fr:trainer:0414' and b['ended'] and b['defeated'] and b['outcome']==1 for b in after['world']['battles'].values()))
    opportunities=after['preparation']['opportunities']
    check('one Rick earned opportunity',sum(o['actor']=='trainer:fr:trainer:0102' for o in opportunities.values())==1)
    rick=after['rick']['result'];envelope=rick['envelope'];schema_validate('envelope',envelope)
    check('Rick source unchanged durable levels', [c['level'] for c in after['rick']['companionState']]==[6,6])
    check('Rick targets and aggregate limits',sorted(v['target'] for v in envelope['levels'].values())==[10,10] and envelope['budgets']['aggregateMoveChanges']==2 and envelope['acquisition']['allowance']==0)
    check('zero finite stock',not envelope['resources']['owned'] and not envelope['resources']['available'] and envelope['resources']['restock'] is False)
    candidates=rick['candidateSet']['candidates']
    check('bounded meaningful native Rick options',2<len(candidates)<=16 and any(c['descriptors']['evolvedCompanions'] for c in candidates))
    for candidate in candidates:schema_validate('candidate',candidate)
    check('fully validated complete host packages',all(c['validation']['valid'] and c['validation']['scope']=='complete opening host package, not native installed team' for c in candidates))
    check('no selection consumption or installation',rick['selectedCandidateID'] is None and rick['commitment'] is None and not rick['installed'] and all(o['status']=='available' for o in opportunities.values()) and not after['preparation']['reservations'])
    restores=read('native-restores.json')
    check('fresh runtime retrieves durable opportunity',restores['freshAfter']['preparation']==after['preparation'])
    check('old candidate rejected after fresh runtime',not restores['freshAfter']['oldCandidateValidation']['valid'])
    check('native paired before restore has no future grant',not restores['before']['preparation']['opportunities'] and not any(restores['before']['preparation']['progression']['flags'].values()))
    check('before restore rejects old candidate',not restores['before']['oldCandidateValidation']['valid'])
    check('before restore exact canonical prefix',restores['before']['world']==before['world'])
    check('fresh restart exact canonical prefix',restores['freshAfter']['world']==after['world'])
    check('native paired after restore restores one original grant',restores['after']['preparation']==after['preparation'])
    check('after restore exact canonical prefix',restores['after']['world']==after['world'])
    check('after restore rejects old candidate',not restores['after']['oldCandidateValidation']['valid'])
    check('actual invalid-option examples rejected',all(not x['rejection']['valid'] for x in read('rejected-options.json')['results']))
    check('manifest binds final validator',read('manifest.json')['validatorSHA256']==envelope['rules']['validatorSHA256']==validator_identity())
    check('fresh processes actually Continued',all(r['continueScreenshot'] and (ROOT/r['continueScreenshot']).exists() and r['launchNonce'] for r in restores.values()))
    check('native savedataUpdated receipts drained',all(p['receipt']['drops']==0 and p['receipt']['depth']==0 and p['receipt']['ack']==p['receipt']['eventCounter'] for p in [before['pairing'],after['pairing']]))
    check('no new memory or ROM bytes',read('memory-impact.json')['newStaticRAMBytes']==0 and manifest()['rom_sha256']=='bec6245f354e0846a9e606ba0665d9dabc2e4f9825ba278342755143de56e829')
    preservation=read('preservation.json');check('protected accepted artifacts preserved',preservation['checked']==114 and not preservation['changed'] and not preservation['missing'])
    tests=(E/'host-tests.log').read_text();count=int(re.search(r'Ran (\d+) tests',tests).group(1));check('final host suite unskipped',tests.rstrip().endswith('OK') and 'skipped=' not in tests and count>=338)
    doug=read('doug-fixture-report.json');check('Doug distinctly fixture qualified',[c['level'] for c in doug['companionState']]==[7,7,7] and sorted(v['target'] for v in doug['result']['envelope']['levels'].values())==[11,11,11] and 'NOT native' in doug['evidenceKind'])
    check('Janice no forest opportunity',after['janice']['opportunity'] is None and after['janiceFirst']['result']['status']=='resolved')
    result={'ticket':'PREP-01','status':'accepted','checks':checks,'hostTests':count,'skipped':0,'nativeEvidence':'actual managed mGBA normal battle/Boulder/save/fresh Continue/paired restores',
            'candidateCounts':{'RickNative':len(candidates),'DougFixture':len(doug['result']['candidateSet']['candidates']),'BrockFirstNative':len(before['brock']['result']['candidateSet']['candidates']),'JaniceFirstNativeStage':len(after['janiceFirst']['result']['candidateSet']['candidates'])},
            'modelsCalled':False,'teamSelected':False,'teamCommitted':False,'teamInstalled':False,'endgameImplemented':False,'nextTask':'STRATEGY-01 under separate authorization','remainingGates':['PREP-ACQ-01/later content','Strategy intent/briefing/provider','SYSTEM1 A commitment/installation','SYSTEM1 B legal-action coverage']}
    (E/'completion.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(checks),'hostTests':count,'candidateCounts':result['candidateCounts']}))
if __name__=='__main__':verify()

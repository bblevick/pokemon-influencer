#!/usr/bin/env python3
"""Evidence checks over actual final-build logs; no emulator actions or fabricated steps."""
import hashlib,json,sys
from pathlib import Path
from pokebook01 import ROOT,E,manifest
from pokebook.wire import HEADER
from bridge.ui import INV

def read(name):return json.loads((E/name).read_text())
def lines(path):return [json.loads(s) for s in path.read_text().splitlines() if s]
def verify():
 checks=[]
 def check(label,condition):
  if not condition:raise AssertionError(label)
  checks.append(label)
 m=manifest();check('enabled RAM symbols',m['allocation_checks']['original_ram_symbols_unchanged'] and m['ewram_remaining']==220)
 check('disabled baseline',read('manifest-disabled.json')['allocation_checks']['disabled_matches_phase0'])
 check('host and actual C',read('tests.json')['passed'])
 check('retained C',all(r['exitCode']==0 for r in read('retained-c.json')))
 check('viewing read-only',read('native-read-only.json')['allUnchanged'] and read('fixture-read-only.json')['allUnchanged'])
 records=read('native-records-S2.json');posts=records['social']['posts'];check('one real post',len(posts)==1)
 post=next(iter(posts.values()));check('one real follow',records['playerFollowerCount']==1)
 outcome=next(iter(records['puppeteer']['obligations'].values()))['outcome']
 check('production offline fallback',outcome['producer']=='deterministic_fallback' and outcome['fallbackReason']=='offline_mode')
 check('Janice scoped',len(records['trainerPackets']['trainer:fr:trainer:0116']['reportedClaims'])==2)
 check('Doug empty',not records['trainerPackets']['trainer:fr:trainer:0103']['reportedClaims'])
 resources=lines(E/'emulator.jsonl.resources')
 opens=[r for r in resources if r['label'].startswith('accepted-repeat-') and r['label'].endswith('-open')]
 closed=[r for r in resources if r['label'].startswith('accepted-repeat-') and r['label'].endswith('-closed')]
 check('five real cycles',len(opens)==len(closed)==5)
 check('open resources',all((r['allocated'],r['tasks'],r['windows'],r['sprites'])==(15572,1,1,0) and r['viewerOwner'] for r in opens))
 check('closed resources stable',len({(r['free'],r['largest'],r['allocated'],r['blocks'],r['tasks'],r['windows'],r['sprites'],r['viewerOwner']) for r in closed})==1 and all(r['viewerOwner']==0 for r in closed))
 host=lines(E/'host.jsonl');groups={}
 for row in host:
  if row['event']!='viewer-response':continue
  payload=bytes.fromhex(row['responseHex']);h=HEADER.unpack_from(payload)
  if h[1]==3:groups.setdefault((tuple(row['historySHA256']),h[3],h[4]),{})[h[6]]=payload[24:]
 for filename in ['stored-hermes-public-fixture.json','layout-public-fixture.json']:
  fixture=read(filename);matching=[]
  for chunks in groups.values():
   if sorted(chunks)!=list(range(len(chunks))):continue
   text=''.join(INV[c] for k in sorted(chunks) for c in chunks[k] if c!=254)
   if text==fixture['body']:matching.append(len(chunks))
  check('complete native wire '+filename,bool(matching))
  if filename.startswith('layout'):check('five pages',5 in matching)
 check('three-row fixture selection',read('fixture-read-only.json')['selectedRow']==3 and read('fixture-read-only.json')['layoutRows']==3)
 check('faults executed',len(read('native-fault-scenarios.json'))==11)
 check('unavailable outcomes',all(read('native-unavailable-pixels.json')['results'].values()))
 emu=lines(E/'emulator.jsonl');check('late phase rejection',any(r['event']=='ui-duplicate-or-phase-rejected' for r in emu))
 early=read('restored-S1.json');late=read('restored-S2.json')
 check('abandoned native payload rejected',early['abandonedPayloadReplay']['nativeRejected'])
 check('native early empty',early['posts']==0 and early['followers']==0 and early['janiceClaims']==0 and early['scopeRevoked'])
 check('native late returns',late['posts']==1 and late['followers']==1 and late['hashesEqual'] and late['scopeRevoked'])
 pictures=[]
 for p in sorted((ROOT/'evidence/private/pokebook01').glob('*.png')):
  pictures.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 (E/'screenshots.json').write_text(json.dumps(pictures,indent=2)+'\n')
 result={'passed':True,'checks':checks,'romSHA256':m['rom_sha256'],'screenshots':len(pictures),'scope':'new host/C/ARM and actual managed native evidence; fixtures distinctly labeled; no inference calls'}
 (E/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':verify()

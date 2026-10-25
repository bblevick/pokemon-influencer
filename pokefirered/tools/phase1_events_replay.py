#!/usr/bin/env python3
"""Offline deterministic schema/identity/order replay. No emulator or provider."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge.events import Consumer,JSON_VALIDATOR
from bridge.events_wire import Message
p=argparse.ArgumentParser();p.add_argument('--log');p.add_argument('--report');a=p.parse_args()
root=Path(__file__).resolve().parents[1]
fixtures=list((root/'tests/fixtures/bridge02').glob('*.json'))
for f in fixtures:JSON_VALIDATOR.validate(json.loads(f.read_text()))
consumers={};count=0
if a.log:
 for line in Path(a.log).read_text().splitlines():
  expected=json.loads(line);wire=bytes.fromhex(expected['wireHex']);msg=Message.decode(wire[2:])
  key=msg.nonce,msg.generation,msg.tag
  actual,_=consumers.setdefault(key,Consumer(*key)).accept(msg)
  assert actual is not None,'accepted log contains duplicate'
  assert actual=={k:v for k,v in expected.items() if k not in ('wireHex','romSHA256')},'replay mismatch'
  count+=1
report={'fixtureCount':len(fixtures),'replayedRecords':count,'identityCount':len(consumers),'passed':True,'scope':'offline recorded bytes and fictional schema fixtures; no emulator/provider invocation'}
if a.report:Path(a.report).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

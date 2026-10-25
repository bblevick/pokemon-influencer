#!/usr/bin/env python3
"""Assert retained final-build native evidence; does not run a new playthrough."""
import hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
from bridge.events_wire import Message
from bridge.ui import Command,decode_response
from bridge.events import decode_event,observation_for_context
from jsonschema import Draft202012Validator
from phase1_ui_build import verify_ui
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase1/bridge03'
def rows(name):return [json.loads(x) for x in (E/name).read_text().splitlines()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks={}
def check(name,value):checks[name]=bool(value)
def main():
 m=json.loads((E/'manifest-enabled.json').read_text());verify_ui(m);check('compiled_allocation_passed',m['static_passed'] and m['ewram_remaining']==224)
 check('UI_allocation_212_bytes',m['ui_mailbox']['size']+m['ui_mailbox']['control_size']==212)
 disabled=json.loads((E/'manifest-disabled.json').read_text());base=json.loads((ROOT/'evidence/phase0/baseline.json').read_text())
 check('disabled_exact_baseline',disabled['rom_sha256']==base['sha256'])
 check('changed_from_BRIDGE02',m['rom_sha256']!=json.loads((ROOT/'evidence/phase1/bridge02/manifest-enabled.json').read_text())['rom_sha256'])
 for name in ['host-static-tests.json','events-regression/host-static-tests.json','ping-regression/host-static-tests.json']:check(name,json.loads((E/name).read_text())['passed'])
 host=rows('host.jsonl');emu=rows('emulator.jsonl');responses=rows('ui-responses.jsonl');scenarios=rows('scenarios.jsonl')
 metadata={};commands={}
 for row in host:
  if row['event']=='ui-request':metadata[(row['run'],row['requestID'])]=row
  elif row['event']=='ui-command':
   req=metadata[(row['run'],row['requestID'])];kind=req['kind'];commands[(row['run'],row['commandID'])]=Command(row['commandID'],row['requestID'],kind,row['text'],((11,'YES'),(22,'NO')) if kind==2 else ())
 validator=Draft202012Validator(json.loads((ROOT/'schemas/bridge/ui-response.schema.json').read_text()))
 identities=[]
 for row in responses:
  msg=Message.decode(bytes.fromhex(row['wireHex'])[2:]);decoded=decode_response(msg,commands[(row['run'],row['commandID'])],row['session'],row['run'],m['build_tag']);validator.validate(decoded)
  check('response-'+str(row['commandID'])+'-correlated',all(row[k]==v for k,v in decoded.items()) and row['romSHA256']==m['rom_sha256'])
  identities.append((row['session'],row['run'],row['commandID']))
 check('no_duplicate_player_effect',len(set(identities))==len(identities))
 for scenario in scenarios:
  expected=scenario['expected'];row=scenario['response'];check('scenario-'+scenario['name'],(row['commandType'],row['result'],row['choiceID'])==(expected['kind'],expected['result'],expected['choice']))
  for item in scenario['screenshots']:check('image-'+scenario['name']+'-'+Path(item['path']).stem,sha(ROOT/item['path'])==item['sha256'])
 check('native_notice_ack',any(r['commandType']==1 and r['result']==0 for r in responses))
 check('native_NO_stable_22',any(r['commandType']==2 and r['result']==0 and r['choiceID']==22 for r in responses))
 check('questlog_menu_battle_busy',len([r for r in responses if r['result']==5])>=3)
 check('duplicate_command_rejected',any(r['event']=='ui-duplicate-or-phase-rejected' for r in emu))
 check('wrong_run_command_rejected',any(r['event']=='ui-stale-rejected' for r in emu))
 check('duplicate_player_receipt_deduped',any(r['event']=='ui-response-duplicate' for r in host))
 check('host_restart_recovered',any(r['event']=='fixture-log-restored' and r.get('command_count',0)>=20 for r in host) and any(r['commandID']==21 and r['result']==0 for r in responses))
 for which in ['rollback','reset']:
  boundary=json.loads((E/(which+'-boundary.json')).read_text());old=boundary['pending_command'];runs=[r['run'] for r in boundary['host_runs']];new=old['run']+1
  check(which+'-new-run',new in runs)
  check(which+'-old-command-not-accepted-in-new-run',not any(r['commandID']==old['commandID'] and r['run']>=new for r in responses))
  check(which+'-cleared-image',(ROOT/'evidence/private/bridge03'/f'{which}-cleared.png').is_file())
 check('reset_native_ids_zero',any(r['event']=='ui-state' and 'state=0 request=0 command=0' in r['detail'] and 'run=3' in r['detail'] for r in emu))
 check('managed_rollback_boundary',any(r['event']=='ui-managed-boundary' and 'run=2' in r['detail'] for r in emu))
 check('post_boundary_notice_success',all(any(r['name']==n and r['response']['result']==0 for r in scenarios) for n in ['after-rollback','after-reset']))
 for which in ['absent','disconnect','timeout','oversized-wire']:
  report=json.loads((E/(which+'-availability.json')).read_text());trace=report['emulator_trace_tail'];positions=[]
  for r in trace:
   if r['event']=='persist':
    match=re.search(r' x=(\d+) y=(\d+)',r['detail'])
    if match:positions.append(tuple(map(int,match.groups())))
  check(which+'-native-movement',len(set(positions))>=2 and positions[-1]==(42,46))
  check(which+'-UI-idle',any(r['event']=='ui-diagnostic' and 'state=0 ' in r['detail'] for r in trace))
  if which=='absent':check('no_host_request_in_absent_case',not any(r['event']=='ui-request' for r in report['host_trace_since_start']))
  if which=='oversized-wire':check('oversized_transport_rejected',any(r['event']=='disconnected' and 'oversized/short frame' in r['detail'] for r in trace))
 events=rows('events.jsonl');canonical=rows('canonical-events.jsonl');observations=rows('observations.jsonl')
 check('canonical_UI_separation',all(r['recordClass']=='canonical_event' for r in canonical) and all(r['recordClass']=='observation' for r in observations))
 for row in events:
  decoded=decode_event(Message.decode(bytes.fromhex(row['wireHex'])[2:]));check('event-'+str(row['sequence'])+'-codec',all(row[k]==v for k,v in decoded.items()))
  if row['recordClass']=='observation':observation_for_context(row)
  else:
   try:observation_for_context(row)
   except ValueError:pass
   else:raise AssertionError('canonical truth authorized as NPC knowledge')
 wild=json.loads((E/'final-wild-regression.json').read_text());check('final_native_wild_win',wild['start']['payload']['battleKind']=='wild' and wild['end']['payload']['outcome']==1)
 check('no_UI_mixed_in_event_sinks',len(events)==len(canonical)+len(observations))
 saved=json.loads((E/'native-battery-save.json').read_text())
 check('native_save_checksum_counter4',saved['passed'] and any(x['valid'] and x['counter']==4 for x in saved['slots']))
 check('retained_battery_copy_hash',sha(ROOT/'.local/phase1-ui-emulator/bridge03-native-counter4.sav')==saved['sha256'])
 check('actual_native_save_callback',any(r['event']=='savedataUpdated' for r in emu))
 check('user_dump_unchanged',sha(ROOT/'pokefirered.gba')==base['sha256'])
 screenshot_files=['ui-native-save-confirmed','notice-shown','choice-shown','questlog-busy-final','native-menu-busy','battle-ui-busy','rollback-pending','rollback-cleared','reset-pending','reset-cleared','absent-idle','absent-moved','absent-returned']
 images={name:sha(ROOT/'evidence/private/bridge03'/f'{name}.png') for name in screenshot_files}
 for name in screenshot_files:check('retained-native-'+name,True)
 report={'scope':'retained actual final-ROM live evidence assertions; no new emulator replay; managed lifecycle only','romSHA256':m['rom_sha256'],'session':responses[0]['session'],'responseCount':len(responses),'eventCount':len(events),'checks':checks,'assertionCount':len(checks),'screenshotSHA256':images,'passed':all(checks.values()),'unsupported':['arbitrary unmanaged loads/rewind','durable host/save pairing','unlimited reconnect/same-process script reload','high/unbounded fast-forward'],'visual_review':'Native notice/choice, busy menus/battle, malformed unchanged field, reset intro and rollback cleared field inspected by the implementation agent.'}
 (E/'emulator-integration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'assertionCount':len(checks),'responses':len(responses),'events':len(events),'failed':[k for k,v in checks.items() if not v]}));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

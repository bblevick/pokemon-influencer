#!/usr/bin/env python3
"""Assert retained LIVE BRIDGE-01 evidence; does not simulate or launch a game."""
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase1'
rows=[json.loads(line) for line in (E/'emulator.jsonl').read_text().splitlines()]
log=(E/'emulator.jsonl').read_text()
disabled=(E/'disabled-emulator.log').read_text()
m=json.loads((E/'manifest-enabled.json').read_text())
md=json.loads((E/'manifest-disabled.json').read_text())
checks={
 'compiled_allocation_layout_safe':m['static_passed'],
 'disabled_byte_identical_baseline':md['allocation_checks']['disabled_matches_phase0'],
 'enabled_boot_and_matching_manifest':sum(x['event']=='build-validated' and x['detail']==m['rom_sha256'] for x in rows)>=2,
 'native_script_listener_repeated_across_launches':sum(x['event']=='listening' for x in rows)>=2,
 'roundtrip_request_id_consumed':'ack=1 successes=1 failures=0' in log and any(x['event']=='response-published' and x['detail']=='1' for x in rows),
 'host_absent_timeout_input_live':'absent-host-input state=0' in log and 'failures=1 error=1' in log,
 'midrequest_disconnect_degraded':'disconnect-field state=0' in log and 'error=5' in log,
 'delayed_reply_timeout_rejected':any(x['event']=='request-expired' and x['detail']=='5' for x in rows) and any(x['event']=='stale-response-rejected' and x['detail']=='5' for x in rows),
 'fragmented_response_consumed':'ack=6 successes=2' in log,
 'duplicate_response_consumed_once':'ack=7 successes=3' in log and any(x['event']=='stale-response-rejected' and x['detail']=='7' for x in rows),
 'actual_battery_write_callback':any(x['event']=='savedataUpdated' for x in rows),
 'valid_battery_counter_2':any(s['valid'] and s['counter']==2 for s in json.loads((E/'battery-save.json').read_text())['slots']),
 'same_game_save_reloaded':all(label+' counter=2 partycount=1 level=5 hp=5 x=18 y=32 mapgroup=3 mapnum=19' in log for label in ['saved-before-reload','fresh-after-reload']),
 'soft_reset_idle_zero_identity':'soft-reset-idle state=0' in log and 'sequence=0 ack=0 successes=0 failures=0 error=0 generation=0' in log,
 'wrong_manifest_no_memory_writes':json.loads((E/'wrong-build-live.json').read_text())['passed'],
 'disabled_normal_boot_and_continue':'disabled-build-boot CRC='+md['rom_crc32'] in disabled and bool(re.search(r'shot=disabled-field .*counter=2 x=18 y=32 mapgroup=3 mapnum=19',disabled)),
 'phase0_assertions_retained':json.loads((ROOT/'evidence/phase0/emulator-smoke.json').read_text())['passed'],
}
images={}
for name in ['enabled-title','absent-host-input','disconnect-field','delayed-response-field','enabled-save-menu','enabled-save-written','soft-reset-idle','fresh-reload-field','disabled-boot','disabled-field']:
 p=ROOT/'evidence/private/phase1'/f'{name}.png'
 checks['retained_image_'+name]=p.is_file()
 if p.is_file():images[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
# Each native bridge load begins a new segment. Correlate forwarding, response publication and ROM ack.
segments=[];current=[]
for row in rows:
 if row['event']=='build-validated':
  if current:segments.append(current)
  current=[]
 current.append(row)
if current:segments.append(current)
roundtrips=[]
for session,segment in enumerate(segments):
 for request in [r for r in segment if r['event']=='request-forwarded']:
  seq=request['detail'];response=next((r for r in segment if r['event']=='response-published' and r['detail']==seq and r['frame']>=request['frame']),None)
  ack=next((r for r in segment if r['event']=='ROM-status' and re.match('ack='+seq+r'\b',r['detail']) and r['frame']>=request['frame']),None)
  if response and ack:roundtrips.append({'launch_segment':session,'sequence':int(seq),'forward_frame':request['frame'],'response_frame':response['frame'],'ack_frame':ack['frame'],'forward_to_ack_frames':ack['frame']-request['frame']})
report={'scope':'retained live emulator/visual evidence assertions, not a new replay; ordinary battle is retained Phase 0 evidence',
        'protocol_version':1,'emulator_version':'0.10.5','rom_sha256':m['rom_sha256'],'mailbox_address':m['mailbox']['address'],'mailbox_size':m['mailbox']['size'],
        'checks':checks,'roundtrips':roundtrips,'screenshot_sha256':images,'passed':all(checks.values()),
        'not_run_in_emulator':['all malformed header/version/oversize combinations (host and native C tested)','fast-forward','savestate rewind/battery rollback','worst-case stack-depth stress','production transport endurance/backpressure','full golden path/new ordinary battle']}
(E/'emulator-integration.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'passed':report['passed'],'roundtrips':roundtrips,'failed':[k for k,v in checks.items() if not v]},indent=2))
raise SystemExit(0 if report['passed'] else 1)

#!/usr/bin/env python3
"""BRIDGE-03 isolated builds and ELF-allocated presentation mailbox."""
import argparse,json,struct
from pathlib import Path
import phase1_events_build as b
ROOT=b.ROOT
E=ROOT/'evidence/phase1/bridge03'
UI_FILES=['include/pi_ui.h','src/pi_ui.c','src/overworld.c','src/text_printer.c']
SPEC=json.loads((ROOT/'bridge/ui_protocol.json').read_text())
FIELDS={}
offset=0
for name,n in SPEC['mailbox_fields']:
 FIELDS[name]={'offset':offset,'size':n};offset+=n

def build(enabled,reuse=False,events_only=False):
 # Reuse audited B2 builder with isolated output names; no B2 evidence overwritten.
 from generate_pi_ui import generate
 generate()
 E.mkdir(parents=True,exist_ok=True)
 b.E=E
 b.build(enabled,reuse,output_prefix='phase1-ui-events' if events_only else 'phase1-ui',ui=not events_only)
 p=E/('manifest-enabled.json' if enabled else 'manifest-disabled.json');m=json.loads(p.read_text())
 if enabled and not events_only:
  elf=ROOT/m['rom_path'].replace('.gba','.elf');symbols=b.symbols(elf);rom=(ROOT/m['rom_path']).read_bytes()
  layout=struct.unpack_from('<'+'I'*(2+len(FIELDS)),rom,symbols['gPiUiLayout']['address']-0x08000000)
  size,control=layout[:2]
  if size!=offset or list(layout[2:])!=[x['offset'] for x in FIELDS.values()] or size+control>240:raise SystemExit('compiled UI ABI mismatch')
  m['ui_protocol']=SPEC;m['ui_schema_version']=1;m['target']['ui_enabled']=True;m['target']['debug_ui']=True
  m['ui_mailbox']={'address':symbols['gPiUi']['address'],'size':size,'fields':FIELDS,'control_size':control}
  m['ui_harness_sha256']={x:b.sha(ROOT/x) for x in ['bridge/ui_transport_mgba.lua','bridge/ui_mgba.lua']}
  p.write_text(json.dumps(m,indent=2)+'\n')
  print(json.dumps({'ui_mailbox':m['ui_mailbox'],'ewram_remaining':m['ewram_remaining']}))
 if events_only:p.rename(E/('manifest-events-'+('enabled' if enabled else 'disabled')+'.json'))
def verify_ui(m):
 """Verify physical UI allocation before any launcher/Lua memory writes."""
 from phase1_events_host import verify
 verify(m)
 if m.get('ui_schema_version')!=1 or not m['target'].get('ui_enabled') or m.get('ui_protocol')!=SPEC:raise ValueError('UI manifest/schema')
 elf=ROOT/m['rom_path'].replace('.gba','.elf');syms=b.symbols(elf);ui=m['ui_mailbox']
 if syms['gPiUi']!={'address':ui['address'],'size':ui['size']} or ui['fields']!=FIELDS:raise ValueError('ELF UI mailbox/fields mismatch')
 data=(ROOT/m['rom_path']).read_bytes();layout=struct.unpack_from('<'+'I'*(2+len(FIELDS)),data,syms['gPiUiLayout']['address']-0x08000000)
 if list(layout)!=[offset,ui['control_size']]+[x['offset'] for x in FIELDS.values()]:raise ValueError('compiled UI layout mismatch')
 if not m['mailbox']['address']+m['mailbox']['size']<=ui['address']<syms['__pi_mailbox_end']['address']<=0x02040000:raise ValueError('UI allocation bounds')
 for file in ['bridge/ui_transport_mgba.lua','bridge/ui_mgba.lua','bridge/ui.py','bridge/ui_protocol.json','schemas/bridge/ui-command.schema.json','schemas/bridge/ui-response.schema.json']:
  if b.sha(ROOT/file)!=m['overlay_sha256'][file]:raise ValueError('UI codec/harness/schema hash mismatch')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--disabled',action='store_true');p.add_argument('--verify-existing',action='store_true');p.add_argument('--events-only',action='store_true');a=p.parse_args();build(not a.disabled,a.verify_existing,a.events_only)

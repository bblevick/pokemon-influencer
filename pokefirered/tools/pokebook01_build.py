#!/usr/bin/env python3
"""Isolated POKEBOOK build, retaining prior pinned build evidence."""
import json,struct,argparse,hashlib,shutil,subprocess
import phase1_events_build as b
import phase1_ui_build as u
ROOT=b.ROOT
E=ROOT/'evidence/phase2/pokebook01'
def build(reuse=False,rebuild=False,disabled=False):
 b.E=E;E.mkdir(parents=True,exist_ok=True)
 b.OVERLAY += ['src/start_menu.c','src/new_menu_helpers.c','src/pi_pokebook.c','include/pi_pokebook.h','include/pi_pokebook_wire.h']
 if disabled:
  if rebuild:
   dest=ROOT/'.local/pokebook01-disabled'
   for file in b.OVERLAY:
    if file!='include/pi_build.h':shutil.copy2(ROOT/file,dest/file)
   args=['make','-j8','rom','PI_BRIDGE=0','PI_BRIDGE_TEST=0','PI_EVENTS=0','PI_UI=0','PI_UI_TEST=0','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0']
   with (E/'disabled-rebuild.log').open('w') as out:
    out.write(json.dumps({'argv':args,'cwd':str(dest)})+'\n');out.flush()
    subprocess.run(args,cwd=dest,stdout=out,stderr=subprocess.STDOUT,check=True)
   reuse=True
  b.build(False,reuse,output_prefix='pokebook01',ui=True)
  return
 if rebuild:
  dest=ROOT/'.local/pokebook01-enabled'
  for file in b.OVERLAY:
   if file!='include/pi_build.h':shutil.copy2(ROOT/file,dest/file)
  names=b.OVERLAY+['bridge/events_protocol.json','bridge/events_mgba.lua','bridge/ui_transport_mgba.lua','bridge/ui_mgba.lua','bridge/ui.py','bridge/ui_protocol.json','schemas/bridge/ui-command.schema.json','schemas/bridge/ui-response.schema.json']
  identities={p:b.sha(ROOT/p) for p in names}
  tag=int(hashlib.sha256(json.dumps({'pin':b.phase0.LOCK['source']['commit'],'files':identities,'enabled':True,'ui':True},sort_keys=True).encode()).hexdigest()[:8],16)
  (dest/'include/pi_build.h').write_text('/* Generated content identity; no timestamp. */\n#define PI_BUILD_TAG %du\n'%tag)
  args=['make','-j8','rom','PI_BRIDGE=1','PI_BRIDGE_TEST=0','PI_EVENTS=1','PI_UI=1','PI_UI_TEST=1','GAME_VERSION=FIRERED','GAME_REVISION=0','GAME_LANGUAGE=ENGLISH','MODERN=0']
  with (E/'rebuild.log').open('w') as out:
   out.write(json.dumps({'argv':args,'cwd':str(dest)})+'\n');out.flush()
   subprocess.run(args,cwd=dest,stdout=out,stderr=subprocess.STDOUT,check=True)
  reuse=True
 b.build(True,reuse,output_prefix='pokebook01',ui=True)
 p=E/'manifest-enabled.json';m=json.loads(p.read_text());syms=b.symbols(ROOT/m['rom_path'].replace('.gba','.elf'))
 rom=(ROOT/m['rom_path']).read_bytes();layout=struct.unpack_from('<'+'I'*(2+len(u.FIELDS)),rom,syms['gPiUiLayout']['address']-0x08000000)
 m['ui_protocol']=u.SPEC;m['ui_schema_version']=1;m['viewer_schema_version']=2;m['target']['ui_enabled']=True
 m['ui_mailbox']={'address':syms['gPiUi']['address'],'size':layout[0],'fields':u.FIELDS,'control_size':layout[1]}
 m['ui_harness_sha256']={x:b.sha(ROOT/x) for x in ['bridge/ui_transport_mgba.lua','bridge/ui_mgba.lua']}
 m['viewer_resources']=list(struct.unpack_from('<5I',rom,syms['gPiPokeBookResources']['address']-0x08000000))
 p.write_text(json.dumps(m,indent=2)+'\n');u.verify_ui(m)
 print(json.dumps({'romSHA256':m['rom_sha256'],'remaining':m['ewram_remaining'],'resources':m['viewer_resources']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--verify-existing',action='store_true');p.add_argument('--rebuild',action='store_true');p.add_argument('--disabled',action='store_true');a=p.parse_args();build(a.verify_existing,a.rebuild,a.disabled)

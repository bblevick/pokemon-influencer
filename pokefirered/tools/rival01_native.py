#!/usr/bin/env python3
"""Isolated, explicitly edited battery fixture + real source script qualification.
No paired-campaign claim, cloud, party edits, trainer flag edits or battle outcome.
"""
import json,struct,sys,hashlib,secrets,subprocess,socket,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from world.saves import fingerprint,layout_from_build
from world.store import WorldStore
from bridge.events_wire import Message,Decoder
from phase1_events_launch import lua
from phase1_events_build import symbols
from battle.domain import decode
E=ROOT/'evidence/phase8/rival01-prerequisites';P=ROOT/'.local/rival01-native-fixture';M=E/'manifest-native.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
 P.mkdir(parents=True,exist_ok=True);screens=ROOT/'evidence/private/rival01-prerequisites';screens.mkdir(parents=True,exist_ok=True)
 m=json.loads(M.read_text());sizes=layout_from_build(ROOT/m['rom_path']);syms=symbols(ROOT/m['rom_path'].replace('.gba','.elf'));rom=(ROOT/m['rom_path']).read_bytes();mp=json.loads((ROOT/'data/maps/CeruleanCity/map.json').read_text());addr=syms['CeruleanCity_ObjectEvents']['address']-0x08000000;templates=rom[addr:addr+24*len(mp['object_events'])];assert len(templates)==24*len(mp['object_events'])
 src=ROOT/'.local/rocket01/post-rocket-pair.sav';data=bytearray(src.read_bytes());original=fingerprint(data,sizes);changes=[]
 # Location only in both checksum-valid battery slots. This is a new synthetic
 # source-script fixture, never a repaired accepted pair or campaign travel.
 for slot in range(2):
  for n in range(slot*14,(slot+1)*14):
   off=n*4096;sid,crc,sig,counter=struct.unpack_from('<HHII',data,off+4084)
   if sig!=0x08012025 or sid not in (0,1):continue
   if sid==0:
    before=data[off+9];data[off+9]|=1
    detail={'continueGameWarpBefore':before,'continueGameWarpAfter':data[off+9],'source':'src/load_save.c:134; include/save_location.h CONTINUE_GAME_WARP'}
   else:
    old=data[off:off+20].hex();struct.pack_into('<hh',data,off,22,7)
    for at in (4,12):struct.pack_into('<BBbBhh',data,off+at,3,3,-1,0,22,7)
    struct.pack_into('<H',data,off+0x32,81)
    detail={'beforeLocationHex':old,'afterLocationHex':data[off:off+20].hex(),'layoutID':81,'source':'normal Continue warp reconstructs source map/objects; no saved object edits'}
   total=sum(struct.unpack_from('<'+'I'*(sizes[sid]//4),data,off))&0xffffffff;struct.pack_into('<H',data,off+4086,((total>>16)+total)&0xffff)
   changes.append({'sector':n,'section':sid,**detail,'checksumRecomputed':True})
 save=P/'pokefirered.sav';save.write_bytes(data);identity=fingerprint(data,sizes);nonce=secrets.randbelow(0xffffffff)+1
 db=P/'world.sqlite3';db.unlink(missing_ok=True)
 with WorldStore(db,m['rom_sha256'],m['build_tag']) as w:w.import_save(identity);w.authorize_launch(nonce,identity)
 cfg={'manifest':str(M),'database':str(db),'port':18792,'nonce':nonce,'token':secrets.token_hex(16),'log':str(E/'native-emulator.jsonl'),'screenshots':str(screens)};(P/'launch.json').write_text(json.dumps(cfg));(P/'launch.json').chmod(0o600)
 syms=symbols(ROOT/m['rom_path'].replace('.gba','.elf'))
 for name in ['gHeap','gPlayerAvatar','gObjectEvents','gTrainerBattleOpponent_A']:m['diagnostic_symbols'][name]=syms[name]['address']
 prefix='PI_MANIFEST='+lua(m)+'\nPI_MANIFEST.rom_sha256_binary="'+''.join('\\%03d'%x for x in bytes.fromhex(m['rom_sha256']))+'"\nPI_CONFIG='+lua(cfg)+'\n'
 transport=(ROOT/'bridge/ui_transport_mgba.lua').read_text().replace("if PI_UI_receive and kind>=4 then", "if PI_BATTLE_receive and kind>=8 then PI_BATTLE_receive(kind,nonce,gen,seq,typ,data);return end\n if PI_UI_receive and kind>=4 then")
 test=(ROOT/'bridge/events_emulator_smoke.lua').read_text().replace('18773','18793').replace("elseif cmd=='reset'", "elseif cmd=='arm' then PI_BATTLE_arm()\n  elseif cmd=='reset'")
 script=P/'run.lua';script.write_text(prefix+transport+'\n'+(ROOT/'bridge/emulator_smoke.lua').read_text()+'\n'+test+'\n'+(ROOT/'bridge/prep_acceptance_probe.lua').read_text()+'\n'+(ROOT/'bridge/campaign_generic_constructor_receipt.lua').read_text()+'\n'+(ROOT/'native/battle_end01/transport.lua').read_text())
 argv=[str(ROOT/'.local/mGBA.app/Contents/MacOS/mGBA'),'-C','hwaccelVideo=0','-C','savegamePath='+str(P),str(ROOT/m['rom_path'])]
 report={'kind':'EXPLICITLY_EDITED_NATIVE_SCRIPT_FIXTURE_NOT_CAMPAIGN_TRAVEL','sourceSHA256':sha(src),'sourceIdentity':original.as_dict(),'fixtureIdentity':identity.as_dict(),'edits':changes,'partyEdited':False,'storyFlagsEdited':False,'internalContinueWarpBitEdited':True,'varsEdited':False,'pairedToAcceptedCampaign':False,'newImportedTestDatabase':str(db),'script':str(script),'scriptSHA256':sha(script),'argv':argv,'romSHA256':m['rom_sha256'],'hostedCalls':0}
 (E/'native-fixture.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
def record(seconds=300):
 cfg=json.loads((P/'launch.json').read_text());m=json.loads(M.read_text());end=time.monotonic()+seconds;parts={};captured=False
 def log(value):
  with (E/'native-trace.jsonl').open('a') as f:f.write(json.dumps(value)+'\n')
 with WorldStore(Path(cfg['database']),m['rom_sha256'],m['build_tag']) as w:
  while time.monotonic()<end:
   try:
    with socket.create_connection(('127.0.0.1',cfg['port']),timeout=.3) as sock:
     sock.settimeout(.3);decoder=Decoder();sock.sendall(Message(0,cfg['nonce'],0,0,m['build_tag'],0,cfg['token'].encode()+bytes.fromhex(m['rom_sha256'])).encode())
     while time.monotonic()<end:
      try:data=sock.recv(256)
      except socket.timeout:continue
      if not data:break
      for msg in decoder.feed(data):
       log({'kind':msg.kind,'type':msg.typ,'sequence':msg.sequence,'wireHex':msg.encode().hex()})
       if msg.kind==3:continue
       if msg.kind==1:
        result=w.ingest(msg);log({'canonicalReceipt':result,'state':w.state()});sock.sendall(Message(2,msg.nonce,msg.generation,msg.sequence,msg.tag,4,b'').encode())
       elif msg.kind==12:
        trainer,count=struct.unpack('<HI',msg.payload);assert trainer==334 and count==1;log({'nativeConstructor':{'trainer':trainer,'count':count,'actor':'trainer:'+w.registry['mapping'][str(trainer)]}})
       elif msg.kind==8:
        req,h,total,off=struct.unpack_from('<IIHH',msg.payload);key=(req,h);buf=parts.setdefault(key,bytearray(total));buf[off:off+len(msg.payload)-12]=msg.payload[12:]
        if off+len(msg.payload)-12==total:
         state=decode(bytes(buf),m['battle_abi'],m['qualified_trainers']);(E/'native-first-state.json').write_text(json.dumps({'snapshotHex':bytes(buf).hex(),'hash32':h,'state':state},indent=2)+'\n');assert state['trainerID']==334;captured=True
       # Qualification never returns an action; existing timeout stays bounded.
   except OSError:time.sleep(.1)
  log({'recorderEnded':True,'capturedSanitizedNativeState':captured,'worldReplaySHA256':w.verify_replay(),'state':w.state(),'hostedCalls':0})
if __name__=='__main__':prepare() if sys.argv[1]=='prepare' else record(float(sys.argv[2]) if len(sys.argv)>2 else 300)

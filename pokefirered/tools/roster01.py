#!/usr/bin/env python3
"""Generate/verify ROSTER-01 without writing gameplay state or contacting providers."""
import argparse,json,sys,hashlib,subprocess,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from roster.extract import extract,digest,file_hash,PIN
ROM_HASH='bec6245f354e0846a9e606ba0665d9dabc2e4f9825ba278342755143de56e829'
EVIDENCE=ROOT/'evidence/phase3/roster01'
def independent(data):
    """Compare with actual agbcc ARM ROM tables; no host initializer reuse."""
    if sys.flags.optimize:raise RuntimeError('verification requires Python assertions enabled')
    build=ROOT/'.local/pokebook01-enabled';rom=build/'pokefirered.gba'
    if file_hash(rom)!=ROM_HASH:raise ValueError('accepted ROM changed')
    blob=rom.read_bytes();symbols={}
    for line in subprocess.check_output(['arm-none-eabi-nm','-S',str(build/'pokefirered.elf')],text=True).splitlines():
        fields=line.split()
        if len(fields)==4:symbols[fields[3]]=(int(fields[0],16),int(fields[1],16))
    def read(name,offset,n):
        addr,size=symbols[name]
        if offset+n>size:raise ValueError('symbol bounds')
        return blob[addr-0x08000000+offset:addr-0x08000000+offset+n]
    checks=0
    species_stride=symbols['gSpeciesInfo'][1]//len(data['species'])
    move_stride=symbols['gBattleMoves'][1]//len(data['moves'])
    trainer_stride=symbols['gTrainers'][1]//len(data['trainers'])
    if (species_stride,move_stride,trainer_stride)!=(28,12,40):raise ValueError('unexpected ARM layout')
    for row in data['species']:
        i=row['id'];raw=read('gSpeciesInfo',i*28,28)
        assert list(raw[:6])==row['stats'] and list(raw[6:8])==row['types'] and list(raw[22:24])==row['abilities'];checks+=1
        assert read('sTMHMLearnsets',i*8,8).hex()==int(row['tmhmMask'],16).to_bytes(8,'little').hex();checks+=1
        assert [list(struct.unpack('<HHH',read('gEvolutionTable',i*40+j*8,6))) for j in range(5)]==row['evolutions'];checks+=1
        addr=struct.unpack('<I',read('gLevelUpLearnsets',i*4,4))[0]-0x08000000
        levels=[]
        for j in range(256):
            word=struct.unpack_from('<H',blob,addr+j*2)[0]
            if word==65535:break
            levels.append([word>>9,word&511])
        else:raise ValueError('missing ROM terminator')
        assert levels==row['learnset'];checks+=1
    for m in data['moves']:
        raw=read('gBattleMoves',m['id']*12,12)
        assert list(raw[:7])==[m[k] for k in ['effect','power','type','accuracy','pp','secondaryChance','target']]
        assert struct.unpack_from('<b',raw,7)[0]==m['priority'] and raw[8]==m['flags'];checks+=1
    for t in data['trainers']:
        raw=read('gTrainers',t['id']*40,40)
        assert raw[0]==t['flags'] and raw[1]==t['class'] and raw[24]==t['doubleBattle'] and raw[32]==len(t['party']) and struct.unpack_from('<I',raw,28)[0]==t['aiFlags']
        assert list(struct.unpack_from('<4H',raw,16))==t['battleItems'];checks+=1
        pointer=struct.unpack_from('<I',raw,36)[0]-0x08000000
        stride={0:8,1:16,2:8,3:16}[t['flags']]
        for p in t['party']:
            off=pointer+p['slot']*stride
            iv,level,species=(struct.unpack_from('<H',blob,off)[0],blob[off+2],struct.unpack_from('<H',blob,off+4)[0])
            assert [iv,level,species]==[p['ivSource'],p['level'],p['species']]
            if t['flags']&2:assert struct.unpack_from('<H',blob,off+6)[0]==p['heldItem']
            if t['flags']&1:assert list(struct.unpack_from('<4H',blob,off+(8 if t['flags']&2 else 6)))==p['moves']
            checks+=1
    suffix={'land_mons':'LandMons','water_mons':'WaterMons','rock_smash_mons':'RockSmashMons','fishing_mons':'FishingMons'}
    for r in data['encounters']:
        name=r['routeID'].split(':')[0]+'_'+suffix[r['method']]
        raw=read(name,r['slot']*4,4)
        assert list(struct.unpack('<BBH',raw))==[r['minLevel'],r['maxLevel'],r['species']];checks+=1
    for other in data['excludedOtherVersion']:
        assert not any(name.startswith(other+'_') for name in symbols);checks+=1
    assert list(struct.unpack('<58H',read('sTMHMMoves',0,116)))==data['machineMoves'];checks+=1
    for row in data['items']:
        raw=read('gItems',row['id']*44,44)
        assert struct.unpack_from('<HH',raw,14)==(row['declaredID'],row['price'])
        effect=data['constants'][row['holdEffect']] if isinstance(row['holdEffect'],str) else row['holdEffect']
        assert raw[18]==effect and raw[19]==row['holdEffectParam']
        for offset,key in [(28,'fieldUseFunc'),(36,'battleUseFunc')]:
            expected=0 if row[key]=='NULL' else symbols[row[key]][0]|1
            assert struct.unpack_from('<I',raw,offset)[0]==expected
        pocket=data['constants'][row['pocket']]
        kind=data['constants'][row['type']] if isinstance(row['type'],str) else row['type']
        assert (raw[24],raw[25],raw[26],raw[27],raw[32],raw[40])==(row['importance'],row['registrability'],pocket,kind,row['battleUsage'],data['constants'].get(row['secondaryId'],row['secondaryId']));checks+=1
    return {'passed':True,'checks':checks,'path':'actual accepted ARM ROM + ELF symbols','romSHA256':ROM_HASH,'elfSHA256':file_hash(build/'pokefirered.elf'),'layouts':{'species':28,'moves':12,'trainers':40},'wildCoverage':'all selected FireRed encounter slots'}
def run(write=False):
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    data=extract()
    import jsonschema
    jsonschema.validate(data,json.loads((ROOT/'schemas/roster/catalog.schema.json').read_text()))
    target=ROOT/'config/roster_catalog.json'
    if not write and json.loads(target.read_text())!=data:raise ValueError('stale catalog; regenerate explicitly')
    policy=json.loads((ROOT/'config/roster_policy.json').read_text())
    import tempfile
    generated={}
    with tempfile.TemporaryDirectory(prefix='roster-generated-') as tmp:
        for name in ['items','wild_encounters']:
            path=f'src/data/{name}.json';template=path+'.txt';out=Path(tmp)/(name+'.h')
            subprocess.run([str(ROOT/'tools/jsonproc/jsonproc'),path,template,str(out)],cwd=ROOT,check=True)
            actual=ROOT/'src/data'/str(name+'.h'); built=ROOT/'.local/pokebook01-enabled/src/data'/str(name+'.h')
            if out.read_bytes()!=actual.read_bytes() or out.read_bytes()!=built.read_bytes():raise ValueError('generated header/source/accepted build disagreement '+name)
            generated[str(actual.relative_to(ROOT))]=file_hash(out)
    from tools.roster01_native import verify
    native=verify(data)
    (EVIDENCE/'native-default-moves.json').write_text(json.dumps(native,indent=2)+'\n')
    for entry in data['sources']:
        path=entry['path']
        if path.startswith(('src/','include/')):
            built=ROOT/'.local/pokebook01-enabled'/path
            if built.is_file() and file_hash(built)!=entry['sha256']:raise ValueError('relevant source changed versus accepted build: '+path)
    source_agreement=independent(data)
    if write:target.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
    # Preserve content-addressed versions for historical interpretation.
    archive=EVIDENCE/('catalog-'+data['catalogSHA256']+'.json')
    if archive.exists() and json.loads(archive.read_text())!=data:raise ValueError('content address collision')
    archive.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
    (EVIDENCE/('policy-'+digest(policy)+'.json')).write_text(json.dumps(policy,sort_keys=True,indent=2)+'\n')
    (EVIDENCE/'source-agreement.json').write_text(json.dumps(source_agreement,indent=2)+'\n')
    manifest={'schemaVersion':1,'sourceCommit':PIN,'catalogSHA256':data['catalogSHA256'],'policySHA256':digest(policy),'target':data['target'],'sources':data['sources'],'extractorVersion':1,'extractorFiles':{p:file_hash(ROOT/p) for p in ['roster/extract.py','roster/domain.py','roster/fixtures.py','tools/roster01.py','tools/roster01_native.py','schemas/roster/catalog.schema.json','schemas/roster/eligibility.schema.json']},'romAssociation':{'sha256':ROM_HASH,'compatibility':'catalog mechanics identity separate from exact ROM association; existing WORLD build guards unchanged','uiOnlyFilesExcluded':['src/pi_pokebook.c','src/start_menu.c','src/new_menu_helpers.c']},'coverage':data['coverage'],'counts':{k:len(data[k]) for k in ['species','moves','trainers','items','encounters']},'actorBinding':{'implementation':'memory/store.py:actor_id','sha256':file_hash(ROOT/'memory/store.py'),'registrySHA256':file_hash(ROOT/'config/trainer_registry.json')},'generatedHeaders':generated,'jsonprocSHA256':file_hash(ROOT/'tools/jsonproc/jsonproc'),'compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0]}
    (EVIDENCE/'extraction-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'passed':True,'catalogSHA256':data['catalogSHA256'],'policySHA256':digest(policy),'independentChecks':source_agreement['checks']}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();run(a.write)

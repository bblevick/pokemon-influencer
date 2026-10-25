"""Compile effective source tables, rather than scrape C initializer values."""
from __future__ import annotations
import hashlib, json, re, subprocess, tempfile
from pathlib import Path
from memory.store import actor_id
ROOT = Path(__file__).resolve().parents[1]
VERSION = 1
CONSTANT_HEADERS = ['global','species','moves','items','pokemon','abilities','battle','battle_ai','battle_move_effects','trainers','opponents','hold_effects']
PIN = '037335f4c725d7c9aecdac87066f2002b4bd7e14'
TABLES = ['src/data/pokemon/species_info.h','src/data/battle_moves.h',
          'src/data/pokemon/level_up_learnsets.h','src/data/pokemon/level_up_learnset_pointers.h',
          'src/data/pokemon/tmhm_learnsets.h','src/data/pokemon/evolution.h',
          'src/data/trainer_parties.h','src/data/trainers.h']
BEHAVIOR = ['src/pokemon.c','src/battle_main.c','src/evolution_scene.c','src/party_menu.c',
            'src/wild_encounter.c','src/vs_seeker.c','src/item.c','src/item_use.c']
INPUTS = TABLES + BEHAVIOR + ['include/pokemon.h','include/battle.h','include/item.h',
    'include/config.h','include/gba/types.h','include/gba/defines.h','config.mk','src/data/wild_encounters.json','src/data/wild_encounters.json.txt',
    'src/data/items.json','src/data/items.json.txt','src/data/party_menu.h','config/trainer_registry.json']
from .hashes import canonical,digest,file_hash
def struct(text, name):
    m = re.search(r'(?:struct|union) '+name+r'\s*\{.*?\n\};', text, re.S)
    if not m: raise ValueError('missing native definition: '+name)
    return m[0]
def harness(root):
    constants = [root/'include/constants'/(n+'.h') for n in CONSTANT_HEADERS]
    # Actual C compiler resolves branches, aliases, bitmasks, designated defaults.
    includes = ''.join('#include "'+str(p.relative_to(root))+'"\n' for p in constants)
    defs = (root/'include/pokemon.h').read_text(); battles=(root/'include/battle.h').read_text()
    names=['SpeciesInfo','BattleMove','Evolution']
    declarations='\n'.join(struct(defs,n) for n in names)
    declarations+='\n'+'\n'.join(struct(battles,n) for n in ['TrainerMonNoItemDefaultMoves',
        'TrainerMonItemDefaultMoves','TrainerMonNoItemCustomMoves','TrainerMonItemCustomMoves','TrainerMonPtr','Trainer'])
    macros='\n'.join(x for x in battles.splitlines() if x.startswith(('#define MOVE_TARGET_', '#define FLAG_')))+'\n'+'\n'.join(x for x in (battles+'\n'+(root/'include/gba/defines.h').read_text()).splitlines() if x.startswith(('#define MAX_TRAINER_ITEMS ', '#define TRUE ', '#define FALSE ')))+'\n'+'\n'.join(x for x in battles.splitlines() if x.startswith('#define ') and '_MOVES(party)' in x)
    item_enum=re.search(r'enum\s*\{.*?\n\};',(root/'include/item.h').read_text(),re.S)[0]
    declarations+='\n'+item_enum
    symbols = sorted(set(re.findall(r'^#define ((?:SPECIES_|MOVE_|ITEM_|TYPE_|ABILITY_|EVO_|TRAINER_|POCKET_|HOLD_EFFECT_|ITEM_TYPE_)[A-Z0-9_]+)\s',
                             '\n'.join(p.read_text() for p in constants), re.M)))
    symbols+=['OLD_ROD','GOOD_ROD','SUPER_ROD','MAX_PER_STAT_IVS','NUM_TECHNICAL_MACHINES','NUM_HIDDEN_MACHINES']
    symbols+=re.findall(r'\bITEM_TYPE_[A-Z_]+\b',item_enum)
    # Exclude function-like macros and abstract string macros; all selected object IDs must compile.
    constants_c=';'.join('printf("\\\"'+n+'\\\":%lld,",(long long)('+n+'))' for n in symbols)
    pointer_pairs=re.findall(r'\[(SPECIES_\w+)\]\s*=\s*(s\w+LevelUpLearnset)',(root/'src/data/pokemon/level_up_learnset_pointers.h').read_text())
    lengths='static const unsigned learnsetLengths[NUM_SPECIES]={' + ','.join('['+species+']=ARRAY_COUNT('+name+')' for species,name in pointer_pairs)+'};'
    machines=re.search(r'static const u16 sTMHMMoves\[\]\s*=\s*\{.*?\n\};',(root/'src/data/party_menu.h').read_text(),re.S)
    if not machines:raise ValueError('unrecognized machine mapping')
    declarations+='\n'+machines[0]
    code='''#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
typedef uint8_t u8; typedef int8_t s8; typedef uint16_t u16; typedef uint32_t u32; typedef uint64_t u64; typedef uint8_t bool8;
#define _(x) x
#define ARRAY_COUNT(x) (sizeof(x)/sizeof((x)[0]))
#define min(a,b) ((a)<(b)?(a):(b))
'''+includes+macros+'\n'+declarations+'\n'+''.join('#include "'+p+'"\n' for p in TABLES)+lengths+'''
int main(void) {
 printf("{\\\"machineMoves\\\":[");
 for(unsigned i=0;i<ARRAY_COUNT(sTMHMMoves);i++)printf("%s%u",i?",":"",sTMHMMoves[i]);
 printf("],\\\"constants\\\":{");
 CONSTANTS
 printf("\\\"_end\\\":0},\\\"species\\\":[");
 for(unsigned i=0;i<ARRAY_COUNT(gSpeciesInfo);i++) {
 const struct SpeciesInfo *s=&gSpeciesInfo[i];
 printf("%s{\\\"id\\\":%u,\\\"stats\\\":[%u,%u,%u,%u,%u,%u],\\\"types\\\":[%u,%u],\\\"abilities\\\":[%u,%u],\\\"catchRate\\\":%u,\\\"growthRate\\\":%u,\\\"learnset\\\":[",i?",":"",i,s->baseHP,s->baseAttack,s->baseDefense,s->baseSpeed,s->baseSpAttack,s->baseSpDefense,s->types[0],s->types[1],s->abilities[0],s->abilities[1],s->catchRate,s->growthRate);
 if(!gLevelUpLearnsets[i] || !learnsetLengths[i] || learnsetLengths[i]>256) return 2;
 if(gLevelUpLearnsets[i][learnsetLengths[i]-1]!=0xffff)return 3;
 unsigned j=0; for(;j<learnsetLengths[i] && gLevelUpLearnsets[i][j]!=0xffff;j++)
 printf("%s[%u,%u]",j?",":"",gLevelUpLearnsets[i][j]>>9,gLevelUpLearnsets[i][j]&511);
 if(j!=learnsetLengths[i]-1) return 3;
 printf("],\\\"tmhmMask\\\":\\\"%016llx\\\",\\\"evolutions\\\":[",((unsigned long long)sTMHMLearnsets[i][1]<<32)|sTMHMLearnsets[i][0]);
 for(j=0;j<EVOS_PER_MON;j++) printf("%s[%u,%u,%u]",j?",":"",gEvolutionTable[i][j].method,gEvolutionTable[i][j].param,gEvolutionTable[i][j].targetSpecies);
 printf("]}"); }
 printf("],\\\"moves\\\":[");
 for(unsigned i=0;i<MOVES_COUNT;i++){const struct BattleMove *m=&gBattleMoves[i]; printf("%s{\\\"id\\\":%u,\\\"type\\\":%u,\\\"power\\\":%u,\\\"pp\\\":%u,\\\"accuracy\\\":%u,\\\"effect\\\":%u,\\\"target\\\":%u,\\\"priority\\\":%d,\\\"flags\\\":%u,\\\"secondaryChance\\\":%u}",i?",":"",i,m->type,m->power,m->pp,m->accuracy,m->effect,m->target,m->priority,m->flags,m->secondaryEffectChance);}
 printf("],\\\"trainers\\\":[");
 for(unsigned i=0;i<ARRAY_COUNT(gTrainers);i++) { const struct Trainer *t=&gTrainers[i];
 printf("%s{\\\"id\\\":%u,\\\"flags\\\":%u,\\\"class\\\":%u,\\\"aiFlags\\\":%u,\\\"doubleBattle\\\":%u,\\\"battleItems\\\":[",i?",":"",i,t->partyFlags,t->trainerClass,t->aiFlags,t->doubleBattle);
 for(unsigned j=0;j<MAX_TRAINER_ITEMS;j++) printf("%s%u",j?",":"",t->items[j]);
 printf("],\\\"party\\\":[");
 for(unsigned j=0;j<t->partySize;j++) {
 unsigned iv,level,species,item=0;const u16 *moves=NULL;
 switch(t->partyFlags) {
 case 0:{const struct TrainerMonNoItemDefaultMoves *p=&t->party.NoItemDefaultMoves[j];iv=p->iv;level=p->lvl;species=p->species;break;}
 case 1:{const struct TrainerMonNoItemCustomMoves *p=&t->party.NoItemCustomMoves[j];iv=p->iv;level=p->lvl;species=p->species;moves=p->moves;break;}
 case 2:{const struct TrainerMonItemDefaultMoves *p=&t->party.ItemDefaultMoves[j];iv=p->iv;level=p->lvl;species=p->species;item=p->heldItem;break;}
 case 3:{const struct TrainerMonItemCustomMoves *p=&t->party.ItemCustomMoves[j];iv=p->iv;level=p->lvl;species=p->species;item=p->heldItem;moves=p->moves;break;}
 default:return 4;}
 printf("%s{\\\"slot\\\":%u,\\\"ivSource\\\":%u,\\\"fixedIV\\\":%u,\\\"level\\\":%u,\\\"species\\\":%u,\\\"heldItem\\\":%u,\\\"moveMode\\\":\\\"%s\\\",\\\"moves\\\":[",j?",":"",j,iv,iv*MAX_PER_STAT_IVS/255,level,species,item,moves?"authored":"default");
 if(moves) for(unsigned k=0;k<4;k++) printf("%s%u",k?",":"",moves[k]);
 printf("]}");}printf("]}");}printf("]}"); return 0;
}
'''.replace('CONSTANTS',constants_c+';')
    return code

def initial_moves(learnset, level):
    moves=[]
    for at,move in learnset:
        if at>level: break
        if move in moves: continue
        if len(moves)==4: moves.pop(0)
        moves.append(move)
    return moves+[0]*(4-len(moves))

def extract(root=ROOT):
    root=Path(root)
    for path in TABLES:
        for directive in (root/path).read_text().splitlines():
            if directive.startswith(('#if','#elif')) and directive not in ('#if defined(FIRERED)','#elif defined(LEAFGREEN)'):
                raise ValueError('unsupported table condition '+directive)
    # These adapters intentionally cover a known native layout/algorithm. New
    # valid C fields or changed generated-table semantics need explicit audit.
    for path in ['src/data/items.json.txt','src/data/wild_encounters.json.txt','config.mk']:
        baseline=subprocess.check_output(['git','show',PIN+':'+path],cwd=root)
        if (root/path).read_bytes()!=baseline:raise ValueError('unsupported effective generator/config change: '+path)
    for path,names in [('include/pokemon.h',['SpeciesInfo','BattleMove','Evolution']),('include/battle.h',['Trainer','TrainerMonPtr','TrainerMonNoItemDefaultMoves','TrainerMonItemDefaultMoves','TrainerMonNoItemCustomMoves','TrainerMonItemCustomMoves'])]:
        baseline=subprocess.check_output(['git','show',PIN+':'+path],cwd=root,text=True)
        for name in names:
            if struct((root/path).read_text(),name)!=struct(baseline,name):raise ValueError('unsupported native layout change '+name)
    lock=json.loads((root/'config/phase0.lock.json').read_text())
    if lock['source']['commit']!=PIN: raise ValueError('unsupported source pin')
    target=lock['source']['target']
    if (target['game'],target['language'],target['revision'],target['modern'])!=('FIRERED','ENGLISH',0,False): raise ValueError('unsupported target')
    with tempfile.TemporaryDirectory(prefix='roster01-') as tmp:
        c=Path(tmp)/'extract.c'; exe=Path(tmp)/'extract'; c.write_text(harness(root))
        subprocess.run(['clang','-std=gnu11','-Werror','-Wno-macro-redefined','-DFIRERED','-DENGLISH','-DREVISION=0','-DMODERN=0','-I',str(root),'-I',str(root/'include'),str(c),'-o',str(exe)],check=True,capture_output=True)
        data=json.loads(subprocess.check_output([str(exe)]))
    constants=data['constants']; constants.pop('_end')
    for s in data['species']:
        if any(not 1<=l<=100 or not 0<m<len(data['moves']) for l,m in s['learnset']):raise ValueError('unresolved/invalid learnset record')
        if int(s['tmhmMask'],16)>>58:raise ValueError('unknown machine bits')
        if any(m and not 0<t<len(data['species']) for m,p,t in s['evolutions']):raise ValueError('unresolved evolution target')
    for name in ['species','moves','trainers']:
        prefix={'species':'SPECIES_','moves':'MOVE_','trainers':'TRAINER_'}[name]
        allowed=set(re.findall(r'^#define (TRAINER_\w+)\s',(root/'include/constants/opponents.h').read_text(),re.M)) if name=='trainers' else None
        for row in data[name]: row['symbols']=sorted(k for k,v in constants.items() if k.startswith(prefix) and v==row['id'] and (allowed is None or k in allowed))
    registry=json.loads((root/'config/trainer_registry.json').read_text())
    data['trainerFamilies']=registry['families'] if 'families' in registry else registry.get('people',{})
    pointers=dict(re.findall(r'\[(SPECIES_\w+)\]\s*=\s*(s\w+LevelUpLearnset)',(root/'src/data/pokemon/level_up_learnset_pointers.h').read_text()))
    if len(pointers)!=len(data['species']):raise ValueError('unrecognized learnset pointer syntax')
    for key,name in pointers.items():data['species'][constants[key]]['learnsetAlias']=name
    for t in data['trainers']:
        t['worldTrainerID']=registry['mapping'].get(str(t['id']))
        t['actorID']=actor_id(t['worldTrainerID']) if t['worldTrainerID'] else None
        for p in t['party']:
            if p['moveMode']=='default': p['moves']=initial_moves(data['species'][p['species']]['learnset'],p['level'])
            if any(m<0 or m>=len(data['moves']) for m in p['moves']): raise ValueError('unresolved move')
            p['baselineKey']=f"{t['id']}:{p['slot']}"
    items=json.loads((root/'src/data/items.json').read_text())['items']
    data['items']=[]
    for index,item in enumerate(items):
        row=dict(item); row['declaredID']=constants[row['itemId']]; row['id']=index
        if row['declaredID'] not in (0,index): raise ValueError('generated item order mismatch')
        row['unused']=row['declaredID']==0 and index!=0
        row['machineMove']=None
        if 'moveId' in row:
            row['machineMove']=constants['MOVE_'+re.sub(r'(?<!^)(?=[A-Z])','_',row['moveId']).upper()]
        if row['machineMove'] is not None:
            index=row['id']-constants['ITEM_TM01']
            if data['machineMoves'][index]!=row['machineMove']:raise ValueError('machine JSON/engine disagreement')
        data['items'].append(row)
    data['encounters']=[];excluded=[]
    raw=json.loads((root/'src/data/wild_encounters.json').read_text())
    for group in raw['wild_encounter_groups']:
        if not group['for_maps']: continue
        fields={f['type']:f for f in group['fields']}
        for e in group['encounters']:
            label=e['base_label']
            if label.endswith('_LeafGreen'): excluded.append(label);continue
            if not label.endswith('_FireRed'): raise ValueError('unqualified encounter version '+label)
            for method in sorted(set(e)-{'map','base_label'}):
                if method not in fields: raise ValueError('unknown encounter syntax '+method)
                entry=e[method]; slots=entry['mons'];field=fields[method]
                if len(slots)!=len(field['encounter_rates']):raise ValueError('encounter slot count')
                for slot,mon in enumerate(slots):
                    if set(mon)!={'species','min_level','max_level'}:raise ValueError('unknown mon syntax')
                    equipment=next((k for k,v in field.get('groups',{}).items() if slot in v),None)
                    data['encounters'].append({'routeID':f'{label}:{method}:{slot}','map':e['map'],'version':'FIRERED','method':method,'equipment':equipment,'methodPrerequisites':{'land_mons':['authored map access'],'water_mons':['authored map access','surf equipment/permission'],'rock_smash_mons':['authored map access','rock smash equipment/permission'],'fishing_mons':['authored map access',equipment or 'rod']}[method],'slot':slot,'species':constants[mon['species']],'symbol':mon['species'],'minLevel':mon['min_level'],'maxLevel':mon['max_level'],'rate':entry['encounter_rate'],'slotWeight':field['encounter_rates'][slot]})
    data['excludedOtherVersion']=excluded
    paths=sorted(set(INPUTS+['include/constants/'+n+'.h' for n in CONSTANT_HEADERS]))
    sources=[]
    for path in paths:
        current=file_hash(root/path)
        try: base=hashlib.sha256(subprocess.check_output(['git','show',PIN+':'+path],cwd=root,stderr=subprocess.DEVNULL)).hexdigest()
        except subprocess.CalledProcessError: base=None
        sources.append({'path':path,'sha256':current,'pinnedSHA256':base,'dirty':base!=current})
    # Whole behavior-file digests are conservative freshness guards. Unrelated UI files are absent.
    data['schemaVersion']=VERSION;data['extractorVersion']=VERSION
    data['sourceCommit']=PIN;data['target']={'game':'FIRERED','language':'ENGLISH','revision':0,'modern':False}
    data['sources']=sources
    data['engineSemantics']={'defaultMoves':'ordered level-up table, stop at first higher level, skip known moves, shift oldest when full','tmConsumable':True,'hmReusable':True,'HMDeletionExcludesDive':True,'nationalDexEvolutionGate':'target species > SPECIES_MEW','everstoneGate':'prevent evolution except item preview','friendshipDayNight':'disabled in FireRed','battleItemRuntimeQualified':False,'personality':'source CreateNPCTrainerParty name hash; catalog does not reroll or synthesize individual stats'}
    data['coverage']={'tableExtraction':'compiled native initializers','qualification':'early slice only; policy gaps fail closed','acquisitionMethods':['land_mons'],'unsupported':['gifts','trade','fossil','static','breeding','tutor','relearner','special evolution methods','NPC item execution']}
    data['catalogSHA256']=digest(data)
    return data

#!/usr/bin/env python3
"""Compile three actual move-construction functions with a Box accessor substitute.

This checks native algorithm semantics, not encryption/ROM constructors or gameplay.
"""
import subprocess,tempfile,json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from roster.extract import struct,initial_moves,file_hash
FUNCTIONS=['GiveMoveToBoxMon','DeleteFirstMoveAndGiveMoveToBoxMon','GiveBoxMonInitialMoveset']
def function(text,name):
    m=re.search(r'static (?:u16|void) '+name+r'\([^;]+?\)\n\{',text)
    if not m:raise ValueError('missing source function '+name)
    depth=1;i=m.end()
    while depth:
        if text[i]=='{':depth+=1
        if text[i]=='}':depth-=1
        i+=1
    return text[m.start():i]
def verify(data):
    src=(ROOT/'src/pokemon.c').read_text()
    text='''#include <stdio.h>
#include <stdint.h>
typedef int8_t s8; typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32; typedef int32_t s32;
#include "include/constants/species.h"
#include "include/constants/moves.h"
#include "include/constants/pokemon.h"
#define MAX_MON_MOVES 4
struct BoxPokemon {u16 species;u8 level;u16 moves[4];u8 pp[4];u8 bonuses;};
u32 GetBoxMonData(struct BoxPokemon *b,int field,void *unused) {
 if(field==MON_DATA_SPECIES)return b->species;
 if(field==MON_DATA_PP_BONUSES)return b->bonuses;
 if(field>=MON_DATA_MOVE1 && field<=MON_DATA_MOVE4)return b->moves[field-MON_DATA_MOVE1];
 if(field>=MON_DATA_PP1 && field<=MON_DATA_PP4)return b->pp[field-MON_DATA_PP1];
 return 0;}
void SetBoxMonData(struct BoxPokemon *b,int field,const void *value) {
 if(field==MON_DATA_PP_BONUSES)b->bonuses=*(const u8*)value;
 else if(field>=MON_DATA_MOVE1 && field<=MON_DATA_MOVE4)b->moves[field-MON_DATA_MOVE1]=*(const u16*)value;
 else if(field>=MON_DATA_PP1 && field<=MON_DATA_PP4)b->pp[field-MON_DATA_PP1]=*(const u8*)value;
}
s32 GetLevelFromBoxMonExp(struct BoxPokemon *b){return b->level;}
'''+struct((ROOT/'include/pokemon.h').read_text(),'BattleMove')+'''
const struct BattleMove gBattleMoves[MOVES_COUNT]={0};
#include "src/data/pokemon/level_up_learnsets.h"
#include "src/data/pokemon/level_up_learnset_pointers.h"
static u16 GiveMoveToBoxMon(struct BoxPokemon *,u16);
static void DeleteFirstMoveAndGiveMoveToBoxMon(struct BoxPokemon *,u16);
'''+ '\n'.join(function(src,n) for n in FUNCTIONS)+'''
int main(void){for(int species=0;species<NUM_SPECIES;species++)for(int level=1;level<=100;level++){
 struct BoxPokemon b={.species=species,.level=level}; GiveBoxMonInitialMoveset(&b);
 printf("%d %d %u %u %u %u\\n",species,level,b.moves[0],b.moves[1],b.moves[2],b.moves[3]);}return 0;}
'''
    with tempfile.TemporaryDirectory(prefix='roster-native-') as t:
        c=Path(t)/'native.c';exe=Path(t)/'native';c.write_text(text)
        subprocess.run(['clang','-std=gnu11','-Werror','-DFIRERED','-DENGLISH','-DREVISION=0','-DMODERN=0','-I',str(ROOT),str(c),'-o',str(exe)],check=True)
        lines=subprocess.check_output([str(exe)],text=True).splitlines()
    for line in lines:
        s,l,*moves=map(int,line.split())
        if moves!=initial_moves(data['species'][s]['learnset'],l):raise ValueError('native default disagreement')
    return {'passed':True,'cases':len(lines),'functions':FUNCTIONS,'sourceSHA256':file_hash(ROOT/'src/pokemon.c'),'substitutes':'Box data accessor/level/PP metadata only; actual extracted source functions and source learnsets','notTested':'encrypted constructor/personality/EV/save/battle execution'}
if __name__=='__main__':
    data=json.loads((ROOT/'config/roster_catalog.json').read_text());result=verify(data)
    (ROOT/'evidence/phase3/roster01/native-default-moves.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

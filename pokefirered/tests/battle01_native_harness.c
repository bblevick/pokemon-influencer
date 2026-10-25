/* Compile actual rules and the unchanged source move helper on host, not an emulator. */
#include "global.h"
#include "battle.h"
#include "pokemon.h"
#include "battle_util.h"
#include "battle_anim.h"
#include "battle_ai_switch_items.h"
#include "pi_battle.h"
#include "pi_events.h"
#include "pi_preparation.h"
#include "battle_controllers.h"
#include "item.h"
#include "constants/battle.h"
#include "constants/pokemon.h"
#include "constants/moves.h"
#include "constants/species.h"
#include "constants/abilities.h"
#include "constants/items.h"
#include "constants/hold_effects.h"
#include "constants/item_effects.h"
#include "constants/battle_move_effects.h"
#include <stdio.h>
#include <assert.h>
typedef char AssertStateOffset[(offsetof(struct PiBattleControl,state)==36)?1:-1];
typedef char AssertReplyOffset[(offsetof(struct PiBattleControl,response)==40)?1:-1];
/* Host Clang pads PiBattleEvent to14; ARM agbcc ABI16 is checked from actual ROM constants. */
typedef char AssertActionsOffset[(offsetof(struct PiBattleSnapshot,actions)==340)?1:-1];
typedef char AssertHistoryOffset[(offsetof(struct PiBattleSnapshot,history)==452)?1:-1];
struct BattlePokemon gBattleMons[4];struct DisableStruct gDisableStructs[4];
struct SideTimer gSideTimers[2];struct BattleStruct bs;struct BattleStruct *gBattleStruct=&bs;
struct BattleHistory history;struct BattleResources resources;struct BattleResources *gBattleResources=&resources;
struct Pokemon gEnemyParty[6];u16 gBattlerPartyIndexes[4];u8 gActiveBattler,gBattlersCount=2,gPotentialItemEffectBattler;
u32 gStatuses3[4];u16 gLastMoves[4];
const u32 gBitTable[]={1,2,4,8};struct BattleEnigmaBerry gEnigmaBerries[4];
struct SaveBlock1 save;struct SaveBlock1 *gSaveBlock1Ptr=&save;
#include "data/battle_moves.h"
#include "data/pokemon/item_effects.h"
struct Slot {u16 species,hp;};struct Slot slots[6];
u32 GetMonData(struct Pokemon *p,s32 field,u8 *dst){u32 i=p-gEnemyParty;if(field==MON_DATA_SPECIES_OR_EGG)return slots[i].species;if(field==MON_DATA_HP)return slots[i].hp;return 0;}
u32 GetMonData2(struct Pokemon *p,s32 field){return GetMonData3(p,field,NULL);}
u8 GetBattlerSide(u8 b){return b&1;}
u8 ItemId_GetHoldEffect(u16 item){return item==ITEM_CHOICE_BAND?HOLD_EFFECT_CHOICE_BAND:0;}
u8 GetItemEffectParamOffset(u16 item,u8 byte,u8 bit){return 6;}
#define ALL_MOVES_MASK 15
struct ProtectStruct gProtectStructs[4];const u8 *gSelectionBattleScripts[4];u8 gBattleBufferB[4][0x200];const u8 BattleScript_NoMovesLeft[]={0};
u8 GetBattlerAtPosition(u8 p){return p;}u16 Random(void){assert(0);return 0;} /* double RNG path never qualified */
/* ENGINE_HELPERS inserted by Python from the actual pinned battle_util.c. */
struct PiBattleWork fixtureWork;volatile struct PiBattleControl gPiBattle;volatile struct PiEventMailbox gPiMailbox;volatile struct PiPreparationMailbox gPiPreparation;
u16 gTrainerBattleOpponent_A=102,gBattleWeather;u32 gBattleTypeFlags=BATTLE_TYPE_TRAINER;u8 gBattleOutcome;
const struct SpeciesInfo gSpeciesInfo[NUM_SPECIES]={[SPECIES_WEEDLE]={.types={TYPE_BUG,TYPE_POISON}},[SPECIES_CATERPIE]={.types={TYPE_BUG,TYPE_BUG}}};
u8 emittedKind;u16 emittedValue;u32 emissions;
void BtlController_EmitTwoReturnValues(u8 buffer,u8 kind,u16 value){emittedKind=kind;emittedValue=value;emissions++;}
void BtlController_EmitChosenMonReturnValue(u8 buffer,u8 slot,u8 *p){emittedKind=99;emittedValue=slot;emissions++;}
u8 GetBattlerPosition(u8 b){return b;}
u8 CalculatePPWithBonus(u16 move,u8 bonus,u8 slot){return gBattleMoves[move].pp;}
static struct PiBattleWork *Work(void){return &fixtureWork;}

/* PROJECT_RULES inserted from the actual compiled overlay through Capture boundary. */
static void reset(void){u8 i;memset(&bs,0,sizeof(bs));memset(gBattleMons,0,sizeof(gBattleMons));memset(gDisableStructs,0,sizeof(gDisableStructs));memset(gStatuses3,0,sizeof(gStatuses3));memset(&history,0,sizeof(history));memset(slots,0,sizeof(slots));memset(gLastMoves,0,sizeof(gLastMoves));memset(gSideTimers,0,sizeof(gSideTimers));resources.battleHistory=&history;bs.monToSwitchIntoId[1]=6;gBattlerPartyIndexes[1]=0;gBattleMons[1].moves[0]=MOVE_TACKLE;gBattleMons[1].moves[1]=MOVE_STRING_SHOT;gBattleMons[1].pp[0]=35;gBattleMons[1].pp[1]=40;gBattleMons[1].hp=10;gBattleMons[1].maxHP=20;for(i=0;i<8;i++)gBattleMons[1].statStages[i]=6;slots[0].species=SPECIES_WEEDLE;slots[0].hp=10;slots[1].species=SPECIES_CATERPIE;slots[1].hp=20;}
static u8 count(u8 kind,u8 phase){struct PiBattleSnapshot s;u8 i,n=0;memset(&s,0,sizeof(s));PiBattle_Enumerate(&s,phase,1);for(i=0;i<s.count;i++)if(s.actions[i].kind==kind)n++;return n;}
/* LIFECYCLE inserted from the actual project wrapper. */
int main(void){u8 type,flags;
/* Gate repair: exact native frame boundary, no hosted provider. */
gActiveBattler=1;gPiBattle.pointer=1;gPiPreparation.state=3;
{u16 elapsed[4]={30,179,181,600};u8 i;for(i=0;i<4;i++){
 reset();gPiBattle.state=0;gPiMailbox.heartbeat=100;assert(PiBattle_Select(PB_NORMAL)==1);
 gPiMailbox.heartbeat+=elapsed[i];gPiBattle.response=gPiBattle.request;gPiBattle.selected=0x100;gPiBattle.state=2;
 if(elapsed[i]<180){assert(PiBattle_Select(PB_NORMAL)==2 && fixtureWork.lastSource==1);assert(PiBattle_Move());}
 else{assert(PiBattle_Select(PB_NORMAL)==0 && fixtureWork.lastSource==2);assert(!PiBattle_Move());}
}}
reset();gPiBattle.state=0;gPiMailbox.heartbeat=100;assert(PiBattle_Select(PB_NORMAL)==1);gPiMailbox.heartbeat+=179;assert(PiBattle_Select(PB_NORMAL)==1);gPiMailbox.heartbeat++;assert(PiBattle_Select(PB_NORMAL)==0 && fixtureWork.lastSource==2);
reset();assert(count(1,PB_NORMAL)==2);assert(count(2,PB_NORMAL)==1);assert(count(3,PB_NORMAL)==0);
gBattleMons[1].pp[0]=0;assert(count(1,PB_NORMAL)==1);reset();gDisableStructs[1].disabledMove=MOVE_TACKLE;assert(count(1,PB_NORMAL)==1);reset();gDisableStructs[1].tauntTimer=1;assert(count(1,PB_NORMAL)==1);reset();gDisableStructs[1].encoreTimer=1;gDisableStructs[1].encoredMove=MOVE_STRING_SHOT;assert(count(1,PB_NORMAL)==1);reset();gLastMoves[1]=MOVE_TACKLE;gBattleMons[1].status2=STATUS2_TORMENT;assert(count(1,PB_NORMAL)==1);reset();gStatuses3[0]=STATUS3_IMPRISONED_OTHERS;gBattleMons[0].moves[0]=MOVE_TACKLE;assert(count(1,PB_NORMAL)==1);reset();gBattleMons[1].item=ITEM_CHOICE_BAND;bs.choicedMove[1]=MOVE_STRING_SHOT;assert(count(1,PB_NORMAL)==1);reset();gBattleMons[1].pp[0]=gBattleMons[1].pp[1]=0;assert(count(1,PB_NORMAL)==0 && count(5,PB_NORMAL)==1);reset();gBattleMons[1].status1=STATUS1_SLEEP;assert(count(1,PB_NORMAL)==2);
reset();gBattleMons[1].status2=STATUS2_WRAPPED;assert(count(2,PB_NORMAL)==0 && count(4,PB_REPLACE)==1);reset();gStatuses3[1]=STATUS3_ROOTED;assert(count(2,PB_NORMAL)==0);reset();gBattleMons[0].ability=ABILITY_SHADOW_TAG;assert(count(2,PB_NORMAL)==0);reset();gBattleMons[0].ability=ABILITY_ARENA_TRAP;assert(count(2,PB_NORMAL)==0);gBattleMons[1].type1=TYPE_FLYING;assert(count(2,PB_NORMAL)==1);reset();gBattleMons[0].ability=ABILITY_MAGNET_PULL;gBattleMons[1].type1=TYPE_STEEL;assert(count(2,PB_NORMAL)==0);reset();slots[1].hp=0;assert(count(2,PB_NORMAL)==0 && count(4,PB_REPLACE)==0);reset();slots[1].species=SPECIES_EGG;assert(count(4,PB_REPLACE)==0);reset();slots[2].species=SPECIES_KAKUNA;slots[2].hp=12;assert(count(4,PB_REPLACE)==2);
reset();history.trainerItems[0]=ITEM_POTION;assert(PiBattle_Item(1,0,&type,&flags) && type==AI_ITEM_HEAL_HP);gBattleMons[1].hp=20;assert(!PiBattle_Item(1,0,&type,&flags));history.trainerItems[0]=ITEM_ANTIDOTE;assert(!PiBattle_Item(1,0,&type,&flags));gBattleMons[1].status1=STATUS1_POISON;assert(PiBattle_Item(1,0,&type,&flags) && flags==0x10);history.trainerItems[0]=ITEM_X_ATTACK;assert(PiBattle_Item(1,0,&type,&flags));gBattleMons[1].statStages[STAT_ATK]=12;assert(!PiBattle_Item(1,0,&type,&flags));history.trainerItems[0]=ITEM_GUARD_SPEC;assert(PiBattle_Item(1,0,&type,&flags));gSideTimers[1].mistTimer=2;assert(!PiBattle_Item(1,0,&type,&flags));history.trainerItems[0]=ITEM_RARE_CANDY;assert(!PiBattle_Item(1,0,&type,&flags));history.trainerItems[0]=0;assert(!PiBattle_Item(1,0,&type,&flags));
reset();gActiveBattler=1;gPiBattle.pointer=1;gPiPreparation.state=3;gPiMailbox.nonce=7;gPiMailbox.generation=1;gPiMailbox.battle_id=3;gPiMailbox.turn_id=1;gPiMailbox.heartbeat=100;gPiBattle.state=0;
assert(PiBattle_Select(PB_NORMAL)==1);gPiBattle.selected=0x100;gPiBattle.response=gPiBattle.request;gPiBattle.state=2;assert(PiBattle_Select(PB_NORMAL)==2 && emittedKind==B_ACTION_USE_MOVE);assert(PiBattle_Move() && emittedKind==10 && (emittedValue&255)==0);assert(!PiBattle_Move());
gPiBattle.state=0;assert(PiBattle_Select(PB_NORMAL)==1);gPiBattle.selected=0x201;gPiBattle.response=gPiBattle.request;gPiBattle.state=2;assert(PiBattle_Select(PB_NORMAL)==2 && emittedKind==B_ACTION_SWITCH && bs.monToSwitchIntoId[1]==1);
reset();gPiBattle.state=0;history.trainerItems[0]=ITEM_POTION;assert(PiBattle_Select(PB_NORMAL)==1);gPiBattle.selected=0x300;gPiBattle.response=gPiBattle.request;gPiBattle.state=2;assert(PiBattle_Select(PB_NORMAL)==2 && emittedKind==B_ACTION_USE_ITEM && !history.trainerItems[0] && bs.chosenItem[0]==ITEM_POTION);assert(count(3,PB_NORMAL)==0);
reset();gPiBattle.state=0;assert(PiBattle_Select(PB_NORMAL)==1);gPiBattle.response=gPiBattle.request;gPiBattle.selected=0xbeef;gPiBattle.state=2;assert(PiBattle_Select(PB_NORMAL)==0 && fixtureWork.lastSource==2);
gPiBattle.state=0;assert(PiBattle_Select(PB_NORMAL)==1);gPiBattle.response=gPiBattle.request;gPiBattle.selected=0x100;gPiBattle.state=2;gPiBattle.hash^=1;assert(PiBattle_Select(PB_NORMAL)==0);
gPiBattle.state=0;assert(PiBattle_Select(PB_NORMAL)==1);gPiBattle.response=gPiBattle.request;gPiBattle.selected=0x100;gPiBattle.state=2;gPiMailbox.turn_id++;assert(PiBattle_Select(PB_NORMAL)==0);
gPiBattle.state=0;assert(PiBattle_Select(PB_NORMAL)==1);gPiMailbox.heartbeat=gPiBattle.deadline;assert(PiBattle_Select(PB_NORMAL)==0 && gPiBattle.state==5);gPiBattle.response=gPiBattle.request;gPiBattle.selected=0x100;gPiBattle.state=2;gPiMailbox.generation++;assert(PiBattle_Select(PB_NORMAL)==0);
reset();gPiBattle.state=0;gPiMailbox.generation=1;gPiMailbox.heartbeat=100;slots[2].species=SPECIES_KAKUNA;slots[2].hp=12;bs.AI_monToSwitchIntoId[0]=PARTY_SIZE;
assert(PiBattle_Select(PB_REPLACE)==1);assert(fixtureWork.snapshot.count==2);gPiBattle.selected=0x402;gPiBattle.response=gPiBattle.request;gPiBattle.state=2;assert(PiBattle_Select(PB_REPLACE)==2 && emittedKind==99 && emittedValue==2);
reset();gPiBattle.state=0;gPiMailbox.heartbeat=100;assert(PiBattle_Select(PB_NORMAL)==1);gPiBattle.response=gPiBattle.request;gPiBattle.selected=0x100;gPiBattle.state=2;gPiMailbox.battle_id++;assert(PiBattle_Select(PB_NORMAL)==0);
gPiBattle.state=0;assert(PiBattle_Select(PB_NORMAL)==1);gPiBattle.response=gPiBattle.request;gPiBattle.selected=0x100;gPiBattle.state=2;gPiMailbox.heartbeat=gPiBattle.deadline;assert(PiBattle_Select(PB_NORMAL)==0 && fixtureWork.lastSource==2);
gPiBattle.state=0;gBattleTypeFlags=BATTLE_TYPE_TRAINER|BATTLE_TYPE_DOUBLE;assert(PiBattle_Select(PB_NORMAL)==0);gBattleTypeFlags=BATTLE_TYPE_TRAINER|BATTLE_TYPE_LINK;assert(PiBattle_Select(PB_NORMAL)==0);gBattleTypeFlags=BATTLE_TYPE_TRAINER|BATTLE_TYPE_IS_MASTER;gPiBattle.state=0;gPiMailbox.heartbeat=100;assert(PiBattle_Select(PB_NORMAL)==1);gPiMailbox.nonce++;gPiBattle.response=gPiBattle.request;gPiBattle.selected=0x100;gPiBattle.state=2;assert(PiBattle_Select(PB_NORMAL)==0);
reset();gPiBattle.state=0;gPiMailbox.heartbeat=100;gBattleTypeFlags=BATTLE_TYPE_TRAINER;{struct PiBattleSnapshot a,b;gBattleMons[0].hp=25;gBattleMons[0].maxHP=50;Capture(&a,PB_NORMAL,1);gBattleMons[0].attack=500;gBattleMons[0].defense=500;gBattleMons[0].item=ITEM_LEFTOVERS;gBattleMons[0].moves[0]=MOVE_SURF;gBattleMons[0].hp=50;gBattleMons[0].maxHP=100;Capture(&b,PB_NORMAL,1);assert(Hash(&a,sizeof(a))==Hash(&b,sizeof(b)));}
reset();gPiBattle.state=0;gPiMailbox.heartbeat=100;gBattleMons[1].pp[0]=gBattleMons[1].pp[1]=0;slots[1].hp=0;assert(PiBattle_Select(PB_NORMAL)==2 && fixtureWork.lastSource==3 && gPiBattle.selected==0x500 && emittedKind==B_ACTION_USE_MOVE);assert(!PiBattle_Move());assert(AreAllMovesUnusable() && gProtectStructs[1].noValidMoves && gSelectionBattleScripts[1]==BattleScript_NoMovesLeft);
puts("native legality and controller execution/lifecycle matrix passed");return 0;}

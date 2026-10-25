/* Source-pinned ordinary single trainer controller boundary; no inference. */
#include "global.h"
#include "pi_battle.h"
#include "pi_events.h"
#include "pi_preparation.h"
#include "pi_build.h"
#include "battle.h"
#include "battle_main.h"
#include "battle_anim.h"
#include "battle_util.h"
#include "battle_controllers.h"
#include "battle_ai_switch_items.h"
#include "pokemon.h"
#include "item.h"
#include "data.h"
#include "malloc.h"
#include "constants/battle.h"
#include "constants/pokemon.h"
#include "constants/abilities.h"
#include "constants/items.h"
#include "constants/item_effects.h"
#include "constants/moves.h"
volatile struct PiBattleControl gPiBattle __attribute__((section("pi_mailbox_data"),aligned(4)))={0};
static struct PiBattleWork *Work(void){return (struct PiBattleWork *)gPiBattle.pointer;}
static u32 Hash(const void *p,u32 size){u32 h=2166136261u,i;const u8 *b=p;for(i=0;i<size;i++)h=(h^b[i])*16777619u;return h;}
/* Default remains the accepted controlled Rick profile. Campaign builds opt in
 * to Brock's actual native singles encounter; the host still requires a lock. */
static bool8 QualifiedTrainer(void)
{
#ifdef PI_CAMPAIGN_BROCK
 if (gTrainerBattleOpponent_A == 414) return TRUE;
#endif
 return gTrainerBattleOpponent_A == 102 && gPiPreparation.state == 3;
}
void PiBattle_PartyConstructed(u16 trainer)
{
#ifdef PI_CAMPAIGN_BROCK
 if (trainer == 414 && (gBattleTypeFlags & BATTLE_TYPE_TRAINER)
  && !(gBattleTypeFlags & ~(BATTLE_TYPE_TRAINER|BATTLE_TYPE_IS_MASTER)))
  gPiPreparation.installations++;
#endif
}
static bool8 Supported(void){return (gBattleTypeFlags & ~(BATTLE_TYPE_TRAINER|BATTLE_TYPE_IS_MASTER))==0 && (gBattleTypeFlags&BATTLE_TYPE_TRAINER) && gBattlersCount==2 && QualifiedTrainer() && gPiBattle.pointer && !gBattleOutcome;}
bool8 PiBattle_SwitchAllowed(u8 b)
{
 u8 foe=b^BIT_SIDE;
 if(gBattleMons[b].status2&(STATUS2_WRAPPED|STATUS2_ESCAPE_PREVENTION) || gStatuses3[b]&STATUS3_ROOTED)return FALSE;
 /* Selection/run restriction, not ShouldSwitch's preference and Arena Trap bug. */
 if(gBattleMons[foe].ability==ABILITY_SHADOW_TAG)return FALSE;
 if(gBattleMons[foe].ability==ABILITY_ARENA_TRAP && gBattleMons[b].ability!=ABILITY_LEVITATE && gBattleMons[b].type1!=TYPE_FLYING && gBattleMons[b].type2!=TYPE_FLYING)return FALSE;
 /* Pinned field-wide Magnet Pull behavior, including allied-side ability. */
 if((gBattleMons[b].ability==ABILITY_MAGNET_PULL || gBattleMons[foe].ability==ABILITY_MAGNET_PULL) && (gBattleMons[b].type1==TYPE_STEEL || gBattleMons[b].type2==TYPE_STEEL))return FALSE;
 return TRUE;
}
bool8 PiBattle_Item(u8 b,u8 slot,u8 *type,u8 *flags)
{
 u16 item;const u8 *e;u32 status=gBattleMons[b].status1;
 *type=AI_ITEM_NOT_RECOGNIZABLE;*flags=0;if(slot>=MAX_TRAINER_ITEMS)return FALSE;item=gBattleResources->battleHistory->trainerItems[slot];
 if(slot>=MAX_TRAINER_ITEMS || item<ITEM_POTION || item>ITEM_ENIGMA_BERRY || !gBattleMons[b].hp)return FALSE;
 e=gItemEffectTable[item-ITEM_POTION];if(!e)return FALSE;
 if(item==ITEM_ENIGMA_BERRY)e=gSaveBlock1Ptr->enigmaBerry.itemEffect;
 if(item==ITEM_FULL_RESTORE){*type=AI_ITEM_FULL_RESTORE;return gBattleMons[b].hp<gBattleMons[b].maxHP || status || gBattleMons[b].status2&STATUS2_CONFUSION;}
 if(e[4]&ITEM4_HEAL_HP && !(e[4]&ITEM4_REVIVE)){*type=AI_ITEM_HEAL_HP;return GetItemEffectParamOffset(item,4,4)!=0 && gBattleMons[b].hp<gBattleMons[b].maxHP;}
 if(e[3]&ITEM3_STATUS_ALL){
  *type=AI_ITEM_CURE_CONDITION;
  if(e[3]&ITEM3_SLEEP && status&STATUS1_SLEEP)*flags|=0x20;
  if(e[3]&ITEM3_POISON && status&(STATUS1_POISON|STATUS1_TOXIC_POISON))*flags|=0x10;
  if(e[3]&ITEM3_BURN && status&STATUS1_BURN)*flags|=8;
  if(e[3]&ITEM3_FREEZE && status&STATUS1_FREEZE)*flags|=4;
  if(e[3]&ITEM3_PARALYSIS && status&STATUS1_PARALYSIS)*flags|=2;
  if(e[3]&ITEM3_CONFUSION && gBattleMons[b].status2&STATUS2_CONFUSION)*flags|=1;
  return *flags!=0;
 }
 if(e[0]&(ITEM0_DIRE_HIT|ITEM0_X_ATTACK) || e[1] || e[2]){
  *type=AI_ITEM_X_STAT;
  if(e[0]&ITEM0_X_ATTACK && gBattleMons[b].statStages[STAT_ATK]<MAX_STAT_STAGE)*flags|=1;
  if(e[1]&ITEM1_X_DEFEND && gBattleMons[b].statStages[STAT_DEF]<MAX_STAT_STAGE)*flags|=2;
  if(e[1]&ITEM1_X_SPEED && gBattleMons[b].statStages[STAT_SPEED]<MAX_STAT_STAGE)*flags|=4;
  if(e[2]&ITEM2_X_SPATK && gBattleMons[b].statStages[STAT_SPATK]<MAX_STAT_STAGE)*flags|=8;
  if(e[2]&ITEM2_X_ACCURACY && gBattleMons[b].statStages[STAT_ACC]<MAX_STAT_STAGE)*flags|=0x20;
  if(e[0]&ITEM0_DIRE_HIT && !(gBattleMons[b].status2&STATUS2_FOCUS_ENERGY))*flags|=0x80;
  return *flags!=0;
 }
 if(e[3]&ITEM3_GUARD_SPEC){*type=AI_ITEM_GUARD_SPECS;return gSideTimers[GetBattlerSide(b)].mistTimer==0;}
 return FALSE;
}
static void Add(struct PiBattleSnapshot *s,u8 kind,u8 slot,u16 value,u8 target,u8 flags)
{
 struct PiBattleAction *a;if(s->count>=PB_ACTIONS)return;
 a=&s->actions[s->count++];a->id=(kind<<8)|slot;a->kind=kind;a->slot=slot;a->value=value;a->target=target;a->flags=flags;
}
u8 PiBattle_Enumerate(struct PiBattleSnapshot *s,u8 phase,u8 b)
{
 u8 i,type,flags,mask,potential=gPotentialItemEffectBattler;u16 species;
 s->count=0;s->phase=phase;s->battler=b;
 if(phase==PB_NORMAL){
  if(gBattleMons[b].status2&(STATUS2_MULTIPLETURNS|STATUS2_RECHARGE))return 0;
  mask=CheckMoveLimitations(b,0,MOVE_LIMITATIONS_ALL);gPotentialItemEffectBattler=potential;s->moveMask=mask;
  for(i=0;i<4;i++)if(!(mask&(1<<i)))Add(s,1,i,gBattleMons[b].moves[i],(gBattleMoves[gBattleMons[b].moves[i]].target&(MOVE_TARGET_USER_OR_SELECTED|MOVE_TARGET_USER))?b:b^BIT_SIDE,0);
  /* Engine owns all-unusable Struggle script; a synthetic id is not a move slot. */
  if(mask==15)Add(s,5,0,MOVE_STRUGGLE,b^BIT_SIDE,0);
 }
 if(phase==PB_REPLACE || PiBattle_SwitchAllowed(b))for(i=0;i<6;i++){
  species=GetMonData(&gEnemyParty[i],MON_DATA_SPECIES_OR_EGG);
  if(species!=SPECIES_NONE && species!=SPECIES_EGG && GetMonData(&gEnemyParty[i],MON_DATA_HP) && i!=gBattlerPartyIndexes[b] && i!=gBattleStruct->monToSwitchIntoId[b])Add(s,phase==PB_REPLACE?4:2,i,species,b,0);
 }
 if(phase==PB_NORMAL)for(i=0;i<4;i++)if(PiBattle_Item(b,i,&type,&flags))Add(s,3,i,gBattleResources->battleHistory->trainerItems[i],type,flags);
 return s->count;
}
static void Capture(struct PiBattleSnapshot *s,u8 phase,u8 b)
{
 u8 i,j,foe=b^BIT_SIDE;struct PiBattleWork *w=Work();memset(s,0,sizeof(*s));
 s->version=1;s->size=sizeof(*s);s->trainer=gTrainerBattleOpponent_A;s->battle=gPiMailbox.battle_id;s->turn=gPiMailbox.turn_id;s->request=gPiBattle.request;s->nonce=gPiMailbox.nonce;s->generation=gPiMailbox.generation;s->activeSlot=gBattlerPartyIndexes[b];
 s->foeSpecies=gBattleMons[foe].species;s->foeHP=gBattleMons[foe].maxHP?(gBattleMons[foe].hp*48+gBattleMons[foe].maxHP-1)/gBattleMons[foe].maxHP:0;s->foeStatus=gBattleMons[foe].status1&0xff;s->weather=gBattleWeather;
 if(gBattlerPartyIndexes[foe]<6)memcpy(s->revealed,w->revealed[gBattlerPartyIndexes[foe]],sizeof(s->revealed));
 for(i=0;i<6;i++){
  struct PiBattleMon *m=&s->own[i];
  m->species=GetMonData(&gEnemyParty[i],MON_DATA_SPECIES);m->level=GetMonData(&gEnemyParty[i],MON_DATA_LEVEL);m->hp=GetMonData(&gEnemyParty[i],MON_DATA_HP);m->maxHP=GetMonData(&gEnemyParty[i],MON_DATA_MAX_HP);m->status=GetMonData(&gEnemyParty[i],MON_DATA_STATUS);m->item=GetMonData(&gEnemyParty[i],MON_DATA_HELD_ITEM);
  if(!m->species)continue;
  m->type1=gSpeciesInfo[m->species].types[0];m->type2=gSpeciesInfo[m->species].types[1];
  for(j=0;j<4;j++){m->moves[j]=GetMonData(&gEnemyParty[i],MON_DATA_MOVE1+j);m->pp[j]=GetMonData(&gEnemyParty[i],MON_DATA_PP1+j);m->maxPP[j]=CalculatePPWithBonus(m->moves[j],GetMonData(&gEnemyParty[i],MON_DATA_PP_BONUSES),j);}
  if(i==s->activeSlot){m->hp=gBattleMons[b].hp;m->status=gBattleMons[b].status1;m->status2=gBattleMons[b].status2;m->status3=gStatuses3[b];m->type1=gBattleMons[b].type1;m->type2=gBattleMons[b].type2;m->ability=gBattleMons[b].ability;memcpy(m->moves,gBattleMons[b].moves,sizeof(m->moves));memcpy(m->pp,gBattleMons[b].pp,4);memcpy(m->stages,gBattleMons[b].statStages,8);}
 }
 memcpy(s->items,gBattleResources->battleHistory->trainerItems,sizeof(s->items));s->historyCount=w->historyCount;memcpy(s->history,w->history,sizeof(s->history));PiBattle_Enumerate(s,phase,b);
}
void PiBattle_Init(void){memset((void *)&gPiBattle,0,sizeof(gPiBattle));gPiBattle.magic=0x50425431;gPiBattle.tag=PI_BUILD_TAG;}
void PiBattle_Start(void)
{
 bool8 armed = gPiBattle.state == 0x8000;
#ifdef PI_CAMPAIGN_BROCK
 if (gTrainerBattleOpponent_A == 414) armed = TRUE;
#endif
#ifdef PI_BATTLE_END_VANILLA
 /* Explicit offline control build only; production activation is unchanged. */
 armed = FALSE;
#endif
 if (!armed) return;
 gPiBattle.state = 0;
 if ((gBattleTypeFlags & ~(BATTLE_TYPE_TRAINER|BATTLE_TYPE_IS_MASTER)) == 0
  && (gBattleTypeFlags & BATTLE_TYPE_TRAINER) && QualifiedTrainer())
  gPiBattle.pointer = (u32)AllocZeroed(sizeof(struct PiBattleWork));
}
void PiBattle_End(void)
{
 /* Copy disposition into the fixed control block before freeing Work.
  * 6 canceled pending; 7 external issued; 8 engine issued; 9 timeout fallback; 10 invalid/stale fallback.
  * No pointer into the freed allocation is retained or read by transport. */
 u16 state=0;
 if(gPiBattle.pointer){
  if(gPiBattle.state==1 || gPiBattle.state==2)state=6;
  else if(gPiBattle.state==4)state=Work()->lastSource==3?8:7;
  else if(gPiBattle.state==5)state=Work()->lastReason==3?10:9;
  Free(Work());
 }
 gPiBattle.pointer=0;gPiBattle.state=state;
}
static u8 Execute(struct PiBattleAction *a,u8 phase)
{
 u8 b=gActiveBattler;struct PiBattleWork *w=Work();w->lastSelected=a->id;
 if(a->kind==1){w->moveSlot=a->slot;w->moveTarget=a->target;w->moveReady=1;BtlController_EmitTwoReturnValues(1,B_ACTION_USE_MOVE,a->target<<8);}
 else if(a->kind==5)BtlController_EmitTwoReturnValues(1,B_ACTION_USE_MOVE,a->target<<8);
 else if(a->kind==2){gBattleStruct->AI_monToSwitchIntoId[GetBattlerPosition(b)>>1]=a->slot;gBattleStruct->monToSwitchIntoId[b]=a->slot;BtlController_EmitTwoReturnValues(1,B_ACTION_SWITCH,0);}
 else if(a->kind==4){gBattleStruct->monToSwitchIntoId[b]=a->slot;BtlController_EmitChosenMonReturnValue(1,a->slot,NULL);}
 else if(a->kind==3){gBattleStruct->AI_itemType[b/2]=a->target;gBattleStruct->AI_itemFlags[b/2]=a->flags;gBattleStruct->chosenItem[(b/2)*2]=a->value;gBattleStruct->chosenItem[(b/2)*2+1]=a->value>>8;gBattleResources->battleHistory->trainerItems[a->slot]=ITEM_NONE;BtlController_EmitTwoReturnValues(1,B_ACTION_USE_ITEM,0);}
 gPiBattle.state=4;return 2;
}
u8 PiBattle_Select(u8 phase)
{
 struct PiBattleWork *w;struct PiBattleSnapshot current;u8 i;
 if(!Supported() || GetBattlerSide(gActiveBattler)!=B_SIDE_OPPONENT)return 0;
 if(phase==PB_REPLACE && gBattleStruct->AI_monToSwitchIntoId[GetBattlerPosition(gActiveBattler)>>1]!=PARTY_SIZE)return 0;
 w=Work();
 if(gPiBattle.state!=1 && gPiBattle.state!=2){
  if(gPiBattle.request==0xffffffffu)return 0;
  gPiBattle.state=0;w->moveReady=0;gPiBattle.request++;Capture(&w->snapshot,phase,gActiveBattler);
  if(!w->snapshot.count){w->lastSource=3;w->lastReason=1;return 0;}
  gPiBattle.hash=Hash(&w->snapshot,sizeof(w->snapshot));gPiBattle.nonce=gPiMailbox.nonce;gPiBattle.generation=gPiMailbox.generation;gPiBattle.battle=gPiMailbox.battle_id;gPiBattle.turn=gPiMailbox.turn_id;gPiBattle.phase=phase;gPiBattle.battler=gActiveBattler;gPiBattle.deadline=gPiMailbox.heartbeat+180;gPiBattle.response=0;gPiBattle.selected=0;
  if(w->snapshot.count==1){gPiBattle.selected=w->snapshot.actions[0].id;w->lastSource=3;w->lastReason=4;return Execute(&w->snapshot.actions[0],phase);}
  gPiBattle.state=1;
 }
 if(gPiBattle.state==2){
  Capture(&current,phase,gActiveBattler);
  if((u32)(gPiMailbox.heartbeat-gPiBattle.deadline)>=0x80000000u && gPiBattle.response==gPiBattle.request && gPiBattle.nonce==gPiMailbox.nonce && gPiBattle.generation==gPiMailbox.generation && gPiBattle.battle==gPiMailbox.battle_id && gPiBattle.turn==gPiMailbox.turn_id && gPiBattle.phase==phase && gPiBattle.battler==gActiveBattler && gPiBattle.hash==Hash(&current,sizeof(current))){
   for(i=0;i<current.count;i++)if(current.actions[i].id==gPiBattle.selected){w->lastSource=1;w->lastReason=0;return Execute(&current.actions[i],phase);}
  }
  w->lastReason=3;
 }else if((u32)(gPiMailbox.heartbeat-gPiBattle.deadline)>=0x80000000u)return 1;
 else w->lastReason=2;
 w->lastSource=2;w->moveReady=0;gPiBattle.state=5;return 0;
}
bool8 PiBattle_Move(void){struct PiBattleWork *w;if(!Supported())return FALSE;w=Work();if(!w->moveReady)return FALSE;w->moveReady=0;BtlController_EmitTwoReturnValues(1,10,w->moveSlot|(w->moveTarget<<8));return TRUE;}
void PiBattle_Reveal(void){u8 i,slot;if(!Supported())return;Work()->actionMove[gBattlerAttacker]=gCurrentMove;if(GetBattlerSide(gBattlerAttacker)!=B_SIDE_PLAYER)return;slot=gBattlerPartyIndexes[gBattlerAttacker];if(slot>=6)return;for(i=0;i<4;i++)if(Work()->revealed[slot][i]==gCurrentMove)return;for(i=0;i<4;i++)if(!Work()->revealed[slot][i]){Work()->revealed[slot][i]=gCurrentMove;return;}}
void PiBattle_Resolved(u8 b,u8 kind){struct PiBattleWork *w;struct PiBattleEvent *e;u8 foe=b^BIT_SIDE;if(!Supported())return;w=Work();if(w->historyCount==PB_HISTORY){memmove(w->history,w->history+1,sizeof(w->history[0])*(PB_HISTORY-1));w->historyCount--;}e=&w->history[w->historyCount++];memset(e,0,sizeof(*e));e->turn=gPiMailbox.turn_id;e->side=GetBattlerSide(b);e->kind=kind;e->move=w->actionMove[b];e->species=gBattleMons[b].species;e->ownHP=gBattleMons[1].hp;e->hpBar=gBattleMons[0].maxHP?(gBattleMons[0].hp*48+gBattleMons[0].maxHP-1)/gBattleMons[0].maxHP:0;e->status=gBattleMons[0].status1&0xff;if(kind==B_ACTION_USE_ITEM)e->item=gLastUsedItem;w->actionMove[b]=0;}

const u32 gPiBattleAbi[]={sizeof(struct PiBattleSnapshot),sizeof(struct PiBattleWork),sizeof(struct PiBattleMon),sizeof(struct PiBattleEvent),offsetof(struct PiBattleSnapshot,own),offsetof(struct PiBattleSnapshot,actions),offsetof(struct PiBattleSnapshot,history),offsetof(struct PiBattleWork,history),offsetof(struct PiBattleWork,lastSource)};

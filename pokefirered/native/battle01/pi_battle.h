#ifndef GUARD_PI_BATTLE_H
#define GUARD_PI_BATTLE_H
#include "global.h"
#include <stddef.h>
#define PB_ACTIONS 14
#define PB_HISTORY 16
#define PB_NORMAL 1
#define PB_REPLACE 2
/* Exactly48 bytes; four bytes remain in the existing reserved EWRAM area. */
struct PiBattleControl {
 u32 magic,tag,request,hash,pointer,nonce,generation,battle;
 u16 turn;u8 phase,battler;u16 state,selected;u32 response,deadline;
};
struct PiBattleAction {u16 id,value;u8 kind,slot,target,flags;};
struct PiBattleMon {
 u16 species,hp,maxHP,item,moves[4];u32 status,status2,status3;
 u8 level,type1,type2,ability,pp[4],maxPP[4],stages[8];
};
struct PiBattleEvent {u16 turn,move,species;u8 side,kind,hpBar,status;u16 ownHP,item;};
struct PiBattleSnapshot {
 u16 version,size,trainer;u8 phase,count;
 u32 battle,request,nonce,generation;
 u16 turn;u8 battler,activeSlot,moveMask,historyCount;u16 foeSpecies;
 u8 foeHP,foeStatus;u16 weather;
 u16 revealed[4],items[4];
 struct PiBattleMon own[6];struct PiBattleAction actions[PB_ACTIONS];
 struct PiBattleEvent history[PB_HISTORY];
};
struct PiBattleWork {
 struct PiBattleSnapshot snapshot;
 struct PiBattleEvent history[PB_HISTORY];
 u16 revealed[6][4],actionMove[4];
 u8 historyCount,moveSlot,moveTarget,moveReady;
 u8 lastSource,lastReason;u16 lastSelected;
 u32 terminalRequest,terminalHash;
};
typedef char PiBattleControlSize[(sizeof(struct PiBattleControl)==48)?1:-1];
typedef char PiBattleActionSize[(sizeof(struct PiBattleAction)==8)?1:-1];
extern volatile struct PiBattleControl gPiBattle;
void PiBattle_Init(void);
void PiBattle_Start(void);
void PiBattle_PartyConstructed(u16 trainer);
void PiBattle_End(void);
u8 PiBattle_Select(u8 phase); /*0 vanilla,1 pending,2 emitted external/sole*/
bool8 PiBattle_Move(void);
void PiBattle_Reveal(void);
void PiBattle_Resolved(u8 actor,u8 kind);
u8 PiBattle_Enumerate(struct PiBattleSnapshot *s,u8 phase,u8 battler);
bool8 PiBattle_SwitchAllowed(u8 battler);
bool8 PiBattle_Item(u8 battler,u8 slot,u8 *type,u8 *flags);
#endif

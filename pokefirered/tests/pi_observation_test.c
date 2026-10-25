#include "pi_events.h"
#include "battle.h"
#include "constants/battle.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
u32 gBattleTypeFlags=8;
u16 gTrainerBattleOpponent_A=101,gBattlerPartyIndexes[4]={0,0},gCurrentMove=33;
u8 gBattlersCount=2,gBattlerAttacker=0,gBattleOutcome=1;
struct BattlePokemon gBattleMons[4];
u8 GetBattlerAtPosition(u8 p){return p&1;}
u8 GetBattlerSide(u8 b){return b&1;}
bool32 HasTrainerBeenFought(u16 trainer){return trainer==0;}
static u32 sum(void){u32 h=2166136261u,words[4],i,j;words[0]=gPiMailbox.sequence;words[1]=gPiMailbox.nonce;words[2]=gPiMailbox.generation;words[3]=4;for(i=0;i<4;i++)for(j=0;j<4;j++)h=(h^((words[i]>>(j*8))&255))*16777619u;return h;}
static void ack(void){gPiMailbox.response_sequence=gPiMailbox.sequence;gPiMailbox.response_nonce=gPiMailbox.nonce;gPiMailbox.response_generation=gPiMailbox.generation;gPiMailbox.message_type=4;gPiMailbox.length=0;gPiMailbox.checksum=sum();gPiMailbox.state=3;PiBridge_Tick();}
static void observation(u8 *bytes){PiBridge_Init();PiEvents_BattleStart();PiEvents_Turn();PiBridge_Tick();ack();ack();assert(gPiMailbox.payload[2]==6 && gPiMailbox.length==64);memcpy(bytes,(const void *)(gPiMailbox.payload+24),40);}
int main(void)
{
    u8 first[40],second[40];
    gBattleMons[0].species=1;gBattleMons[0].hp=10;gBattleMons[0].maxHP=20;gBattleMons[0].moves[0]=33;
    gBattleMons[1].species=10;gBattleMons[1].hp=15;gBattleMons[1].maxHP=20;gBattleMons[1].moves[0]=33;gBattleMons[1].pp[0]=10;
    observation(first);gBattleMons[0].moves[0]=999;gBattleMons[0].status1=255;gBattleMons[3].species=999;observation(second);
    assert(!memcmp(first,second,40));puts("PASS hidden move/status/unused battler counterfactual leaves observation unchanged");
    assert(first[28]==0 && first[29]==0);puts("PASS unrevealed player moves absent");
    PiEvents_Reveal();ack();PiEvents_NextTurn();PiEvents_Turn();PiBridge_Tick();ack();assert(gPiMailbox.payload[2]==6 && gPiMailbox.payload[24+28]==33);puts("PASS public announcement authorizes only revealed move");
    assert(gPiMailbox.payload[24+26]==24 && gPiMailbox.payload[24+27]==0);puts("PASS public HP coarse and legal actions incomplete");
    ack();PiEvents_End();PiBridge_Tick();assert(gPiMailbox.payload[2]==4);ack();assert(gPiMailbox.payload[2]==5);puts("PASS victory trainer defeat precedes battle ended");
    PiBridge_Init();gBattleTypeFlags=BATTLE_TYPE_POKEDUDE;PiEvents_BattleStart();assert(gPiMailbox.battle_id==0 && gPiMailbox.event_counter==0);puts("PASS Poke Dude tutorial excluded by supported-flags allowlist");
    gBattleTypeFlags=8;PiEvents_BattleStart();gPiMailbox.turn_id=65535;PiEvents_NextTurn();PiEvents_Turn();PiEvents_Action(0,0);PiEvents_End();assert(gPiMailbox.event_counter==1 && gPiMailbox.drops==1);puts("PASS turn exhaustion disables encounter export without identity reuse");
    puts("7 actual C gameplay observation cases passed");return 0;
}

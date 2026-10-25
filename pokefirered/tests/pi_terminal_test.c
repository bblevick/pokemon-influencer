#include "pi_events.h"
#include "battle.h"
#include "constants/battle.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
u32 gBattleTypeFlags=8;
u16 gTrainerBattleOpponent_A=414,gBattlerPartyIndexes[4]={0,0},gCurrentMove=33;
u8 gBattlersCount=2,gBattlerAttacker=0,gBattleOutcome=0;
struct BattlePokemon gBattleMons[4];
u8 GetBattlerAtPosition(u8 p){return p&1;}u8 GetBattlerSide(u8 b){return b&1;}
bool32 HasTrainerBeenFought(u16 trainer){return trainer==0;}
static u32 sum(void){u32 h=2166136261u,words[4],i,j;words[0]=gPiMailbox.sequence;words[1]=gPiMailbox.nonce;words[2]=gPiMailbox.generation;words[3]=4;for(i=0;i<4;i++)for(j=0;j<4;j++)h=(h^((words[i]>>(j*8))&255))*16777619u;return h;}
static void ack(void){gPiMailbox.response_sequence=gPiMailbox.sequence;gPiMailbox.response_nonce=gPiMailbox.nonce;gPiMailbox.response_generation=gPiMailbox.generation;gPiMailbox.message_type=4;gPiMailbox.length=0;gPiMailbox.checksum=sum();gPiMailbox.state=3;PiBridge_Tick();}
int main(void){
 u32 i,seq;u8 copy[28];
 PiBridge_Init();PiEvents_BattleStart();PiBridge_Tick();ack();gBattleOutcome=B_OUTCOME_WON;PiEvents_End();PiEvents_End();assert(gPiMailbox.queue_depth==2);PiBridge_Tick();assert(gPiMailbox.payload[2]==4);ack();assert(gPiMailbox.payload[2]==5 && gPiMailbox.payload[27]==1);puts("PASS exactly one source-native victory terminal");
 seq=gPiMailbox.sequence;memcpy(copy,(const void*)gPiMailbox.payload,28);memset(gBattleMons,0,sizeof(gBattleMons));for(i=0;i<1200;i++)PiBridge_Tick();assert(gPiMailbox.sequence==seq && gPiMailbox.queue_depth==1 && !memcmp(copy,(const void*)gPiMailbox.payload,28) && !gPiMailbox.drops);puts("PASS stable terminal after cleanup and long host absence");
 ack();assert(gPiMailbox.last_ack==seq && !gPiMailbox.queue_depth);puts("PASS delayed matching ACK retires terminal");
 PiBridge_Init();gBattleOutcome=B_OUTCOME_LOST;PiEvents_BattleStart();PiBridge_Tick();ack();PiEvents_End();PiBridge_Tick();assert(gPiMailbox.queue_depth==1 && gPiMailbox.payload[2]==5 && gPiMailbox.payload[27]==2);puts("PASS player defeat terminal without trainer-defeated reward");
 seq=gPiMailbox.sequence;gPiMailbox.state=PI_STATE_ERROR;gPiMailbox.error=PI_ERR_DISCONNECTED;PiBridge_Tick();assert(gPiMailbox.sequence==seq && gPiMailbox.payload[27]==2);ack();assert(!gPiMailbox.queue_depth);puts("PASS reconnect retry preserves exact sequence/outcome");
 PiBridge_Init();gPiMailbox.battle_id=1;for(i=0;i<4;i++)PiEvents_Enqueue(2,1,NULL,0);{u8 data[4]={158,1,1,1};PiEvents_Enqueue(4,3,data,4);PiEvents_Enqueue(5,3,data,4);}assert(gPiMailbox.queue_depth==4 && gPiMailbox.drops==2);PiBridge_Tick();ack();ack();assert(gPiMailbox.payload[2]==4);ack();assert(gPiMailbox.payload[2]==5);ack();assert(!gPiMailbox.queue_depth);puts("PASS terminal reservation preserves defeat and end under backpressure");
 PiBridge_Init();assert(!gPiMailbox.queue_depth && !gPiMailbox.event_counter);puts("PASS explicit reset clears transient identities");
 puts("7 actual-C terminal cases passed (game globals stubbed)");return 0;
}

#include "global.h"
#if PI_EVENTS
#include "pi_events.h"
#include "pi_build.h"
#ifndef PI_EVENTS_NATIVE_TEST
#include "battle.h"
#include "battle_anim.h"
#include "battle_setup.h"
#include "constants/battle.h"
#endif

#define PI_ALLOC __attribute__((section("pi_mailbox_data"), aligned(4)))
const u32 gPiBuildTag = PI_BUILD_TAG;
/* Generated offsets are checked against actual compiler output by the builder. */
const u32 gPiCompiledLayout[] = {sizeof(struct PiEventMailbox),
    offsetof(struct PiEventMailbox, magic), offsetof(struct PiEventMailbox, version),
    offsetof(struct PiEventMailbox, size), offsetof(struct PiEventMailbox, build_tag),
    offsetof(struct PiEventMailbox, nonce), offsetof(struct PiEventMailbox, generation),
    offsetof(struct PiEventMailbox, sequence), offsetof(struct PiEventMailbox, response_sequence),
    offsetof(struct PiEventMailbox, response_nonce), offsetof(struct PiEventMailbox, response_generation),
    offsetof(struct PiEventMailbox, state), offsetof(struct PiEventMailbox, message_type),
    offsetof(struct PiEventMailbox, length), offsetof(struct PiEventMailbox, result),
    offsetof(struct PiEventMailbox, error), offsetof(struct PiEventMailbox, reserved),
    offsetof(struct PiEventMailbox, checksum), offsetof(struct PiEventMailbox, heartbeat),
    offsetof(struct PiEventMailbox, deadline), offsetof(struct PiEventMailbox, last_ack),
    offsetof(struct PiEventMailbox, successes), offsetof(struct PiEventMailbox, failures),
    offsetof(struct PiEventMailbox, debug_trigger), offsetof(struct PiEventMailbox, event_counter),
    offsetof(struct PiEventMailbox, drops), offsetof(struct PiEventMailbox, retries),
    offsetof(struct PiEventMailbox, queue_depth), offsetof(struct PiEventMailbox, battle_id),
    offsetof(struct PiEventMailbox, turn_id), offsetof(struct PiEventMailbox, payload)};
volatile struct PiEventMailbox gPiMailbox PI_ALLOC = {0};
struct PiRecord {u16 length; u8 data[PI_PAYLOAD_MAX];};
struct PiEventState {
    struct PiRecord queue[4];
    u32 battleFlags;
    u16 trainer;
    u16 revealed[6][4];
    u16 actionMove[4];
    u8 head, count, attempt, active, supported, firstWin, turnReady;
};
static struct PiEventState sPiEvents PI_ALLOC = {0};
static void Put16(u8 *p, u16 v) {p[0]=v; p[1]=v>>8;}
static void Put32(u8 *p, u32 v) {Put16(p,v);Put16(p+2,v>>16);}
static u32 Sum(void)
{
    u32 h=2166136261u, i; u8 bytes[16];
    Put32(bytes,gPiMailbox.sequence);Put32(bytes+4,gPiMailbox.nonce);
    Put32(bytes+8,gPiMailbox.generation);Put16(bytes+12,gPiMailbox.message_type);Put16(bytes+14,gPiMailbox.length);
    for(i=0;i<16;i++)h=(h^bytes[i])*16777619u;
    for(i=0;i<gPiMailbox.length;i++)h=(h^gPiMailbox.payload[i])*16777619u;
    return h;
}
void PiBridge_Init(void)
{
    u32 i; volatile u8 *p=(volatile u8 *)&gPiMailbox;
    for(i=0;i<sizeof(gPiMailbox);i++)p[i]=0;
    p=(volatile u8 *)&sPiEvents;for(i=0;i<sizeof(sPiEvents);i++)p[i]=0;
    gPiMailbox.version=PI_VERSION;gPiMailbox.size=sizeof(gPiMailbox);gPiMailbox.build_tag=PI_BUILD_TAG;
    gPiMailbox.magic=PI_MAGIC;
}
void PiEvents_Enqueue(u16 type, u16 phase, const u8 *data, u16 length)
{
    struct PiRecord *r; u32 i;
    if(gPiMailbox.event_counter==0xffffffffu) {gPiMailbox.drops++;return;}
    gPiMailbox.event_counter++;
    /* Two terminal records need space even under bounded backpressure.
     * Discard only unsent tail observations; never overwrite the in-flight head. */
    if(type==PI_EVENT_TRAINER_DEFEATED || type==PI_EVENT_BATTLE_ENDED)
    {
        u8 limit=type==PI_EVENT_TRAINER_DEFEATED?2:3;
        while(sPiEvents.count>limit)
        {
            struct PiRecord *tail=&sPiEvents.queue[(sPiEvents.head+sPiEvents.count-1)%4];
            u16 tailType=tail->data[2]|(tail->data[3]<<8);
            if(tailType==PI_EVENT_TRAINER_DEFEATED || tailType==PI_EVENT_BATTLE_ENDED)break;
            sPiEvents.count--;gPiMailbox.drops++;
        }
    }
    if(length>PI_PAYLOAD_MAX-24 || sPiEvents.count==4) {gPiMailbox.drops++;return;}
    r=&sPiEvents.queue[(sPiEvents.head+sPiEvents.count)%4];
    for(i=0;i<PI_PAYLOAD_MAX;i++)r->data[i]=0;
    Put16(r->data,1);Put16(r->data+2,type);Put32(r->data+4,gPiMailbox.event_counter);
    Put32(r->data+8,gPiMailbox.battle_id);Put16(r->data+12,gPiMailbox.turn_id);
    Put16(r->data+14,phase);Put32(r->data+16,gPiMailbox.heartbeat);Put16(r->data+20,length);
    /* Reserved flags stay zero. No pointers, strings, RNG or wall-clock data. */
    for(i=0;i<length;i++)r->data[24+i]=data[i];
    r->length=24+length;sPiEvents.count++;gPiMailbox.queue_depth=sPiEvents.count;
}
static void Pop(void)
{
    if(sPiEvents.count){sPiEvents.head=(sPiEvents.head+1)%4;sPiEvents.count--;}
    gPiMailbox.queue_depth=sPiEvents.count;sPiEvents.attempt=0;gPiMailbox.state=PI_STATE_IDLE;
}
static void Failure(u16 code)
{
    gPiMailbox.error=code;gPiMailbox.failures++;gPiMailbox.state=PI_STATE_ERROR;
}
void PiBridge_Tick(void)
{
    u32 i;
    gPiMailbox.heartbeat++;
    if(gPiMailbox.magic!=PI_MAGIC || gPiMailbox.size!=sizeof(gPiMailbox)) {Failure(PI_ERR_MALFORMED);return;}
    if(gPiMailbox.version!=PI_VERSION || gPiMailbox.build_tag!=PI_BUILD_TAG) {Failure(PI_ERR_VERSION);return;}
    if(gPiMailbox.state==PI_STATE_RESPONSE_READY)
    {
        if(gPiMailbox.response_sequence!=gPiMailbox.sequence || gPiMailbox.response_nonce!=gPiMailbox.nonce
         || gPiMailbox.response_generation!=gPiMailbox.generation) Failure(PI_ERR_STALE);
        else if(gPiMailbox.message_type!=PI_TYPE_EVENT_ACK || gPiMailbox.length!=0 || gPiMailbox.result || gPiMailbox.error || gPiMailbox.reserved
             || gPiMailbox.checksum!=Sum()) Failure(PI_ERR_MALFORMED);
        else {gPiMailbox.last_ack=gPiMailbox.sequence;gPiMailbox.successes++;Pop();}
    }
    else if(gPiMailbox.state==PI_STATE_REQUEST_READY || gPiMailbox.state==PI_STATE_REQUEST_IN_PROGRESS)
    {
        if((u32)(gPiMailbox.heartbeat-gPiMailbox.deadline)<0x80000000u)Failure(PI_ERR_TIMEOUT);
    }
    else if(gPiMailbox.state==PI_STATE_ERROR)
    {
        struct PiRecord *r=&sPiEvents.queue[sPiEvents.head];
        u16 type=r->data[2]|(r->data[3]<<8);
        if(type==PI_EVENT_TRAINER_DEFEATED || type==PI_EVENT_BATTLE_ENDED)
        { /* Stable copied terminal payload: bounded per-frame work, no game wait.
           * Same identity is retained until ACK or explicit fresh/reset lifecycle. */
            sPiEvents.attempt=0;gPiMailbox.retries++;gPiMailbox.state=PI_STATE_IDLE;
        }
        else if(++sPiEvents.attempt>2){gPiMailbox.drops++;Pop();}
        else {gPiMailbox.retries++;gPiMailbox.state=PI_STATE_IDLE;}
    }
    else if(gPiMailbox.state!=PI_STATE_IDLE)Failure(PI_ERR_MALFORMED);
    if(gPiMailbox.state==PI_STATE_IDLE && sPiEvents.count)
    {
        struct PiRecord *r=&sPiEvents.queue[sPiEvents.head];
        gPiMailbox.sequence=r->data[4]|(r->data[5]<<8)|(r->data[6]<<16)|((u32)r->data[7]<<24);
        gPiMailbox.message_type=PI_TYPE_EVENT;gPiMailbox.length=r->length;
        gPiMailbox.result=0;gPiMailbox.error=0;
        for(i=0;i<r->length;i++)gPiMailbox.payload[i]=r->data[i];
        gPiMailbox.deadline=gPiMailbox.heartbeat+PI_TIMEOUT_FRAMES;gPiMailbox.checksum=Sum();
        gPiMailbox.state=PI_STATE_REQUEST_READY;
    }
}
#ifndef PI_EVENTS_NATIVE_TEST
void PiEvents_BattleStart(void)
{
    u8 data[8];u32 i,j;
    sPiEvents.active=0;
    /* Native special modes remain untouched, and are not presented as supported. */
    if(gBattleTypeFlags & ~(BATTLE_TYPE_IS_MASTER|BATTLE_TYPE_TRAINER))return;
    if(gPiMailbox.battle_id==0xffffffffu){gPiMailbox.drops++;return;}
    gPiMailbox.battle_id++;gPiMailbox.turn_id=0;sPiEvents.active=1;sPiEvents.turnReady=1;
    sPiEvents.battleFlags=gBattleTypeFlags;sPiEvents.trainer=(gBattleTypeFlags&BATTLE_TYPE_TRAINER)?gTrainerBattleOpponent_A:0;
    sPiEvents.firstWin=sPiEvents.trainer && !HasTrainerBeenFought(sPiEvents.trainer);
    for(i=0;i<6;i++)for(j=0;j<4;j++)sPiEvents.revealed[i][j]=0;
    for(i=0;i<4;i++)sPiEvents.actionMove[i]=0;
    Put32(data,gBattleTypeFlags);Put16(data+4,sPiEvents.trainer);data[6]=sPiEvents.firstWin;data[7]=0;
    PiEvents_Enqueue(PI_EVENT_BATTLE_STARTED,PI_PHASE_START,data,8);
}
void PiEvents_NextTurn(void) {sPiEvents.turnReady=1;}
void PiEvents_Turn(void)
{
    u8 data[40];u32 i,own,other,slot;u16 turn;
    if(!sPiEvents.active || gBattlersCount!=2)return;
    if(!sPiEvents.turnReady)return;
    if(gPiMailbox.turn_id==65535){sPiEvents.active=0;gPiMailbox.drops++;return;}
    sPiEvents.turnReady=0;
    turn=gPiMailbox.turn_id+1;
    gPiMailbox.turn_id=turn;
    PiEvents_Enqueue(PI_EVENT_BATTLE_TURN_STARTED,PI_PHASE_SELECTION,NULL,0);
    own=GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT);other=GetBattlerAtPosition(B_POSITION_PLAYER_LEFT);
    slot=gBattlerPartyIndexes[other];
    for(i=0;i<40;i++)data[i]=0;
    /* Observer is NPC side. Never copy the BattlePokemon structure wholesale. */
    Put16(data,sPiEvents.trainer);Put16(data+2,gBattleMons[own].species);
    Put16(data+4,gBattleMons[own].hp);Put16(data+6,gBattleMons[own].maxHP);
    Put32(data+8,gBattleMons[own].status1 & 0xff);
    for(i=0;i<4;i++){Put16(data+12+2*i,gBattleMons[own].moves[i]);data[20+i]=gBattleMons[own].pp[i];}
    Put16(data+24,gBattleMons[other].species);
    /* Coarse public HP bar, 0..48; deliberately excludes exact player HP. */
    data[26]=gBattleMons[other].maxHP ? (gBattleMons[other].hp*48+gBattleMons[other].maxHP-1)/gBattleMons[other].maxHP : 0;
    data[27]=0; /* legal-action list NOT complete; no tactical request can be issued */
    if(slot<6)for(i=0;i<4;i++)Put16(data+28+2*i,sPiEvents.revealed[slot][i]);
    /* Remaining four bytes reserved. Opponent items/stats/status2/RNG omitted. */
    PiEvents_Enqueue(PI_EVENT_BATTLE_OBSERVATION,PI_PHASE_SELECTION,data,40);
}
void PiEvents_Reveal(void)
{
    u32 i,slot;
    if(!sPiEvents.active || gBattlerAttacker>=4)return;
    sPiEvents.actionMove[gBattlerAttacker]=gCurrentMove;
    if(GetBattlerSide(gBattlerAttacker)!=B_SIDE_PLAYER)return;
    slot=gBattlerPartyIndexes[gBattlerAttacker];if(slot>=6)return;
    for(i=0;i<4;i++)if(sPiEvents.revealed[slot][i]==gCurrentMove)return;
    for(i=0;i<4;i++)if(!sPiEvents.revealed[slot][i]){sPiEvents.revealed[slot][i]=gCurrentMove;return;}
}
void PiEvents_Action(u8 actor,u8 kind)
{
    u8 data[6];
    if(!sPiEvents.active || actor>=gBattlersCount)return;
    (void)kind;
    data[0]=GetBattlerSide(actor);data[1]=sPiEvents.actionMove[actor] ? 1 : 0;
    Put16(data+2,sPiEvents.actionMove[actor]);Put16(data+4,gBattleMons[actor].species);
    PiEvents_Enqueue(PI_EVENT_BATTLE_ACTION_RESOLVED,PI_PHASE_RESOLVED,data,6);
    sPiEvents.actionMove[actor]=0;
}
void PiEvents_End(void)
{
    u8 data[4];
    if(!sPiEvents.active)return;
    Put16(data,sPiEvents.trainer);data[2]=sPiEvents.firstWin;data[3]=gBattleOutcome;
    if(sPiEvents.trainer && gBattleOutcome==B_OUTCOME_WON)
        PiEvents_Enqueue(PI_EVENT_TRAINER_DEFEATED,PI_PHASE_END,data,4);
    PiEvents_Enqueue(PI_EVENT_BATTLE_ENDED,PI_PHASE_END,data,4);sPiEvents.active=0;
}
#endif
#endif

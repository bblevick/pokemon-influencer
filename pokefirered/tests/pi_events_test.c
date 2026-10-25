#include "pi_events.h"
#include <assert.h>
#include <stdio.h>
static u32 sum(void)
{
    u32 h=2166136261u,words[4],i,j;
    words[0]=gPiMailbox.sequence;words[1]=gPiMailbox.nonce;words[2]=gPiMailbox.generation;words[3]=4;
    for(i=0;i<4;i++)for(j=0;j<4;j++)h=(h^((words[i]>>(j*8))&255))*16777619u;
    return h;
}
static void ack(void)
{
    gPiMailbox.response_sequence=gPiMailbox.sequence;gPiMailbox.response_nonce=gPiMailbox.nonce;
    gPiMailbox.response_generation=gPiMailbox.generation;gPiMailbox.message_type=4;gPiMailbox.length=0;
    gPiMailbox.checksum=sum();gPiMailbox.state=3;
}
static void init(void){PiBridge_Init();gPiMailbox.battle_id=1;PiEvents_Enqueue(1,0,NULL,0);PiBridge_Tick();}
int main(void)
{
    u32 i,seq;u8 bytes[73]={0};
    init();assert(gPiMailbox.version==2 && gPiMailbox.state==1);puts("PASS event publication");
    ack();PiBridge_Tick();assert(gPiMailbox.successes==1 && gPiMailbox.queue_depth==0);puts("PASS event ACK");
    init();seq=gPiMailbox.sequence;for(i=0;i<184;i++)PiBridge_Tick();assert(!gPiMailbox.queue_depth && gPiMailbox.drops==1 && gPiMailbox.failures==3 && gPiMailbox.retries==2);puts("PASS unavailable bounded retry timeout drop");
    init();ack();gPiMailbox.response_sequence++;PiBridge_Tick();assert(gPiMailbox.error==4);puts("PASS stale ACK rejected");
    init();ack();gPiMailbox.response_generation++;PiBridge_Tick();assert(gPiMailbox.error==4);puts("PASS stale generation rejected");
    init();ack();gPiMailbox.length=97;PiBridge_Tick();assert(gPiMailbox.error==2);puts("PASS oversized ACK rejected before read");
    init();gPiMailbox.state=4;gPiMailbox.error=5;PiBridge_Tick();assert(gPiMailbox.retries==1 && gPiMailbox.sequence==seq && gPiMailbox.state==1);puts("PASS disconnect retry same ID");
    PiBridge_Init();for(i=0;i<5;i++)PiEvents_Enqueue(1,0,NULL,0);assert(gPiMailbox.queue_depth==4 && gPiMailbox.drops==1 && gPiMailbox.event_counter==5);puts("PASS backpressure bounded gap");
    PiBridge_Init();PiEvents_Enqueue(1,0,bytes,72);PiBridge_Tick();assert(gPiMailbox.length==96);puts("PASS payload maximum");
    PiBridge_Init();PiEvents_Enqueue(1,0,bytes,73);assert(gPiMailbox.drops==1 && !gPiMailbox.queue_depth);puts("PASS oversized enqueue rejected");
    init();PiBridge_Init();assert(!gPiMailbox.sequence && !gPiMailbox.event_counter && !gPiMailbox.battle_id && !gPiMailbox.queue_depth && !gPiMailbox.nonce);puts("PASS reset clears transient identities");
    init();ack();gPiMailbox.error=1;PiBridge_Tick();assert(gPiMailbox.error==2 && !gPiMailbox.successes);puts("PASS nonzero ACK error rejected");
    init();ack();gPiMailbox.reserved=1;PiBridge_Tick();assert(gPiMailbox.error==2 && !gPiMailbox.successes);puts("PASS reserved ACK bits rejected");
    puts("13 actual C event transport cases passed");return 0;
}

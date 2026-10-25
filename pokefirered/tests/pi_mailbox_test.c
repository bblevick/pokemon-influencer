/* Execute the actual ROM state machine on the host, with only platform types stubbed. */
#include "pi_protocol.h"
#include "main.h"
#include <assert.h>
#include <stdio.h>
struct PiTestMain gMain;
static unsigned count;
static void passed(const char *name) { printf("PASS %s\n", name);count++; }
static u32 checksum(void)
{
    u32 h=2166136261u, words[4],i,j;
    words[0]=gPiMailbox.response_sequence;words[1]=gPiMailbox.response_nonce;
    words[2]=gPiMailbox.response_generation;words[3]=2 | (4u<<16);
    for(i=0;i<4;i++)for(j=0;j<4;j++)h=(h ^ ((words[i]>>(j*8))&255))*16777619u;
    for(i=0;i<4;i++)h=(h ^ gPiMailbox.payload[i])*16777619u;
    return h;
}
static void request(void)
{
    PiBridge_Init();gPiMailbox.nonce=12;gPiMailbox.generation=3;
    gPiMailbox.debug_trigger=1;PiBridge_Tick();assert(gPiMailbox.state==1);
}
static void respond(void)
{
    gPiMailbox.response_sequence=gPiMailbox.sequence;gPiMailbox.response_nonce=12;
    gPiMailbox.response_generation=3;gPiMailbox.message_type=2;
    gPiMailbox.payload[0]='P';gPiMailbox.payload[1]='O';gPiMailbox.payload[2]='N';gPiMailbox.payload[3]='G';
    gPiMailbox.checksum=checksum();gPiMailbox.state=3;
}
int main(void)
{
    unsigned i;u32 heartbeat;
    PiBridge_Init();assert(gPiMailbox.magic==PI_MAGIC && gPiMailbox.version==1 && gPiMailbox.state==0 && sizeof(gPiMailbox)==108);passed("initial-layout-idle");
    request();assert(gPiMailbox.sequence==1 && gPiMailbox.length==4 && gPiMailbox.payload[2]=='K');passed("ROM-originated-bounded-request");
    respond();PiBridge_Tick();assert(gPiMailbox.state==0 && gPiMailbox.last_ack==1 && gPiMailbox.successes==1);passed("valid-response-ack-identity");
    request();for(i=0;i<60;i++)PiBridge_Tick();assert(gPiMailbox.state==4 && gPiMailbox.error==1);heartbeat=gPiMailbox.heartbeat;PiBridge_Tick();assert(gPiMailbox.state==0 && gPiMailbox.heartbeat>heartbeat);passed("host-absent-timeout-keeps-ticking");
    request();respond();gPiMailbox.response_sequence=2;PiBridge_Tick();assert(gPiMailbox.error==4 && !gPiMailbox.successes);passed("stale-sequence-rejected");
    request();respond();gPiMailbox.response_nonce=13;PiBridge_Tick();assert(gPiMailbox.error==4);passed("stale-session-rejected");
    request();respond();gPiMailbox.response_generation=4;PiBridge_Tick();assert(gPiMailbox.error==4);passed("stale-generation-rejected");
    request();respond();gPiMailbox.length=65535;PiBridge_Tick();assert(gPiMailbox.error==2);passed("oversized-response-no-buffer-read");
    request();respond();gPiMailbox.checksum^=1;PiBridge_Tick();assert(gPiMailbox.error==2);passed("corrupt-response-rejected");
    request();gPiMailbox.version=2;PiBridge_Tick();assert(gPiMailbox.error==3);passed("unsupported-version");
    request();gPiMailbox.magic=0;PiBridge_Tick();assert(gPiMailbox.error==2);passed("malformed-magic");
    PiBridge_Init();gPiMailbox.sequence=0xffffffffu;gPiMailbox.debug_trigger=1;PiBridge_Tick();assert(gPiMailbox.error==4 && gPiMailbox.sequence==0xffffffffu);passed("sequence-wrap-refused");
    request();gPiMailbox.state=4;gPiMailbox.error=5;PiBridge_Tick();assert(gPiMailbox.state==0 && gPiMailbox.error==5);passed("disconnect-error-degrades");
    request();PiBridge_Init();assert(gPiMailbox.state==0 && !gPiMailbox.sequence && !gPiMailbox.nonce && !gPiMailbox.successes);passed("ROM-reset-defined-idle");
    request();gPiMailbox.heartbeat=0xfffffff0u;gPiMailbox.deadline=gPiMailbox.heartbeat+60;for(i=0;i<59;i++)PiBridge_Tick();assert(gPiMailbox.state==1);PiBridge_Tick();assert(gPiMailbox.state==4);passed("frame-counter-wrap-timeout");
    printf("%u actual C state-machine cases passed\n",count);return 0;
}

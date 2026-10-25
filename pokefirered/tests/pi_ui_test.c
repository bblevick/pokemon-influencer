#include <assert.h>
#include <stdio.h>
#include <stddef.h>
#include "pi_events.h"
volatile struct PiEventMailbox gPiMailbox;
#include "../src/pi_ui.c"
static void Put16(u16 n,u16 v){gPiUi.payload[n]=v;gPiUi.payload[n+1]=v>>8;}
static void Put32(u16 n,u32 v){Put16(n,v);Put16(n+2,v>>16);}
static void Start(void)
{
 PiUi_Init();gPiMailbox.heartbeat=100;gPiUi.run_nonce=1;gPiUi.run_generation=2;
 gPiUi.trigger=2;PiUi_Tick();assert(gPiUi.state==1 && gPiUi.request_id==1);
 gPiUi.command_id=81;gPiUi.state=3;gPiUi.length=23;
 Put16(0,1);Put16(2,2);Put32(4,1);Put32(8,900);Put16(12,2);Put16(14,11);Put16(16,22);Put16(18,3);
 gPiUi.payload[20]=0xbb;gPiUi.payload[21]=0;gPiUi.payload[22]=0xd5;
 gPiUi.checksum=Sum();
}
static void Check(u16 result){gPiUi.checksum=Sum();PiUi_Tick();assert(gPiUi.state==5 && gPiUi.result==result);}
int main(void)
{
 u16 c;Start();PiUi_Tick();assert(gPiUi.state==3 && sUi.text[3]==255 && sUi.yes==11 && sUi.no==22);
 Start();gPiUi.length=97;PiUi_Tick();assert(gPiUi.result==2);
 Start();gPiUi.length=8;Check(2);
 Start();Put16(0,2);Check(3);
 Start();Put16(2,1);Check(2);
 Start();Put32(4,2);Check(2);
 Start();gPiUi.command_id=0;Check(2);
 Start();Put32(8,901);Check(2);
 Start();Put32(8,59);Check(2);
 Start();Put16(12,4);Check(2);
 Start();Put16(14,0);Check(2);
 Start();Put16(16,11);Check(2);
 for(c=0xfa;c<=0xff;c++){if(c==0xfe)continue;Start();gPiUi.payload[20]=c;Check(4);}
 Start();gPiUi.payload[20]=0xfe;Check(4);
 Start();gPiUi.payload[22]=0xfe;Check(4);
 Start();gPiUi.length=69;Check(2);
 Start();gPiUi.checksum++;PiUi_Tick();assert(gPiUi.result==2);
 Start();gPiUi.run_generation=3;PiUi_Tick();assert(gPiUi.state==0);
 Start();gPiUi.run_nonce=2;PiUi_Tick();assert(gPiUi.state==0);
 Start();gPiUi.state=2;gPiMailbox.heartbeat=280;PiUi_Tick();assert(gPiUi.result==6 && gPiUi.state==5);
 gPiMailbox.heartbeat=460;PiUi_Tick();assert(gPiUi.state==0);
 Start();gPiUi.state=6;gPiMailbox.heartbeat=280;PiUi_Tick();assert(gPiUi.state==0);
 Start();PiUi_Init();assert(gPiUi.state==0 && !sUi.owned && !gPiUi.request_id);
 Start();gPiUi.trigger=1;PiUi_Tick();assert(gPiUi.kind==2 && gPiUi.request_id==1);
 puts("28 actual-C validation/request/run-change/timeout/reset cases passed (native UI excluded)");return 0;
}

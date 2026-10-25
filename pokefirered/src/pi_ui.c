#include "global.h"
#if PI_UI
#if !PI_EVENTS
#error PI_UI requires PI_EVENTS
#endif
#include "pi_ui.h"
#include "pi_events.h"
#ifndef PI_UI_NATIVE_TEST
#include "gflib.h"
#include "field_message_box.h"
#include "menu.h"
#include "new_menu_helpers.h"
#include "script.h"
#include "event_object_movement.h"
#include "quest_log.h"
#endif
#define PI_ALLOC __attribute__((section("pi_mailbox_data"), aligned(4)))
volatile struct PiUiMailbox gPiUi PI_ALLOC = {0};
struct PiUiState { u32 nonce, generation; u16 yes, no; u8 owned, phase; u8 text[PI_UI_TEXT_BYTES+1]; };
static struct PiUiState sUi PI_ALLOC = {0};
const u32 gPiUiLayout[] = {sizeof(struct PiUiMailbox), sizeof(struct PiUiState),PI_UI_LAYOUT_VALUES};
typedef char PiUiBounds[(sizeof(struct PiUiMailbox)+sizeof(struct PiUiState)<=240)?1:-1];
#ifndef PI_UI_NATIVE_TEST
static bool8 Safe(void);
#endif
static u16 U16(u16 n) { return gPiUi.payload[n] | gPiUi.payload[n+1]<<8; }
static u32 U32(u16 n) { return U16(n) | ((u32)U16(n+2)<<16); }
static u32 Sum(void)
{
 u32 h=2166136261u,i,v;u8 b[16];
 v=gPiUi.command_id;for(i=0;i<4;i++)b[i]=v>>(i*8);
 v=gPiUi.nonce;for(i=0;i<4;i++)b[i+4]=v>>(i*8);
 v=gPiUi.generation;for(i=0;i<4;i++)b[i+8]=v>>(i*8);
 b[12]=6;b[13]=0;b[14]=gPiUi.length;b[15]=gPiUi.length>>8;
 for(i=0;i<16;i++)h=(h^b[i])*16777619u;
 for(i=0;i<gPiUi.length;i++)h=(h^gPiUi.payload[i])*16777619u;
 return h;
}
static bool8 Character(u8 c)
{
 return c==0 || (c>=0xA1 && c<=0xAE) || c==0xB4 || c==0xB8 || c==0xBA
     || (c>=0xBB && c<=0xEE) || c==0xFE;
}
static void Finish(u16 result,u16 choice)
{
 gPiUi.result=result;gPiUi.choice_id=choice;gPiUi.completed++;
 gPiUi.deadline=gPiMailbox.heartbeat+PI_UI_REQUEST_TICKS;gPiUi.state=5;
}
static u16 Validate(void)
{
 u16 n,i,col=0,lines=1;u32 ttl;
 if(gPiUi.length>PI_UI_COMMAND_PAYLOAD || gPiUi.length<21) return 2;
 if(Sum()!=gPiUi.checksum) return 2;
 if(U16(0)!=PI_UI_SCHEMA) return 3;
 if(U16(2)!=gPiUi.kind || U32(4)!=gPiUi.request_id || !gPiUi.command_id) return 2;
 ttl=U32(8);if(ttl<PI_UI_MIN_UI_TICKS || ttl>PI_UI_MAX_UI_TICKS) return 2;
 n=U16(18);if(n==0 || n>PI_UI_TEXT_BYTES || gPiUi.length!=20+n) return 2;
 if(gPiUi.kind==1) { if(U16(12)||U16(14)||U16(16))return 2; }
 else if(gPiUi.kind==2) { if(U16(12)!=2 || !U16(14) || !U16(16) || U16(14)==U16(16))return 2; }
 else return 2;
 for(i=0;i<n;i++)
 {
  u8 c=gPiUi.payload[20+i];if(!Character(c))return 4;
  if(c==0xFE) {if(!col || ++lines>PI_UI_LINES || i==n-1)return 4;col=0;}
  else if(++col>PI_UI_LINE_CHARACTERS)return 4;
  sUi.text[i]=c;
 }
 sUi.text[n]=0xFF;sUi.yes=U16(14);sUi.no=U16(16);
 gPiUi.deadline=gPiMailbox.heartbeat+ttl;
 return 0;
}
bool8 PiUi_ViewerChecksum(void)
{
 return gPiUi.kind==3 && gPiUi.state==3 && gPiUi.length<=96 && gPiUi.command_id
 && gPiUi.nonce==gPiUi.run_nonce && gPiUi.generation==gPiUi.run_generation && Sum()==gPiUi.checksum;
}
void PiUi_Init(void)
{
 u32 i;volatile u8 *p=(volatile u8 *)&gPiUi;
 for(i=0;i<sizeof(gPiUi);i++)p[i]=0;
 p=(volatile u8 *)&sUi;for(i=0;i<sizeof(sUi);i++)p[i]=0;
 gPiUi.magic=PI_UI_MAGIC;
}
void PiUi_Tick(void)
{
 u16 result;
 /* Native UI cleanup is owned solely by the overworld hook. */
 if(gPiUi.state && (gPiUi.nonce!=gPiUi.run_nonce || gPiUi.generation!=gPiUi.run_generation))
 {if(!sUi.owned)gPiUi.state=0;return;}
#if PI_UI_TEST
 if(gPiUi.trigger)
 {
  u16 kind=gPiUi.trigger;gPiUi.trigger=0;
  if(gPiUi.state==0 && kind<=2 && gPiUi.request_id!=0xffffffffu)
  {
   gPiUi.request_id++;gPiUi.command_id=0;gPiUi.kind=kind;
   gPiUi.nonce=gPiUi.run_nonce;gPiUi.generation=gPiUi.run_generation;
   gPiUi.result=0;gPiUi.choice_id=0;gPiUi.deadline=gPiMailbox.heartbeat+PI_UI_REQUEST_TICKS;
   gPiUi.state=1;
  }
 }
#endif
 if(gPiUi.state==3 && gPiUi.kind!=3)
 {
  result=Validate();if(result)Finish(result,0);
#ifndef PI_UI_NATIVE_TEST
  else if(!PiUi_IsField() || !Safe())Finish(5,0);
#endif
  /* Validated command waits only until this frame's safe field hook; no queue. */
 }
 if(gPiUi.state && (s32)(gPiMailbox.heartbeat-gPiUi.deadline)>=0 && !sUi.owned)
 {
  if(gPiUi.state==5 || gPiUi.state==6)gPiUi.state=0;
  else Finish(6,0);
 }
}
#ifndef PI_UI_NATIVE_TEST
static void Release(void)
{
 if(sUi.phase==3)DestroyYesNoMenu();
 /* Slot zero belongs to our field message while we own the control lock. */
 PiUi_StopPrinter();
 HideFieldMessageBox();UnfreezeObjectEvents();UnlockPlayerFieldControls();
 sUi.owned=0;sUi.phase=0;
}
static bool8 Safe(void)
{
 return !ArePlayerFieldControlsLocked() && !ScriptContext_IsEnabled()
     && !gPaletteFade.active && IsFieldMessageBoxHidden()
     && !QL_IS_PLAYBACK_STATE && QL_GetPlaybackState()!=QL_PLAYBACK_STATE_RUNNING
     && gPlayerAvatar.tileTransitionState==T_NOT_MOVING;
}
bool8 PiUi_Field(void)
{
 s8 input;
 if(sUi.owned)
 {
  if(sUi.nonce!=gPiUi.run_nonce || sUi.generation!=gPiUi.run_generation)
  {Release();gPiUi.state=0;return TRUE;}
  if((s32)(gPiMailbox.heartbeat-gPiUi.deadline)>=0)
  {Release();Finish(6,0);return TRUE;}
  if(sUi.phase==1 && IsFieldMessageBoxHidden())
  {
   if(gPiUi.kind==2){DisplayYesNoMenuDefaultYes();sUi.phase=3;}
   else sUi.phase=2;
   return TRUE;
  }
  if(sUi.phase==2 && (gMain.newKeys & (A_BUTTON|B_BUTTON)))
  {Release();Finish(0,0);}
  else if(sUi.phase==3)
  {
   input=Menu_ProcessInputNoWrapClearOnChoose();
   if(input!=MENU_NOTHING_CHOSEN)
   {
    u16 choice=input==0?sUi.yes:sUi.no;
    /* Native input function already destroys the yes/no window. */
    sUi.phase=2;Release();Finish(input==MENU_B_PRESSED?7:0,input==MENU_B_PRESSED?0:choice);
   }
  }
  return TRUE;
 }
 if(gPiUi.state!=3 || gPiUi.kind==3)return FALSE;
 if(!Safe()){Finish(5,0);return FALSE;}
 LockPlayerFieldControls();FreezeObjectEvents();MsgSetNotSignpost();
 if(!ShowFieldMessage(sUi.text)){UnfreezeObjectEvents();UnlockPlayerFieldControls();Finish(5,0);return FALSE;}
 sUi.owned=1;sUi.phase=1;sUi.nonce=gPiUi.nonce;sUi.generation=gPiUi.generation;
 gPiUi.state=4;return TRUE;
}
#else
bool8 PiUi_Field(void) {return FALSE;}
#endif
#endif

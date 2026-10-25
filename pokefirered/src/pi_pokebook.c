#include "global.h"
#if PI_UI
#include "gflib.h"
#include "pi_ui.h"
#include "pi_events.h"
#include "pi_pokebook.h"
#include "pi_pokebook_wire.h"
#include "overworld.h"
#include "menu.h"
#include "list_menu.h"
#include "task.h"
#include "text_window.h"
#include "constants/rgb.h"
/* Only a four-byte owner pointer is permanent. All screen data is checked heap. */
struct PbScreen {
 u32 view,snapshot,post,nonce,run;
 u16 op,page,pages,feedPage,feedCursor;
 u8 list,waiting,count;
 u8 labels[3][19],text[73];
 struct ListMenuItem items[3];
 struct ListMenuTemplate menu;
 u16 tilemap[1024];
};
static struct PbScreen *sPb __attribute__((section("pi_mailbox_data"),aligned(4))) = NULL;
const u32 gPiPokeBookResources[]={sizeof(struct PbScreen),26*16*32,1,1,0};
static const struct BgTemplate sBg={.bg=0,.charBaseIndex=0,.mapBaseIndex=31,.priority=0};
static const struct WindowTemplate sWindows[]={ {0,2,2,26,16,15,1}, DUMMY_WIN_TEMPLATE };
static const u8 sTitle[] = _("PokeBook");
static const u8 sHome[][19] = {_("Feed"),_("Followers"),_("Refresh")};
static const u8 sHint[] = _("A Open  B Back\nLeft/Right Page");
static const u8 sWait[] = _("Contacting PokeBook...\nB Exit");
static const u8 sUnavailable[] = _("PokeBook unavailable.\nB Back or Exit");
static const u8 sEmpty[] = _("Nothing here yet.");
static const u8 sFollowers[] = _("Followers");
static const u8 sPage[] = _("Page");
static void Main(void);
static void Put16(u16 at,u16 v){gPiUi.payload[at]=v;gPiUi.payload[at+1]=v>>8;}
static void Put32(u16 at,u32 v){Put16(at,v);Put16(at+2,v>>16);}
static void Text(const u8 *p,u8 x,u8 y){AddTextPrinterParameterized(0,FONT_NORMAL,p,x,y,0xff,NULL);}
static void DropList(void){if(sPb->list!=0xff){DestroyListMenuTask(sPb->list,NULL,NULL);sPb->list=0xff;}}
static void Frame(void){FillWindowPixelBuffer(0,0x11);Text(sTitle,0,0);Text(sHint,0,99);}
static void Copy(void){PutWindowTilemap(0);CopyWindowToVram(0,COPYWIN_FULL);}
static void Number(u32 n,u8 x,u8 y){u8 b[12];ConvertIntToDecimalStringN(b,n,STR_CONV_MODE_LEFT_ALIGN,3);Text(b,x,y);}
static void List(u8 count,u16 cursor)
{
 u16 i;DropList();sPb->count=count;
 if(!count){Text(sEmpty,0,35);Copy();return;}
 for(i=0;i<count;i++){sPb->items[i].label=sPb->labels[i];sPb->items[i].index=i;}
 sPb->menu.items=sPb->items;sPb->menu.totalItems=count;sPb->menu.maxShowed=count;
 sPb->menu.windowId=0;sPb->menu.item_X=10;sPb->menu.cursor_X=0;sPb->menu.upText_Y=15;
 sPb->menu.cursorPal=2;sPb->menu.fillValue=1;sPb->menu.cursorShadowPal=3;
 sPb->menu.itemVerticalPadding=2;sPb->menu.fontId=FONT_NORMAL;
 sPb->list=ListMenuInit(&sPb->menu,0,cursor<count?cursor:0);Text(sTitle,0,0);Text(sHint,0,99);Copy();
}
static void Query(u16 op,u16 page,u32 post)
{
 DropList();Frame();Text(sWait,0,30);Copy();sPb->waiting=TRUE;
 sPb->op=op;sPb->page=page;sPb->post=post;
 if(gPiUi.request_id==0xffffffffu){sPb->waiting=FALSE;Frame();Text(sUnavailable,0,30);Copy();return;}
 gPiUi.state=0;gPiUi.request_id++;
 if(op==1){sPb->view=gPiUi.request_id;sPb->snapshot=0;}
 gPiUi.kind=3;gPiUi.command_id=0;gPiUi.length=24;gPiUi.result=0;
 gPiUi.nonce=gPiUi.run_nonce;gPiUi.generation=gPiUi.run_generation;
 sPb->nonce=gPiUi.nonce;sPb->run=gPiUi.generation;
 Put16(0,2);Put16(2,op);Put32(4,gPiUi.request_id);Put32(8,sPb->view);
 Put32(12,sPb->snapshot);Put32(16,post);Put16(20,page);Put16(22,0);
 gPiUi.deadline=gPiMailbox.heartbeat+180;gPiUi.state=1;
}
static void Exit(void)
{
 SetVBlankCallback(NULL);DropList();gPiUi.state=0;
 FreeAllWindowBuffers();UnsetBgTilemapBuffer(0);Free(sPb);sPb=NULL;
 SetMainCallback2(CB2_ReturnToFieldWithOpenMenu);
}
static void VBlank(void){LoadOam();ProcessSpriteCopyRequests();TransferPlttBuffer();}
void CB2_OpenPokeBook(void)
{
 SetVBlankCallback(NULL);
 sPb=AllocZeroed(sizeof(*sPb));
 if(!sPb){SetMainCallback2(CB2_ReturnToFieldWithOpenMenu);return;}
 sPb->list=0xff;
 ResetTasks();ResetSpriteData();FreeAllSpritePalettes();
 SetGpuReg(REG_OFFSET_DISPCNT,0);SetGpuReg(REG_OFFSET_BLDCNT,0);
 SetGpuReg(REG_OFFSET_BLDY,0);SetGpuReg(REG_OFFSET_WIN0H,0);SetGpuReg(REG_OFFSET_WIN0V,0);
 ResetBgsAndClearDma3BusyFlags(0);InitBgsFromTemplates(0,&sBg,1);
 SetBgTilemapBuffer(0,sPb->tilemap);ChangeBgX(0,0,BG_COORD_SET);ChangeBgY(0,0,BG_COORD_SET);
 if(!InitWindows(sWindows)){Exit();return;}
 DeactivateAllTextPrinters();LoadPalette(GetTextWindowPalette(0),BG_PLTT_ID(15),PLTT_SIZE_4BPP);
 ResetPaletteFade();ShowBg(0);SetGpuReg(REG_OFFSET_DISPCNT,DISPCNT_MODE_0|DISPCNT_BG0_ON);
 SetVBlankCallback(VBlank);SetMainCallback2(Main);Query(1,0,0);
}
static void Response(void)
{
 u8 p[96];u16 i,n=gPiUi.length;bool8 valid=PiUi_ViewerChecksum();
 if(n>96)valid=FALSE;else for(i=0;i<n;i++)p[i]=gPiUi.payload[i];
 if(valid)valid=PbValidate(p,n,gPiUi.request_id,sPb->view,sPb->snapshot,sPb->post,sPb->op,sPb->page);
 gPiUi.state=0;sPb->waiting=FALSE;Frame();
 if(!valid || (Pb16(p+2)>>8)){Text(sUnavailable,0,30);Copy();return;}
 sPb->snapshot=Pb32(p+12);sPb->pages=Pb16(p+22);
 if(sPb->op==1)
 {
  for(i=0;i<3;i++)StringCopy(sPb->labels[i],sHome[i]);
  Text(sFollowers,95,0);Number(Pb32(p+24),174,0);List(3,0);Text(sFollowers,95,0);Number(Pb32(p+24),174,0);Copy();return;
 }
 if(sPb->pages){Text(sPage,130,0);Number(sPb->page+1,170,0);Number(sPb->pages,194,0);}
 if(sPb->op==3)
 {
  for(i=24;i<n;i++)sPb->text[i-24]=p[i];sPb->text[n-24]=255;
  if(GetStringWidth(FONT_NORMAL,sPb->text,0)>208){Text(sUnavailable,0,30);Copy();return;}
  Text(sPb->labels[sPb->feedCursor],0,18);
  Text(sPb->text,0,40);Copy();return;
 }
 for(i=0;i<(n-24)/23;i++)
 {
  u16 j;for(j=0;j<19;j++)sPb->labels[i][j]=p[28+i*23+j];
  if(GetStringWidth(FONT_NORMAL,sPb->labels[i],0)>184){Text(sUnavailable,0,30);Copy();return;}
 }
 List((n-24)/23,sPb->op==2?sPb->feedCursor:0);
 if(sPb->pages){Text(sPage,130,0);Number(sPb->page+1,170,0);Number(sPb->pages,194,0);}Copy();
}
static void Main(void)
{
 s32 chosen=LIST_NOTHING_CHOSEN;u16 cursor=0;
 RunTasks();UpdatePaletteFade();
 if(sPb->nonce!=gPiUi.run_nonce || sPb->run!=gPiUi.run_generation){Exit();return;}
 if(gMain.newKeys&B_BUTTON)
 {
  if(sPb->waiting || sPb->op==1){Exit();return;}
  if(sPb->op==3){Query(2,sPb->feedPage,0);return;}
  Query(1,0,0);return;
 }
 if(sPb->waiting)
 {
  if(gPiUi.state==3){Response();return;}
  if(gPiUi.state==5 || !gPiUi.state){gPiUi.state=0;sPb->waiting=FALSE;Frame();Text(sUnavailable,0,30);Copy();}
  return;
 }
 if(sPb->list!=0xff){chosen=ListMenu_ProcessInput(sPb->list);ListMenuGetScrollAndRow(sPb->list,NULL,&cursor);}
 if(sPb->op==1 && chosen>=0){Query(chosen==0?2:chosen==1?4:1,0,0);return;}
 if(sPb->op==2 && chosen>=0){sPb->feedPage=sPb->page;sPb->feedCursor=cursor;Query(3,0,sPb->page*3+chosen+1);return;}
 if(sPb->op!=1 && (gMain.newKeys&(DPAD_LEFT|DPAD_RIGHT)))
 {
  u16 page=sPb->page;
  if((gMain.newKeys&DPAD_RIGHT) && page+1<sPb->pages)page++;
  if((gMain.newKeys&DPAD_LEFT) && page)page--;
  if(page!=sPb->page){if(sPb->op==2)sPb->feedCursor=0;Query(sPb->op,page,sPb->post);}
 }
}
#endif

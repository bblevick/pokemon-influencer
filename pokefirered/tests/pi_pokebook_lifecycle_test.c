/* Actual screen code; deterministic platform substitutes, not emulator evidence. */
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include "../src/pi_pokebook.c"
struct Main gMain;
volatile struct PiUiMailbox gPiUi;
volatile struct PiEventMailbox gPiMailbox;
static unsigned allocated,windows,tasks,failAlloc,failWindows,lastCursor,lastAbove,selected;
static void *windowBuffer;
static void (*callback)(void);
void *AllocZeroed(u32 n){void *p;if(failAlloc)return NULL;p=calloc(1,n);if(p)allocated++;return p;}
void Free(void *p){if(p){assert(allocated);allocated--;free(p);}}
void SetVBlankCallback(void (*f)(void)){(void)f;}
void SetMainCallback2(void (*f)(void)){callback=f;}
void CB2_ReturnToFieldWithOpenMenu(void){}
void ResetTasks(void){tasks=0;}void RunTasks(void){}
void ResetSpriteData(void){}void FreeAllSpritePalettes(void){}
void SetGpuReg(u16 a,u16 b){(void)a;(void)b;}
void ResetBgsAndClearDma3BusyFlags(u8 n){(void)n;}
void InitBgsFromTemplates(u8 n,const struct BgTemplate *p,u8 c){(void)n;(void)p;(void)c;}
void SetBgTilemapBuffer(u8 n,void *p){(void)n;(void)p;}
void UnsetBgTilemapBuffer(u8 n){(void)n;}
void ChangeBgX(u8 n,s32 x,u8 t){(void)n;(void)x;(void)t;}
void ChangeBgY(u8 n,s32 y,u8 t){(void)n;(void)y;(void)t;}
bool16 InitWindows(const struct WindowTemplate *p){(void)p;windowBuffer=AllocZeroed(13312);windows=windowBuffer!=NULL;return windows&&!failWindows;}
void FreeAllWindowBuffers(void){Free(windowBuffer);windowBuffer=NULL;windows=0;}
const u16 *GetTextWindowPalette(u8 n){static const u16 p[16]={0};(void)n;return p;}
void LoadPalette(const void *p,u16 n,u16 len){(void)p;(void)n;(void)len;}
void DeactivateAllTextPrinters(void){}void ResetPaletteFade(void){}void ShowBg(u8 n){(void)n;}
void LoadOam(void){}void ProcessSpriteCopyRequests(void){}void TransferPlttBuffer(void){}void UpdatePaletteFade(void){}
void AddTextPrinterParameterized(u8 win,u8 font,const u8 *p,u8 x,u8 y,u8 speed,void *cb){(void)win;(void)font;(void)p;(void)x;(void)y;(void)speed;(void)cb;}
void FillWindowPixelBuffer(u8 w,u8 v){(void)w;(void)v;}
void PutWindowTilemap(u8 w){(void)w;}void CopyWindowToVram(u8 w,u8 mode){(void)w;(void)mode;}
u8 *ConvertIntToDecimalStringN(u8 *p,u32 n,u8 mode,u8 digits){(void)n;(void)mode;(void)digits;p[0]=255;return p;}
u8 *StringCopy(u8 *to,const u8 *from){while(*from) *to++=*from++;*to=255;return to;}
s32 GetStringWidth(u8 font,const u8 *p,s16 spacing){(void)font;(void)p;(void)spacing;return 0;}
u8 ListMenuInit(const struct ListMenuTemplate *p,u16 pos,u16 above){(void)p;lastCursor=pos;lastAbove=above;tasks++;return 0;}
void DestroyListMenuTask(u8 t,u16 *a,u16 *b){(void)t;(void)a;(void)b;assert(tasks);tasks--;}
s32 ListMenu_ProcessInput(u8 t){(void)t;return selected==2?2:LIST_NOTHING_CHOSEN;}
void ListMenuGetScrollAndRow(u8 t,u16 *a,u16 *b){(void)t;if(a)*a=0;if(b)*b=selected;}
bool8 PiUi_ViewerChecksum(void){return TRUE;}
int main(void){unsigned i;
 failAlloc=1;CB2_OpenPokeBook();assert(!allocated&&!sPb&&callback==CB2_ReturnToFieldWithOpenMenu);failAlloc=0;
 failWindows=1;CB2_OpenPokeBook();assert(!allocated&&!sPb&&!windows&&callback==CB2_ReturnToFieldWithOpenMenu);failWindows=0;
 for(i=0;i<30;i++){gMain.newKeys=0;CB2_OpenPokeBook();assert(allocated==2&&sPb&&windows&&gPiUi.state==1);gMain.newKeys=B_BUTTON;Main();assert(!allocated&&!sPb&&!windows&&!tasks&&gPiUi.state==0);}
 gMain.newKeys=0;CB2_OpenPokeBook();gPiUi.run_generation++;Main();assert(!sPb&&!allocated&&gPiUi.state==0);
 gMain.newKeys=0;CB2_OpenPokeBook();List(3,2);assert(lastCursor==0&&lastAbove==2);List(3,1);assert(lastCursor==0&&lastAbove==1);sPb->op=2;sPb->waiting=FALSE;selected=2;gMain.newKeys=A_BUTTON;Main();assert(sPb->feedCursor==2&&sPb->post==3);Exit();assert(!sPb&&!allocated&&!tasks);
 puts("actual-C selected-row restoration,screen allocation failure,partial window failure,30 pending cancellations,generation exit passed; hardware APIs substituted");return 0;}

#include "global.h"
#include "window.h"
#include "list_menu.h"
struct BgTemplate {u8 bg,charBaseIndex,mapBaseIndex,priority;};
#define REG_OFFSET_DISPCNT 0
#define REG_OFFSET_BLDCNT 1
#define REG_OFFSET_BLDY 2
#define REG_OFFSET_WIN0H 3
#define REG_OFFSET_WIN0V 4
#define BG_COORD_SET 0
#define BG_PLTT_ID(x) (x)
#define PLTT_SIZE_4BPP 32
#define DISPCNT_MODE_0 0
#define DISPCNT_BG0_ON 1
void *AllocZeroed(u32 n);void Free(void *p);
void SetVBlankCallback(void (*f)(void));void SetMainCallback2(void (*f)(void));
void ResetSpriteData(void);void FreeAllSpritePalettes(void);void SetGpuReg(u16 a,u16 b);
void ResetBgsAndClearDma3BusyFlags(u8 n);void InitBgsFromTemplates(u8 n,const struct BgTemplate *p,u8 c);
void SetBgTilemapBuffer(u8 n,void *p);void UnsetBgTilemapBuffer(u8 n);void ChangeBgX(u8 n,s32 x,u8 t);void ChangeBgY(u8 n,s32 y,u8 t);
void LoadPalette(const void *p,u16 n,u16 len);void DeactivateAllTextPrinters(void);void ResetPaletteFade(void);void ShowBg(u8 n);
void LoadOam(void);void ProcessSpriteCopyRequests(void);void TransferPlttBuffer(void);void UpdatePaletteFade(void);
void AddTextPrinterParameterized(u8 win,u8 font,const u8 *p,u8 x,u8 y,u8 speed,void *cb);
u8 *ConvertIntToDecimalStringN(u8 *p,u32 n,u8 mode,u8 digits);u8 *StringCopy(u8 *to,const u8 *from);
s32 GetStringWidth(u8 font,const u8 *p,s16 spacing);

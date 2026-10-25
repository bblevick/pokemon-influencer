#ifndef PB_TEST_GLOBAL_H
#define PB_TEST_GLOBAL_H
#include <stdint.h>
#include <stddef.h>
typedef uint8_t u8;typedef int8_t s8;typedef uint16_t u16;typedef int16_t s16;typedef uint32_t u32;typedef int32_t s32;
typedef u8 bool8;typedef u16 bool16;typedef u32 bool32;
#define TRUE 1
#define FALSE 0
#define _(s) s
#define FONT_NORMAL 2
#define STR_CONV_MODE_LEFT_ALIGN 0
#define A_BUTTON 1
#define B_BUTTON 2
#define DPAD_LEFT 32
#define DPAD_RIGHT 16
struct Main {u16 newKeys;};extern struct Main gMain;
#endif

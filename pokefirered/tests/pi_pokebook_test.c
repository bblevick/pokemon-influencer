#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;typedef u8 bool8;
#define TRUE 1
#define FALSE 0
#include "../include/pi_pokebook_wire.h"
static u8 p[96];
static void P16(u16 n,u16 v){p[n]=v;p[n+1]=v>>8;}
static void P32(u16 n,u32 v){P16(n,v);P16(n+2,v>>16);}
static void Base(u16 op){unsigned i;for(i=0;i<96;i++)p[i]=0;P16(0,2);P16(2,op);P32(4,1);P32(8,2);P32(12,3);P32(16,op==3?1:0);P16(22,1);}
static int V(u16 n,u16 op){return PbValidate(p,n,1,2,3,op==3?1:0,op,0);}
int main(void){unsigned c,n;Base(3);p[24]=0xbb;assert(V(25,3));
for(n=0;n<24;n++)assert(!V(n,3));assert(!V(97,3));
for(c=0;c<256;c++){Base(3);p[24]=c;assert(V(25,3)==PbChar(c));}
Base(3);for(n=24;n<47;n++)p[n]=0xbb;p[47]=0xfe;p[48]=0xd5;assert(V(49,3));p[47]=0xbb;assert(!V(49,3));
Base(3);p[24]=0xbb;P32(4,2);assert(!V(25,3));P32(4,1);P32(12,4);assert(!V(25,3));
Base(2);P32(24,1);p[28]=0xbb;p[29]=255;assert(V(47,2));p[30]=255;assert(!V(47,2));
Base(2);P16(22,0);assert(V(24,2));Base(3);P16(2,515);P16(22,0);assert(V(24,3));assert(!V(25,3));
puts("actual-C viewer validation: lengths,256 bytes, wrapping, identity, snapshots, labels, empty,errors passed");return 0;}

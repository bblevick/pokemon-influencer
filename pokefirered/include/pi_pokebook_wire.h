/* Viewer schema2. Pure validator also compiled by host actual-C tests. */
#ifndef GUARD_PI_POKEBOOK_WIRE_H
#define GUARD_PI_POKEBOOK_WIRE_H
static u16 Pb16(const u8 *p) {return p[0]|p[1]<<8;}
static u32 Pb32(const u8 *p) {return Pb16(p)|((u32)Pb16(p+2)<<16);}
static bool8 PbChar(u8 c) {return c==0 || (c>=0xa1 && c<=0xae) || c==0xb4 || c==0xb8 || c==0xba || (c>=0xbb && c<=0xee);}
static bool8 PbValidate(const u8 *p,u16 n,u32 req,u32 view,u32 snapshot,u32 post,u16 op,u16 page)
{
 u16 i,col=0,lines=1,rows;bool8 ended;
 if(n<24 || n>96 || Pb16(p)!=2 || (Pb16(p+2)&255)!=op || (Pb16(p+2)>>8)>2
 || Pb32(p+4)!=req || Pb32(p+8)!=view || Pb32(p+16)!=post || Pb16(p+20)!=page)return FALSE;
 if(op!=1 && Pb32(p+12)!=snapshot)return FALSE;
 if(Pb16(p+2)>>8)return n==24 && Pb16(p+22)==0;
 if(!Pb32(p+12))return FALSE;
 if(op==1)return n==28 && Pb16(p+22)<=192 && Pb32(p+24)<=192;
 if(Pb16(p+22)>64 || (Pb16(p+22) && page>=Pb16(p+22)))return FALSE;
 if(op==3)
 {
  if(n==24 || !Pb16(p+22))return FALSE;
  for(i=24;i<n;i++)
   if(p[i]==0xfe){if(!col || ++lines>3 || i==n-1)return FALSE;col=0;}
   else if(!PbChar(p[i]) || ++col>23)return FALSE;
  return TRUE;
 }
 if(op!=2 && op!=4)return FALSE;
 if((n-24)%23 || n>93 || ((n==24)!=(Pb16(p+22)==0)))return FALSE;
 rows=(n-24)/23;
 for(i=0;i<rows;i++)
 {
  u16 j;const u8 *q=p+24+i*23;
  if(Pb32(q)!=page*3+i+1)return FALSE;
  ended=FALSE;
  for(j=4;j<23;j++)
   if(ended){if(q[j])return FALSE;}
   else if(q[j]==255){if(j==4)return FALSE;ended=TRUE;}
   else if(!PbChar(q[j]))return FALSE;
  if(!ended)return FALSE;
 }
 return TRUE;
}
#endif

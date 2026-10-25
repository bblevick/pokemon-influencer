/* Controlled SYSTEM1-01A acceptance route, not rematch invitation UX. */
#include "global.h"
#include "pi_preparation.h"
#include "pi_events.h"
#include "pi_build.h"
#include "battle.h"
#include "battle_setup.h"
#include "pokemon.h"
#include "script.h"
#include "data.h"
#include "constants/trainers.h"
#include "constants/species.h"
#include "constants/moves.h"
#include "constants/battle.h"
#include "constants/battle_setup.h"
#include "characters.h"
volatile struct PiPreparationMailbox gPiPreparation __attribute__((section("pi_mailbox_data"),aligned(4)))={0};
static const u8 sReturnScript[]={0x6b,0x02}; /* releaseall; end, verified event.inc */
static const u8 sDefeatText[]={0xff};
static bool8 Valid(void)
{
 u32 h=2166136261u,i; const volatile u8 *b=(const volatile u8 *)&gPiPreparation;
 if(gPiPreparation.magic!=0x50525031 || gPiPreparation.tag!=PI_BUILD_TAG || !gPiPreparation.sequence
 || gPiPreparation.nonce!=gPiMailbox.nonce || gPiPreparation.generation!=gPiMailbox.generation
 || !gPiMailbox.nonce || gPiPreparation.trainer!=TRAINER_BUG_CATCHER_RICK || gPiPreparation.count!=2)return FALSE;
 for(i=8;i<20;i++)h=(h^b[i])*16777619u;
 for(i=24;i<59;i++)h=(h^b[i])*16777619u;
 for(i=72;i<sizeof(gPiPreparation);i++)h=(h^b[i])*16777619u;
 if(h!=gPiPreparation.checksum)return FALSE;
 for(i=0;i<gPiPreparation.count;i++) {
  u32 j; const volatile struct PiPreparedMon *p=&gPiPreparation.party[i];
  /* Source-backed opening capacity/species/levels/items, host whole-package validation is primary. */
  if(p->level<6 || p->level>10 || p->fixedIV!=0 || p->heldItem!=0)return FALSE;
  if((p->originalSpecies==SPECIES_WEEDLE && p->species!=SPECIES_WEEDLE && p->species!=SPECIES_KAKUNA && p->species!=SPECIES_BEEDRILL)
  ||(p->originalSpecies==SPECIES_CATERPIE && p->species!=SPECIES_CATERPIE && p->species!=SPECIES_METAPOD && p->species!=SPECIES_BUTTERFREE)
  ||(p->originalSpecies!=SPECIES_WEEDLE && p->originalSpecies!=SPECIES_CATERPIE)
  ||gPiPreparation.party[0].originalSpecies==gPiPreparation.party[1].originalSpecies)return FALSE;
  for(j=0;j<4;j++)if(p->moves[j]>=MOVES_COUNT)return FALSE;
 }
 return TRUE;
}
void PiPreparation_Init(void)
{
 u32 i;volatile u8 *p=(volatile u8 *)&gPiPreparation;
 for(i=0;i<sizeof(gPiPreparation);i++)p[i]=0;
 gPiPreparation.tag=PI_BUILD_TAG;gPiPreparation.magic=0x50525031;
}
bool8 PiPreparation_Field(void)
{
 u8 args[15];u32 address;
 if(!gPiPreparation.trigger)return FALSE;
 gPiPreparation.trigger=0;
 if(gPiPreparation.state!=1 || !Valid() || ArePlayerFieldControlsLocked() || ScriptContext_IsEnabled()) {gPiPreparation.error=1;return FALSE;}
 args[0]=TRAINER_BATTLE_SINGLE;args[1]=TRAINER_BUG_CATCHER_RICK;args[2]=0;args[3]=0;args[4]=0;
 address=(u32)sDefeatText;memcpy(args+5,&address,4);memcpy(args+9,&address,4);
 args[13]=0x6b;args[14]=0x02;
 BattleSetup_ConfigureTrainerBattle(args);
 /* Return pointer must be durable, not the parser's temporary argument buffer. */
 ScriptContext_SetupScript(sReturnScript);LockPlayerFieldControls();
 gPiPreparation.state=2;StartTrainerBattle();return TRUE;
}
u8 PiPreparation_CreateParty(struct Pokemon *party,u16 trainer)
{
 u32 i,j,nameHash=0,personality;
 if(gPiPreparation.state!=2 || trainer!=gPiPreparation.trainer || gBattleTypeFlags!=BATTLE_TYPE_TRAINER || !Valid())return 0;
 ZeroEnemyPartyMons();
 for(i=0;i<gPiPreparation.count;i++) {
  const volatile struct PiPreparedMon *p=&gPiPreparation.party[i];u16 item=p->heldItem;
  /* Stable personality uses original species/slot, not new evolution names. */
  nameHash=0;
  if(p->originalSpecies==SPECIES_CATERPIE) {
   for(j=0;gTrainers[trainer].trainerName[j]!=EOS;j++)nameHash+=gTrainers[trainer].trainerName[j];
   for(j=0;gSpeciesNames[SPECIES_WEEDLE][j]!=EOS;j++)nameHash+=gSpeciesNames[SPECIES_WEEDLE][j];
  }
  for(j=0;gTrainers[trainer].trainerName[j]!=EOS;j++)nameHash+=gTrainers[trainer].trainerName[j];
  for(j=0;gSpeciesNames[p->originalSpecies][j]!=EOS;j++)nameHash+=gSpeciesNames[p->originalSpecies][j];
  personality=0x88+(nameHash<<8);
  CreateMon(&party[i],p->species,p->level,p->fixedIV,TRUE,personality,OT_ID_RANDOM_NO_SHINY,0);
  SetMonData(&party[i],MON_DATA_HELD_ITEM,&item);
  for(j=0;j<4;j++) {u16 move=p->moves[j];SetMonData(&party[i],MON_DATA_MOVE1+j,&move);SetMonData(&party[i],MON_DATA_PP1+j,&gBattleMoves[move].pp);}
 }
 gPiPreparation.state=3;gPiPreparation.installations++;return gPiPreparation.count;
}

#ifndef GUARD_PI_PREPARATION_H
#define GUARD_PI_PREPARATION_H
#include "global.h"
#include <stddef.h>
struct PiPreparedMon { u16 species; u8 level, fixedIV; u16 moves[4], heldItem, originalSpecies; };
struct PiPreparationMailbox {
 u32 magic, tag, nonce, generation, sequence, checksum;
 u8 commitment[32];
 u16 trainer; u8 count, state;
 u32 trigger, installations, error;
 struct PiPreparedMon party[6];
};
typedef char PiPreparedMonSize[(sizeof(struct PiPreparedMon)==16)?1:-1];
typedef char PiPreparationSize[(sizeof(struct PiPreparationMailbox)==168)?1:-1];
typedef char PiPreparationPartyOffset[(offsetof(struct PiPreparationMailbox,party)==72)?1:-1];
extern volatile struct PiPreparationMailbox gPiPreparation;
void PiPreparation_Init(void);
bool8 PiPreparation_Field(void);
u8 PiPreparation_CreateParty(struct Pokemon *party,u16 trainer);
#endif

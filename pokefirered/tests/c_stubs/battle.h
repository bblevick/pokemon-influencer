#ifndef PI_TEST_BATTLE_H
#define PI_TEST_BATTLE_H
#include "global.h"
struct BattlePokemon {u16 species,hp,maxHP,moves[4];u8 pp[4];u32 status1;};
extern struct BattlePokemon gBattleMons[4];
extern u32 gBattleTypeFlags;
extern u16 gTrainerBattleOpponent_A,gBattlerPartyIndexes[4],gCurrentMove;
extern u8 gBattlersCount,gBattlerAttacker,gBattleOutcome;
#endif

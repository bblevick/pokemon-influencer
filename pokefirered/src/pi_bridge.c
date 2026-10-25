#include "global.h"
#include "pi_protocol.h"
#include "pi_build.h"
#include "main.h"

#if PI_BRIDGE && !PI_EVENTS
/* Dedicated linker section, outside heap and all existing EWRAM globals. */
const u32 gPiBuildTag = PI_BUILD_TAG;
const u32 gPiCompiledLayout[] = {sizeof(struct PiMailbox),
    offsetof(struct PiMailbox, magic),
    offsetof(struct PiMailbox, version),
    offsetof(struct PiMailbox, size),
    offsetof(struct PiMailbox, build_tag),
    offsetof(struct PiMailbox, nonce),
    offsetof(struct PiMailbox, generation),
    offsetof(struct PiMailbox, sequence),
    offsetof(struct PiMailbox, response_sequence),
    offsetof(struct PiMailbox, response_nonce),
    offsetof(struct PiMailbox, response_generation),
    offsetof(struct PiMailbox, state),
    offsetof(struct PiMailbox, message_type),
    offsetof(struct PiMailbox, length),
    offsetof(struct PiMailbox, result),
    offsetof(struct PiMailbox, error),
    offsetof(struct PiMailbox, reserved),
    offsetof(struct PiMailbox, checksum),
    offsetof(struct PiMailbox, heartbeat),
    offsetof(struct PiMailbox, deadline),
    offsetof(struct PiMailbox, last_ack),
    offsetof(struct PiMailbox, successes),
    offsetof(struct PiMailbox, failures),
    offsetof(struct PiMailbox, debug_trigger),
    offsetof(struct PiMailbox, payload)};
volatile struct PiMailbox gPiMailbox __attribute__((section("pi_mailbox_data"), aligned(4))) = {0};

static u32 PiChecksum(bool32 response)
{
    u32 hash = 2166136261u;
    u32 words[4];
    u32 i, j;
    words[0] = response ? gPiMailbox.response_sequence : gPiMailbox.sequence;
    words[1] = response ? gPiMailbox.response_nonce : gPiMailbox.nonce;
    words[2] = response ? gPiMailbox.response_generation : gPiMailbox.generation;
    words[3] = gPiMailbox.message_type | ((u32)gPiMailbox.length << 16);
    for (i = 0; i < 4; i++)
        for (j = 0; j < 4; j++)
            hash = (hash ^ ((words[i] >> (j * 8)) & 255)) * 16777619u;
    for (i = 0; i < gPiMailbox.length; i++)
        hash = (hash ^ gPiMailbox.payload[i]) * 16777619u;
    return hash;
}

static void PiError(u16 code)
{
    gPiMailbox.error = code;
    gPiMailbox.failures++;
    gPiMailbox.state = PI_STATE_ERROR;
}

void PiBridge_Init(void)
{
    u32 i;
    volatile u8 *bytes = (volatile u8 *)&gPiMailbox;
    for (i = 0; i < sizeof(gPiMailbox); i++)
        bytes[i] = 0;
    gPiMailbox.version = PI_VERSION;
    gPiMailbox.size = sizeof(gPiMailbox);
    gPiMailbox.build_tag = PI_BUILD_TAG;
    /* Publish magic last; emulator is not permitted to touch uninitialized RAM. */
    gPiMailbox.magic = PI_MAGIC;
}

void PiBridge_Tick(void)
{
    gPiMailbox.heartbeat++;
    if (gPiMailbox.magic != PI_MAGIC || gPiMailbox.size != sizeof(gPiMailbox))
    {
        if (gPiMailbox.error != PI_ERR_MALFORMED)
            PiError(PI_ERR_MALFORMED);
        return;
    }
    if (gPiMailbox.version != PI_VERSION || gPiMailbox.build_tag != PI_BUILD_TAG)
    {
        if (gPiMailbox.error != PI_ERR_VERSION)
            PiError(PI_ERR_VERSION);
        return;
    }
    if (gPiMailbox.state == PI_STATE_RESPONSE_READY)
    {
        if (gPiMailbox.response_sequence != gPiMailbox.sequence
         || gPiMailbox.response_nonce != gPiMailbox.nonce
         || gPiMailbox.response_generation != gPiMailbox.generation)
            PiError(PI_ERR_STALE);
        else if (gPiMailbox.length != 4 || gPiMailbox.message_type != PI_TYPE_PONG
              || gPiMailbox.result != 0 || gPiMailbox.checksum != PiChecksum(TRUE)
              || gPiMailbox.payload[0] != 'P' || gPiMailbox.payload[1] != 'O'
              || gPiMailbox.payload[2] != 'N' || gPiMailbox.payload[3] != 'G')
            PiError(PI_ERR_MALFORMED);
        else
        {
            gPiMailbox.last_ack = gPiMailbox.sequence;
            gPiMailbox.successes++;
            gPiMailbox.state = PI_STATE_IDLE;
        }
    }
    else if (gPiMailbox.state == PI_STATE_REQUEST_READY || gPiMailbox.state == PI_STATE_REQUEST_IN_PROGRESS)
    {
        if ((u32)(gPiMailbox.heartbeat - gPiMailbox.deadline) < 0x80000000u)
            PiError(PI_ERR_TIMEOUT);
    }
    else if (gPiMailbox.state == PI_STATE_ERROR)
        gPiMailbox.state = PI_STATE_IDLE; /* Retain sticky error/counters for diagnostics. */
    else if (gPiMailbox.state != PI_STATE_IDLE)
        PiError(PI_ERR_MALFORMED);
#if PI_BRIDGE_TEST
    else if (gPiMailbox.debug_trigger == 1
          || ((gMain.heldKeys & (L_BUTTON | R_BUTTON)) == (L_BUTTON | R_BUTTON)
           && (gMain.newKeys & SELECT_BUTTON)))
    {
        gPiMailbox.debug_trigger = 0;
        if (gPiMailbox.sequence == 0xFFFFFFFFu)
        {
            PiError(PI_ERR_STALE); /* No sequence reuse in a session; reset/reload bridge. */
            return;
        }
        gPiMailbox.sequence++;
        gPiMailbox.message_type = PI_TYPE_PING;
        gPiMailbox.length = 4;
        gPiMailbox.result = 0;
        gPiMailbox.error = PI_ERR_NONE;
        gPiMailbox.payload[0] = 'P'; gPiMailbox.payload[1] = 'O';
        gPiMailbox.payload[2] = 'K'; gPiMailbox.payload[3] = 'E';
        gPiMailbox.deadline = gPiMailbox.heartbeat + PI_TIMEOUT_FRAMES;
        gPiMailbox.checksum = PiChecksum(FALSE);
        gPiMailbox.state = PI_STATE_REQUEST_READY; /* Publish after payload/header. */
    }
#endif
}
#endif

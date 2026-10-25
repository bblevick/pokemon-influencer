This should lock down an extremely important principle:
Jev receives observations and choices; it does not receive authority.

For example:
{
  "battle_id": "B-019283",
  "turn": 7,

  "trainer": {
    "id": 183,
    "personality": {
      "risk_tolerance": 0.31,
      "competitiveness": 0.82
    }
  },

  "strategy": {
    "preserve_ace": true,
    "fire_threat": "high",
    "status_preference": "medium"
  },

  "battle_state": {
    "self_active": "Butterfree",
    "self_hp_percent": 0.61,
    "opponent_active": "Charmeleon",
    "opponent_hp_percent": 0.42
  },

  "known_opponent_information": {
    "revealed_moves": [
      "Ember",
      "Scratch"
    ]
  },

  "recent_turns": [
    "...",
    "..."
  ]
}
Then legal choices:
A = Confusion
B = Gust
C = Sleep Powder
D = Switch to Beedrill
E = Potion on Butterfree
Jev answers:
A 0.51
B 0.06
C 0.18
D 0.19
E 0.06
We select A.
OpenRouter currently describes Jev precisely as a structured System One decision model that accepts text state and returns typed choices/probabilities rather than free-form text. The pinned typesafe/jev-1.13 currently exposes a 32K context window.

Don't pass the entire NPC memory into Jev.
Do:
WORLD MEMORY
     │
     ▼
Hermes
     │
     ▼
relevant beliefs
     │
     ▼
StrategicPosture
     │
     ▼
System One
Not:
thousands of NPC memories
         ↓
        Jev
That creates a nice cognitive hierarchy.
For instance Hermes produces:
risk_tolerance: 0.35
preserve_ace: true

opponent_model:
  fire_dependency: 0.78
  switch_frequency: 0.16
  aggression: 0.73

goals:
  - preserve Butterfree if possible
  - punish predictable stay-ins
  - seek status opportunities

confidence:
  opponent_model: 0.69
Jev doesn't need to know why Rick believes those things.
It just needs the resulting posture.
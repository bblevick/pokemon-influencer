I would spell out that Hermes is not the database.
Hermes becomes the reasoning/orchestration layer over our Pokémon world.
Hermes Puppeteer
       │
       ├── get_npc_context()
       ├── retrieve_memories()
       ├── get_relationship()
       ├── inspect_social_graph()
       ├── inspect_recent_events()
       ├── inspect_pokebook_feed()
       │
       ├── propose_belief_update()
       ├── propose_social_action()
       ├── propose_post()
       ├── propose_relationship_change()
       └── request_strategy_update()
Those should ultimately become Hermes tools.
Hermes's plugin system is well suited to this: project/user plugins can add tools, while custom memory-provider plugins implement persistent cross-session knowledge. GitHub
And importantly, Hermes itself supports provider plugins for inference backends, so the Puppeteer shouldn't care whether we're using Claude, GPT, Gemini, Qwen, etc. GitHub
For our world memory, I still would not rely on standard MEMORY.md. Hermes documents that built-in memory as deliberately bounded—roughly 800 tokens for MEMORY.md—so our full NPC/event/social state belongs in the Pokémon world store exposed to Hermes through tools or a project memory provider
#!/usr/bin/env python3
"""Generate fixture to run in pinned mGBA Lua interpreter; no game memory writes."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'native/battle01/transport.lua').read_text();f=s[s.index('function PI_BATTLE_receive'):s.index('function PI_BATTLE_arm')]
t=(ROOT/'tests/battle01_response_fixture.lua').read_text().replace('-- INSERT ACTUAL PI_BATTLE_receive',f)
p=ROOT/'.local/battle01/lua-contract-tests.lua';p.write_text(t);print(p)

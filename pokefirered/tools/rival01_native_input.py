#!/usr/bin/env python3
"""Logged ordinary button automation for isolated constructor qualification."""
import sys,socket,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase8/rival01-prerequisites'
commands=sys.argv[1:]
with socket.create_connection(('127.0.0.1',18793),timeout=2) as s:
 s.settimeout(2)
 for c in commands:
  if c.split()[0] not in ('key','shot','sample','a','arm'):raise ValueError('qualification input allowlist')
  s.sendall((c+'\n').encode());assert s.recv(128)==b'OK\n',c
with (E/'native-inputs.jsonl').open('a') as f:f.write(json.dumps({'atUnix':time.time(),'commands':commands,'kind':'isolated normal buttons; arm existing control interface only'})+'\n')

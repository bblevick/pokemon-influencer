#!/usr/bin/env python3
"""Bounded emulator-test commands, not gameplay bridge RPC."""
import json
from pathlib import Path
import socket
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
deadline=time.monotonic()+5
while True:
    try:
        s=socket.create_connection(('127.0.0.1',18773),timeout=2)
        s.settimeout(3);s.sendall(b'sample\n')
        if s.recv(128).strip()!=b'OK':raise ConnectionError('readiness response')
        break
    except OSError:
        if 's' in globals():s.close()
        if time.monotonic()>deadline:raise
        time.sleep(.1)
with s:
    for command in sys.argv[1:]:
        if len(command)>96 or '\n' in command:raise ValueError('command bounds')
        s.sendall((command+'\n').encode('ascii'));reply=s.recv(128).decode().strip()
        with (ROOT/'evidence/phase1/bridge02/input-commands.jsonl').open('a') as f:f.write(json.dumps({'command':command,'response':reply})+'\n')
        print(command+': '+reply)
        if reply!='OK':raise SystemExit(1)

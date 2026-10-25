#!/usr/bin/env python3
"""Send bounded input-test commands to the Phase 0 Lua diagnostic, not a ROM bridge."""
from pathlib import Path
import socket
import sys
import json
import time
root=Path(__file__).resolve().parents[1]
with socket.create_connection(('127.0.0.1',18766),timeout=3) as sock:
    sock.settimeout(3)
    data=('\n'.join(sys.argv[1:])+'\n').encode('ascii')
    sock.sendall(data)
    expected=len(sys.argv)-1
    response=b''
    while response.count(b'\n')<expected:
        part=sock.recv(1024)
        if not part: raise RuntimeError('Disconnected before command acknowledgments')
        response+=part
with (root/'evidence/phase0/input-commands.jsonl').open('a') as log:
    log.write(json.dumps({'commands':sys.argv[1:],'response':response.decode(),'time_monotonic':time.monotonic()})+'\n')
print(response.decode().strip())
if response!=b'OK\n'*expected: sys.exit(1)

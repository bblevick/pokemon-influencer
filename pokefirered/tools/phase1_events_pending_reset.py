#!/usr/bin/env python3
"""Live test only: normal A taps, then explicit reset on an observed pending event.
Requires host stopped, a reviewed trainer intro and no queued gameplay driver.
One input connection; finite taps/deadline; never retries ambiguous commands.
"""
import json,re,socket,time
from pathlib import Path
from phase1_events_scenario import ROOT,LOG,task_lock

def tail_samples():
    with LOG.open('rb') as f:
        f.seek(max(0,LOG.stat().st_size-32768));lines=f.read().decode().splitlines()[1:]
    rows=[json.loads(x) for x in lines]
    return next(x for x in reversed(rows) if x['event']=='sample')

with task_lock(),socket.create_connection(('127.0.0.1',18773),timeout=2) as sock:
    def command(s):
        sock.sendall((s+'\n').encode());assert sock.recv(128).strip()==b'OK'
    deadline=time.monotonic()+15;next_tap=0;taps=0;before=None
    while time.monotonic()<deadline:
        command('sample');r=tail_samples()
        fields={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',r['detail'])}
        if fields['state'] in (1,2) and fields['sequence']>0:
            before=r
            # Reset can unwind the callback before its test-socket reply. Never
            # repeat that consequential command; verify independent live state.
            try:command('reset');reply_timeout=False
            except TimeoutError:reply_timeout=True
            break
        if time.monotonic()>=next_tap and taps<6:
            command('key 0 1 180');taps+=1;next_tap=time.monotonic()+1.8
        time.sleep(.04) # Host test only; emulator callback never sleeps.
    assert before,'No pending event observed; reset not performed'
    sock.close()
    time.sleep(.5)
    sock=socket.create_connection(('127.0.0.1',18773),timeout=2)
    command('sample');after=tail_samples();sock.close()
    post={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',after['detail'])}
    assert post['state']==0 and post['sequence']==0 and post['ack']==0
    cfg=json.loads((ROOT/'.local/phase1-events-launch.json').read_text())
    m=json.loads((ROOT/cfg['manifest']).read_text())
    result={'session':cfg['nonce'],'romSHA256':m['rom_sha256'],'before':before,'after':after,
            'normalATaps':taps,'resetCommand':'reset','resetReplyTimedOut':reply_timeout,
            'scope':'live pending event and emulator reset; no host/save pairing'}
    (ROOT/'evidence/phase1/bridge02/pending-reset.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

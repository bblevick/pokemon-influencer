#!/usr/bin/env python3
"""Existing single-writer offline host plus deterministic tactical boundary."""
import sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from battle01_launch import E,PRIVATE,CONFIG,SCREENS,manifest,open_store,save_identity
from battle.transport import Handler
import strategy01_host as retained

def main():
 p=argparse.ArgumentParser();p.add_argument('--policy',choices=['first_move','switch_once','timeout','unavailable','delayed'],default='first_move');a=p.parse_args();
 from battle.domain import DelayedTestProvider
 handler=Handler(manifest(),E,a.policy,DelayedTestProvider() if a.policy=='delayed' else None)
 # Retain all event ACK, paired-save, mandatory offline recap and viewer handling.
 # Only add the dedicated tactical envelope dispatch to this isolated runtime.
 source=(ROOT/'tools/strategy01_host.py').read_text();source=source[:source.index("if __name__=='__main__':")]
 source=source.replace("       elif msg.kind==1 and msg.typ==5:","       elif msg.kind in (8,10):\n        try:battle_handler.receive(msg,w,sock)\n        except (ValueError,KeyError,struct.error) as error:log('tactical-rejected',reason=str(error))\n       elif msg.kind==1 and msg.typ==5:")
 source=source.replace('      saves();generation()', '      battle_handler.tick(w,sock);saves();generation()')
 source=source.replace("   except OSError as error:log('connection-ended',reason=str(error))","   except OSError as error:battle_handler.cancel();log('connection-ended',reason=str(error))")
 namespace={'__name__':'battle01_retained_host','battle_handler':handler};exec(compile(source,'retained-offline-host','exec'),namespace)
 for n in ('E','PRIVATE','CONFIG','SCREENS','manifest','open_store','save_identity'):namespace[n]=globals()[n]
 try:namespace['run'](1800)
 finally:handler.close()
if __name__=='__main__':main()

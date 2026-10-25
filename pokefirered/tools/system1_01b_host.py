#!/usr/bin/env python3
"""Same single-writer BATTLE-01 runtime; only explicit shadow/enabled live role."""
import sys,json,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from system1_01b_launch import E,PRIVATE,CONFIG,SCREENS,manifest,open_store,save_identity
from battle.live import LiveBattleProvider
from battle.transport import Handler
from system1_01b_preflight import refresh
import battle01_host as retained
class LiveHandler(Handler):
 def __init__(self,m,e,*args,**kwargs):super().__init__(m,e,provider=LiveBattleProvider(),shadow=MODE=='shadow',decision_source='mercury',decision_seconds=2.75)
MODE=None
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ('shadow','enabled'):raise ValueError('explicit shadow or enabled required')
 MODE=sys.argv[1]
 if MODE=='enabled' and not (E/'shadow-accepted.json').exists():raise ValueError('enabled requires passed shadow evidence')
 refresh();stop=threading.Event()
 def metadata():
  while not stop.wait(50):
   try:refresh()
   except Exception:pass # existing TTL/free guard fails closed; never blocks game writer
 thread=threading.Thread(target=metadata,name='public-route-refresh',daemon=True);thread.start()
 for n in ('E','PRIVATE','CONFIG','SCREENS','manifest','open_store','save_identity'):setattr(retained,n,globals()[n])
 retained.Handler=LiveHandler;sys.argv=[sys.argv[0],'--policy','first_move']
 try:retained.main()
 finally:stop.set();thread.join(16)

#!/usr/bin/env python3
"""Reuse accepted source-collision native walking with isolated campaign evidence."""
import sys,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import prep01_route as retained
from vertical_slice01_host import E,PRIVATE,open_store
from vertical_slice01_input import segment
retained.E=E;retained.open_store=open_store;retained.segment=segment
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('map');p.add_argument('x',type=int);p.add_argument('y',type=int);p.add_argument('--label',required=True);p.add_argument('--bound',type=int,default=40);a=p.parse_args()
 out=retained.walk(a.map,(a.x,a.y),a.label,bound=a.bound,config_path=PRIVATE/'launch.json')
 (E/(a.label+'-route.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

#!/usr/bin/env python3
import sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import strategy01_transport_input as retained
from system1_01a_launch import E,SCREENS
retained.E=E
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('commands',nargs='+');a=p.parse_args();retained.send(*a.commands)

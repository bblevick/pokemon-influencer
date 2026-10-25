#!/usr/bin/env python3
"""Native navigation through the retained input driver; never domain mutations."""
import sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from campaign.provider import E,PRIVATE
import strategy01_input as driver
SCREENS=ROOT/'evidence/private/vertical_slice01'
driver.E=E;driver.PRIVATE=PRIVATE;driver.SCREENS=SCREENS;driver.CONFIG=PRIVATE/'launch.json';driver.retained.E=E
segment=driver.segment
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('commands',nargs='+');a=p.parse_args();print(segment(a.label,a.commands))

#!/usr/bin/env python3
"""Offline gate harness on isolated C1. Explicitly refuses hosted flags."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
import campaign_expansion01 as base
if any(x in sys.argv for x in ('--live','--continue-authorized-run','--gym-closeout')):raise ValueError('gate repair authorizes zero hosted generation')
base.E=ROOT/'evidence/phase6/campaign_expansion01_gate_repair';base.PRIVATE=ROOT/'.local/campaign_expansion01_gate_repair'
import campaign.runtime,campaign.expansion_runtime
campaign.runtime.E=base.E;campaign.expansion_runtime.E=base.E
if __name__=="__main__":base.main()

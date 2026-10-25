#!/usr/bin/env python3
"""Managed PREP helpers, accepted unmodified ROM and separate test lineage copy."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prep.store import PrepStore
from pokebook01 import manifest,save_identity
E=ROOT/'evidence/phase3/prep01'
def open_store(path):
 m=manifest();return PrepStore(path,m['rom_sha256'],m['build_tag'])

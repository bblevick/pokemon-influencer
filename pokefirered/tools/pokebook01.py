#!/usr/bin/env python3
"""POKEBOOK managed final-build helpers. No inference."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from phase1_ui_build import verify_ui
from world.saves import fingerprint,layout_from_build
from puppeteer.store import PuppeteerStore
E=ROOT/'evidence/phase2/pokebook01'
def manifest():
 m=json.loads((E/'manifest-enabled.json').read_text());verify_ui(m)
 if m.get('viewer_schema_version')!=2:raise ValueError('viewer schema')
 return m
def open_store(path):
 m=manifest();return PuppeteerStore(path,m['rom_sha256'],m['build_tag'])
def save_identity(path):return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/manifest()['rom_path']))

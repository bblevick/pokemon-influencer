#!/usr/bin/env python3
"""Reproduce species rendering names from the pinned upstream Git objects."""
import argparse,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COMMIT='037335f4c725d7c9aecdac87066f2002b4bd7e14'
FILES=['include/constants/species.h','src/data/text/species_names.h']
def catalog():
    constants,text=[subprocess.check_output(['git','show',COMMIT+':'+p],cwd=ROOT,text=True) for p in FILES]
    numbers={k:int(v) for k,v in re.findall(r'^#define (SPECIES_\w+)\s+(\d+)\b',constants,re.M)}
    names={str(numbers[k]):v for k,v in re.findall(r'\[(SPECIES_\w+)\]\s*=\s*_\("([^"]+)"\)',text) if k in numbers and k not in ('SPECIES_NONE','SPECIES_EGG')}
    return {'sourceCommit':COMMIT,'sourceFiles':FILES,'names':names}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();target=ROOT/'config/social_species_names.json';expected=catalog()
    if a.write:target.write_text(json.dumps(expected,indent=2)+'\n')
    elif json.loads(target.read_text())!=expected:raise ValueError('catalog differs from pinned source')
    print(json.dumps({'passed':True,'sourceCommit':COMMIT,'names':len(expected['names'])}))

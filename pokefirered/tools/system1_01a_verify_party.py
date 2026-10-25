#!/usr/bin/env python3
"""Decode only constructed opponent BoxPokemon using pinned source substruct map."""
import sys,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from system1_01a_launch import E,SCREENS,PRIVATE,open_store
from roster.extract import digest

def decode(row):
 b=bytes.fromhex(row['pokemonBytes']);personality,ot=struct.unpack_from('<II',b);key=personality^ot;clear=b''.join(struct.pack('<I',x^key) for x in struct.unpack_from('<12I',b,32))
 if sum(struct.unpack('<24H',clear))&0xffff!=struct.unpack_from('<H',b,28)[0]:raise ValueError('native Box checksum')
 mapping={int(n):[int(x) for x in rest.split(',')] for n,rest in re.findall(r'SUBSTRUCT_CASE\(\s*(\d+),([\d,]+)\)',(ROOT/'src/pokemon.c').read_text())};offsets=mapping[personality%24];growth=clear[offsets[0]*12:offsets[0]*12+12];attacks=clear[offsets[1]*12:offsets[1]*12+12]
 species,item=struct.unpack_from('<HH',growth);moves=list(struct.unpack_from('<4H',attacks));return {'species':species,'level':row['level'],'moves':moves,'heldItem':item},list(attacks[8:12]),personality

def main():
 raw=json.loads((SCREENS/'native-party-private.json').read_text());rows=[decode(r) for r in raw['party']];receipt={k:raw[k] for k in ('nativeConstructorCount','nonce','generation','nativeROM','commitmentDigest')};receipt['party']=[r[0] for r in rows]
 with open_store(PRIVATE/'world.sqlite3') as w:
  c=w.locked_preparation('trainer:fr:trainer:0102');expected=[next(p for p in c['candidate']['party'] if p['lineage']==lineage) for lineage in c['candidate']['order']]
  if receipt['party']!=[{k:p[k] for k in ('species','level','moves','heldItem')} for p in expected]:raise ValueError('native party mismatch')
  for party,pp,personality in rows:
   if pp!=[w.content.cat.lookup('moves',m)['pp'] if m else 0 for m in party['moves']]:raise ValueError('native PP mismatch')
  r=w.record_installation(c['encounterID'],receipt)
 (E/'native-installation.json').write_text(json.dumps({'installation':r,'partyPP':[r[1] for r in rows],'personalities':[r[2] for r in rows],'nativeObservationSHA256':digest(raw),'privateBytesPublished':False},indent=2)+'\n');print('Actual native constructor party matches locked commitment and PP.')
if __name__=='__main__':main()

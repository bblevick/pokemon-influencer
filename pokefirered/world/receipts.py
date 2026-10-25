"""Bounded complete-line lifecycle receipt reader; crash tails stay unconsumed."""
import json
from pathlib import Path

def read_receipts(path,offset):
 path=Path(path)
 if not path.exists():return [],offset
 if path.stat().st_size<offset:raise ValueError('lifecycle receipt file truncated')
 with path.open('rb') as f:f.seek(offset);chunk=f.read(4096)
 end=chunk.rfind(b'\n')+1
 if not end:
  if len(chunk)>512:raise ValueError('oversized lifecycle receipt')
  return [],offset
 lines=chunk[:end].splitlines()
 if any(len(line)>512 for line in lines):raise ValueError('oversized lifecycle receipt')
 return [json.loads(line) for line in lines],offset+end

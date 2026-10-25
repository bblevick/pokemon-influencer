"""Shared canonical hashes without loading game/world services."""
import json,hashlib
from pathlib import Path
def canonical(obj): return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
def digest(obj): return hashlib.sha256(canonical(obj)).hexdigest()
def file_hash(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

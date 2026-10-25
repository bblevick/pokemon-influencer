"""Durable transport receipts; canonical authority still commits before ACK.

NativeWitness is supplied by a trusted managed runtime, never by a model or a
socket peer. It establishes a still-live native counterpart; a battery hash or
checksum alone cannot substitute for that witness.
"""
import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from bridge.events import decode_event
from bridge.events_wire import Decoder
from world.store import WorldError, dump

@dataclass(frozen=True)
class NativeWitness:
    build: str
    nonce: int
    run: int
    origin: str
    loaded_fingerprint: str
    process_identity: str
    frame: int
    event_counter: int
    ack: int
    drops: int
    counterpart_available: bool
    physical_build: str | None = None
    physical_tag: int | None = None

    def validate(self, w, message):
        launch = w._launch(message.nonce, message.generation)
        if not self.counterpart_available or not self.process_identity:
            raise WorldError('native counterpart unavailable; restore verified pair')
        compatibility = getattr(w, 'compatibility', {})
        expected_build = compatibility.get('nativeROM', w.build)
        expected_tag = compatibility.get('nativeTag', w.tag)
        if (self.physical_build or self.build, self.physical_tag or message.tag) != (expected_build, expected_tag) or message.tag != expected_tag:
            raise WorldError('native witness physical build mismatch')
        if (self.build, self.nonce, self.run, self.origin, self.loaded_fingerprint) != (
            w.build, message.nonce, message.generation, launch['id'], launch['loaded_fingerprint']
        ):
            raise WorldError('native witness launch/build/generation mismatch')
        if self.drops or not 0 <= self.ack <= self.event_counter or message.sequence > self.event_counter:
            raise WorldError('native witness gap/counter mismatch')
        return launch

class Inbox:
    VERSION = 1
    def __init__(self, path):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS receipts(
          identity TEXT PRIMARY KEY, wire TEXT NOT NULL, payload_hash TEXT NOT NULL,
          scope TEXT NOT NULL, witness TEXT NOT NULL, received_at REAL NOT NULL,
          result TEXT);
        CREATE TABLE IF NOT EXISTS recovery_audit(
          id INTEGER PRIMARY KEY, identity TEXT NOT NULL, disposition TEXT NOT NULL,
          method TEXT NOT NULL, version INTEGER NOT NULL, at REAL NOT NULL);
        CREATE TRIGGER IF NOT EXISTS immutable_receipt_delete BEFORE DELETE ON receipts
          BEGIN SELECT RAISE(ABORT,'immutable transport receipt'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_receipt_content BEFORE UPDATE OF
          identity,wire,payload_hash,scope,witness,received_at ON receipts
          BEGIN SELECT RAISE(ABORT,'immutable transport receipt'); END;
        ''')
        if 'provenance' not in {r['name'] for r in self.db.execute('PRAGMA table_info(recovery_audit)')}:
            self.db.execute('ALTER TABLE recovery_audit ADD COLUMN provenance TEXT')
    def close(self):
        self.db.close()
    def identity(self, w, message):
        return f'{w.build}:{message.nonce}:{message.generation}:{message.sequence}'
    def stage(self, w, message, native):
        decode_event(message)  # Reject invalid schema/inner identity before retention.
        launch = native.validate(w, message)
        c = w.campaign()
        identity = self.identity(w, message)
        wire = message.encode().hex()
        old = self.db.execute('SELECT * FROM receipts WHERE identity=?', (identity,)).fetchone()
        if old:
            if old['wire'] != wire:
                raise WorldError('conflicting duplicate transport receipt')
            return identity
        scope = {'campaign': c['id'], 'branch': c['active_branch'], 'cursor': c['cursor'],
                 'origin': launch['id'], 'loadedFingerprint': launch['loaded_fingerprint'],
                 'nonce': message.nonce, 'run': message.generation, 'sequence': message.sequence,
                 'build': w.build, 'tag': w.tag,
                 'physicalBuild': native.physical_build or native.build, 'physicalTag': message.tag}
        # This is a transport receipt, not canonical application or permission to ACK.
        self.db.execute('INSERT INTO receipts VALUES (?,?,?,?,?,?,NULL)', (
            identity, wire, hashlib.sha256(message.payload).hexdigest(), dump(scope),
            dump(native.__dict__), time.time()))
        return identity
    def apply(self, w, identity, native, method='delivery', failure='none'):
        row = self.db.execute('SELECT * FROM receipts WHERE identity=?', (identity,)).fetchone()
        if row is None:
            raise WorldError('unknown durable receipt')
        decoder = Decoder()
        packets = decoder.feed(bytes.fromhex(row['wire']))
        if len(packets) != 1 or decoder.buffer:
            raise WorldError('durable receipt wire framing')
        message = packets[0]
        native.validate(w, message)
        prior_native = json.loads(row['witness'])
        if native.process_identity != prior_native['process_identity'] or native.frame < prior_native['frame']:
            raise WorldError('native counterpart replaced/reset after receipt')
        scope = json.loads(row['scope'])
        c = w.campaign()
        if c['id'] != scope['campaign']:
            raise WorldError('receipt belongs to different campaign')
        existing = w._one('SELECT * FROM deliveries WHERE identity=?', (identity,))
        if existing:
            # The accepted NativePreparationStore adapter preserves physical
            # provenance separately and normalizes only the audited build tag.
            canonical_wire = replace(message, tag=w.tag).encode().hex()
            if existing['wire'] != canonical_wire:
                raise WorldError('conflicting committed receipt')
            if existing['event'] and existing['event'] not in {e['eventID'] for e in w.get_canonical_events()}:
                raise WorldError('receipt belongs to inactive future branch')
            if not existing['event'] and c['active_branch'] != scope['branch']:
                raise WorldError('observation receipt branch changed')
        elif c['active_branch'] != scope['branch'] or c['cursor'] < scope['cursor']:
            raise WorldError('unapplied receipt branch/cutoff changed')
        # WorldStore enforces contiguous sequence, native battle lifecycle, branch,
        # canonical origin and transaction atomicity. No domain-table edits here.
        result = w.ingest(message)
        if result['duplicate'] and failure == 'none':
            failure = 'repeated-delivery; prior-commit-retained'
        frozen = dump(result)
        if row['result'] is None:
            self.db.execute('UPDATE receipts SET result=? WHERE identity=?', (frozen, identity))
        provenance = {'attemptID': str(uuid.uuid4()), 'originalEventID': result.get('eventID'),
                      'originalTransportIdentity': identity, 'payloadSHA256': row['payload_hash'],
                      'origin': scope['origin'], 'nonce': scope['nonce'], 'generation': scope['run'],
                      'sequence': scope['sequence'], 'campaign': scope['campaign'],
                      'captureBranch': scope['branch'], 'failureClassification': failure,
                      'tool': 'bridge.continuity.Inbox', 'version': self.VERSION}
        self.db.execute('INSERT INTO recovery_audit(identity,disposition,method,version,at,provenance) VALUES (?,?,?,?,?,?)', (
            identity, 'duplicate' if result['duplicate'] else 'applied', method, self.VERSION, time.time(), dump(provenance)))
        return result
    def pending(self):
        return [dict(r) for r in self.db.execute('SELECT * FROM receipts WHERE result IS NULL ORDER BY received_at,identity')]

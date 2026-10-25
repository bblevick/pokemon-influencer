"""Host-only typed fixtures. New live acceptance is recorded separately."""
import json
import sqlite3
import struct
import tempfile
import unittest
from pathlib import Path
from test_world01 import BUILD, TAG, SIZES, flash, msg
from bridge.events_wire import Message
from world.store import WorldStore, WorldError, dump
from world.saves import fingerprint
from memory.store import MemoryStore, actor_id

RICK = actor_id('fr:trainer:0102')
JANICE = actor_id('fr:trainer:0116')


def visible(seq, turn=1, nonce=100):
    m = msg(seq, 6, turn=turn, nonce=nonce)
    data = bytearray(m.payload)
    struct.pack_into('<4H', data, 24 + 28, 33, 0, 0, 0)
    return Message(m.kind, m.nonce, m.generation, m.sequence, m.tag, m.typ, bytes(data))


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'memory.sqlite3'
        self.w = MemoryStore(self.path, BUILD, TAG)
        self.s1 = fingerprint(flash(), SIZES)
        self.w.import_save(self.s1)
        self.w.authorize_launch(100, self.s1)

    def tearDown(self):
        self.w.close()
        self.tmp.cleanup()

    def battle(self):
        for m in [msg(1), msg(2, 2), visible(3), msg(4, 3), msg(5, 2, turn=2), visible(6, turn=2), msg(7, 3, turn=2), msg(8, 4, turn=2), msg(9, 5, turn=2)]:
            self.w.ingest(m)

    def receipt(self, counter=2, nonce=100, last=9):
        return dict(event='savedataUpdated', nonce=nonce, run=1, eventCounter=last, ack=last, depth=0, state=0, drops=0, counter=counter)

    def result_id(self):
        return next(r['memoryID'] for r in self.w.for_actor(RICK).records()['records'] if r['claim']['type'] == 'TRAINER_BATTLE_RESULT')

    def deliver(self, **overrides):
        c = self.w.campaign()
        args = dict(delivery_id='test-result', sender=RICK, recipient=JANICE, source_memory_id=self.result_id(), campaign=c['id'], branch=c['active_branch'], cursor=c['cursor'])
        args.update(overrides)
        return self.w.deliver_fixture(**args)

    def test_identity_registry_reuse(self):
        self.assertEqual(self.w.get_actor(RICK)['primarySourceID'], 102)
        self.assertEqual(actor_id(self.w.registry['mapping']['507']), JANICE)
        self.assertEqual(len(self.w.registry_actor_ids()), 580)

    def test_canonical_only_writer_cannot_bypass_memory(self):
        with self.assertRaisesRegex(WorldError, 'requires MemoryStore'):
            WorldStore(self.path, BUILD, TAG)

    def test_already_open_legacy_writer_is_revoked_after_migration(self):
        other = Path(self.tmp.name) / 'old.sqlite3'
        with WorldStore(other, BUILD, TAG) as old:
            old.import_save(self.s1)
            with MemoryStore(other, BUILD, TAG):
                with self.assertRaisesRegex(WorldError, 'requires MemoryStore'):
                    old.authorize_launch(123, self.s1)

    def test_firewall(self):
        self.battle()
        r = self.w.for_actor(RICK).context()
        j = self.w.for_actor(JANICE).context()
        self.assertEqual(len(r['directObservations']), 4)
        self.assertEqual(j['directObservations'] + j['deliveries'], [])
        did = self.deliver()
        j = self.w.for_actor(JANICE).context()
        self.assertEqual(j['directObservations'], [])
        self.assertEqual(len(j['deliveries']), 1)
        self.assertEqual(j['deliveries'][0]['claim']['nativeOutcome'], 1)
        self.assertEqual(j['deliveries'][0]['claim']['type'], 'TRAINER_BATTLE_RESULT')
        chain = self.w.for_actor(JANICE).provenance(did)
        self.assertEqual([x['mode'] for x in chain], ['delivered', 'direct'])
        self.assertEqual(chain[1]['actorID'], RICK)
        with self.assertRaisesRegex(WorldError, 'not authorized'):
            self.w.for_actor(JANICE).provenance(self.result_id())

    def test_repeated_reveal_compaction(self):
        self.battle()
        context = self.w.for_actor(RICK).context()
        move = next(r for r in context['directObservations'] if r['claim']['type'] == 'MOVE_REVEALED')
        self.assertEqual(move['occurrencesInWindow'], 2)
        self.assertEqual(len(move['evidenceIDs']), 2)
        self.assertEqual(len(self.w.for_actor(RICK).records()['records']), 6)

    def test_minimization(self):
        self.battle()
        value = dump(self.w.for_actor(RICK).context())
        for private in ['ownActive', 'knownMoveIDs', 'movePP', 'maxHP', 'publicHPBar', 'previouslyUndefeated', 'battleFlags', 'frameCounter', 'statusMask', 'personality', 'belief', 'confidence']:
            self.assertNotIn(private, value)
        self.assertEqual({r['claim'].get('speciesID') for r in self.w.for_actor(RICK).context()['directObservations']} - {None}, {1})
        self.assertEqual({r['claim'].get('moveID') for r in self.w.for_actor(RICK).context()['directObservations']} - {None}, {33})

    def test_announced_player_move_only(self):
        self.w.ingest(msg(1)); self.w.ingest(msg(2, 2))
        m = msg(3, 3)
        data = bytearray(m.payload); data[24] = 0
        self.w.ingest(Message(m.kind, m.nonce, m.generation, m.sequence, m.tag, m.typ, bytes(data)))
        move = next(r for r in self.w.for_actor(RICK).context()['directObservations'] if r['claim']['type'] == 'MOVE_REVEALED')
        self.assertEqual(move['claim']['moveID'], 33)

    def test_provenance_correlated(self):
        self.battle()
        for r in self.w.for_actor(RICK).records()['records']:
            table = 'events' if r['source']['kind'] == 'event' else 'observations'
            self.assertIsNotNone(self.w._one('SELECT id FROM ' + table + ' WHERE id=?', (r['source']['id'],)))
            self.assertIn(r['source']['battleID'], self.w.state()['battles'])
            self.assertIn(r['source']['turnID'], (0, 1, 2))

    def test_duplicate_transport_and_delivery(self):
        self.battle(); before = self.w.for_actor(RICK).context()
        self.w.ingest(visible(3)); self.assertEqual(before, self.w.for_actor(RICK).context())
        did = self.deliver(); j = self.w.for_actor(JANICE).context()
        self.assertEqual(self.deliver(), did)
        self.assertEqual(j, self.w.for_actor(JANICE).context())

    def test_conflicting_delivery(self):
        self.battle(); self.deliver()
        with self.assertRaisesRegex(WorldError, 'conflicting'):
            self.deliver(recipient=RICK)

    def test_invalid_recipient_sender_and_source(self):
        self.battle()
        for args in [dict(recipient='unknown'), dict(sender=JANICE), dict(source_memory_id='invented')]:
            with self.assertRaises(WorldError):
                self.deliver(**args)

    def test_stale_branch_campaign_future_cursor(self):
        self.battle()
        for args in [dict(branch='other'), dict(campaign='other'), dict(cursor=999), dict(cursor=0)]:
            with self.assertRaisesRegex(WorldError, 'stale'):
                self.deliver(**args)

    def test_delivery_bounds(self):
        self.battle()
        for identity in ['', 'x' * 65, 'bad\nkey']:
            with self.assertRaises(WorldError):
                self.deliver(delivery_id=identity)

    def test_restart_and_replay(self):
        self.battle(); self.deliver()
        before = self.w.for_actor(RICK).context(); j = self.w.for_actor(JANICE).context()
        sha = self.w.verify_memory_replay()
        self.w.close(); self.w = MemoryStore(self.path, BUILD, TAG)
        self.assertEqual(before, self.w.for_actor(RICK).context()); self.assertEqual(j, self.w.for_actor(JANICE).context())
        self.assertEqual(sha, self.w.verify_memory_replay())

    def test_restore_and_divergent_branch(self):
        self.battle(); self.deliver(); a = self.w.get_active_branch()
        old = self.w.for_actor(RICK); oldj = self.w.for_actor(JANICE)
        self.w.authorize_launch(200, self.s1)
        self.assertEqual(self.w.for_actor(RICK).context()['directObservations'], [])
        self.assertEqual(self.w.for_actor(JANICE).context()['deliveries'], [])
        for view in [old, oldj]:
            with self.assertRaisesRegex(WorldError, 'revoked'):
                view.context()
        self.w.ingest(msg(1, nonce=200, trainer=0))
        self.assertNotEqual(a, self.w.get_active_branch())
        self.assertEqual(self.w.for_actor(RICK).context()['directObservations'], [])
        self.assertEqual(self.w.for_actor(JANICE).context()['deliveries'], [])
        self.assertEqual(self.w._one('SELECT COUNT(*) n FROM memory_evidence WHERE branch=?', (a,))['n'], 7)
        self.w.verify_memory_replay()

    def test_same_world_cursor_delivery_rewinds(self):
        self.battle()
        s2 = fingerprint(flash(2, 2), SIZES)
        self.w.finish_save(self.w.begin_save(100, self.s1), s2, self.receipt())
        self.deliver()
        view = self.w.for_actor(JANICE)
        self.w.authorize_launch(200, s2)
        self.assertEqual(self.w.for_actor(JANICE).context()['deliveries'], [])
        self.assertEqual(len(self.w.for_actor(RICK).context()['directObservations']), 4)
        self.assertEqual(self.w.campaign()['pending_fork'], 1)
        with self.assertRaises(WorldError): view.context()
        with self.assertRaisesRegex(WorldError, 'settled'): self.deliver()
        self.w.ingest(msg(1, nonce=200, trainer=0))
        self.assertEqual(self.w.for_actor(JANICE).context()['deliveries'], [])
        self.assertEqual(len(self.w.for_actor(RICK).context()['directObservations']), 4)
        with self.assertRaisesRegex(WorldError, 'conflicting'):
            self.deliver()

    def test_as_of_cursor(self):
        self.battle(); self.deliver()
        view = self.w.for_actor(RICK)
        early = view.context(as_of_cursor=1)
        self.assertEqual([r['claim']['type'] for r in early['directObservations']], ['BATTLE_PARTICIPATION'])
        self.assertEqual(self.w.for_actor(JANICE).context(as_of_cursor=1)['deliveries'], [])
        for cursor in [-1, 99, True]:
            with self.assertRaises(WorldError): view.context(as_of_cursor=cursor)

    def test_save_barrier_blocks_deliveries(self):
        self.battle(); self.w.begin_save(100, self.s1)
        with self.assertRaisesRegex(WorldError, 'barrier'): self.deliver()

    def test_checkpoint_rollback(self):
        self.battle(); s2 = fingerprint(flash(2, 2), SIZES)
        with self.assertRaisesRegex(WorldError, 'injected'):
            self.w.finish_save(self.w.begin_save(100, self.s1), s2, self.receipt(), fail=True)
        self.assertEqual(self.w._one('SELECT COUNT(*) n FROM memory_checkpoints')['n'], 1)

    def test_memory_failure_rolls_back_canonical_ingestion(self):
        original = self.w._derive
        def fail():
            original()
            raise WorldError('injected memory failure')
        self.w._derive = fail
        with self.assertRaisesRegex(WorldError, 'injected memory'):
            self.w.ingest(msg(1))
        self.w._derive = original
        self.assertEqual(self.w.state()['cursor'], 0)
        self.assertEqual(self.w._maximum(), 0)
        self.assertEqual(self.w._one('SELECT COUNT(*) n FROM deliveries')['n'], 0)

    def test_unknown_memory_version(self):
        self.w.db.execute('UPDATE memory_version SET reducer=2')
        with self.assertRaisesRegex(WorldError, 'unsupported memory'): MemoryStore(self.path, BUILD, TAG)

    def test_immutable_evidence_and_cutoffs(self):
        self.battle()
        for table in ['memory_evidence', 'memory_actors', 'memory_checkpoints', 'memory_sources', 'memory_branches']:
            with self.assertRaises(sqlite3.IntegrityError): self.w.db.execute('DELETE FROM ' + table)

    def test_legacy_migration(self):
        self.w.close(); self.path.unlink()
        with WorldStore(self.path, BUILD, TAG) as old:
            old.import_save(self.s1); old.authorize_launch(100, self.s1)
            for m in [msg(1), msg(2, 2), visible(3), msg(4, 3), msg(5, 4), msg(6, 5)]: old.ingest(m)
            facts = old.state(); canonical = old.verify_replay()
        self.w = MemoryStore(self.path, BUILD, TAG)
        self.assertEqual(self.w.state(), facts); self.assertEqual(self.w.verify_replay(), canonical)
        self.assertEqual(len(self.w.for_actor(RICK).context()['directObservations']), 4)
        self.w.restore(self.s1)
        self.assertEqual(self.w.for_actor(RICK).context()['directObservations'], [])
        self.w.verify_memory_replay()

    def test_grant_pinned_before_future_ingestion(self):
        view = self.w.for_actor(RICK)
        self.battle()
        self.assertEqual(view.context()['directObservations'], [])

    def test_suspension_revokes_context(self):
        view = self.w.for_actor(RICK); self.w.suspend('gap')
        with self.assertRaises(WorldError): view.context()

    def test_bounds_and_no_actor_selection(self):
        view = self.w.for_actor(RICK)
        for args in [dict(limit=257), dict(after=-1)]:
            with self.assertRaises(WorldError): view.records(**args)
        with self.assertRaises(TypeError): view.context(actor=JANICE)

    def test_wild_battle_grants_no_trainer(self):
        self.w.ingest(msg(1, trainer=0)); self.w.ingest(msg(2, 2, trainer=0))
        self.w.ingest(msg(3, 6, trainer=0))
        self.assertEqual(self.w._maximum(), 0)

    def test_unannounced_action_not_a_claim(self):
        self.w.ingest(msg(1)); self.w.ingest(msg(2, 2))
        m = msg(3, 3); data = bytearray(m.payload)
        struct.pack_into('<BBHH', data, 24, 0, 0, 0, 1)
        self.w.ingest(Message(m.kind, m.nonce, m.generation, m.sequence, m.tag, m.typ, bytes(data)))
        self.assertEqual(len(self.w.for_actor(RICK).context()['directObservations']), 1)

    def test_delivery_chain_does_not_copy_other_claims(self):
        self.battle(); self.deliver()
        c = self.w.campaign(); other = actor_id('fr:trainer:0103')
        parent = self.w.for_actor(JANICE).records()['records'][0]['memoryID']
        did = self.w.deliver_fixture(delivery_id='chain', sender=JANICE, recipient=other, source_memory_id=parent, campaign=c['id'], branch=c['active_branch'], cursor=c['cursor'])
        view = self.w.for_actor(other)
        self.assertEqual(len(view.context()['deliveries']), 1)
        self.assertEqual([r['actorID'] for r in view.provenance(did)], [other, JANICE, RICK])
        self.assertEqual({r['claim']['type'] for r in view.provenance(did)}, {'TRAINER_BATTLE_RESULT'})

    def test_malformed_provenance_detected_by_replay(self):
        self.battle(); self.deliver()
        self.w.db.execute('DROP TRIGGER immutable_memory_evidence_UPDATE')
        self.w.db.execute("UPDATE memory_evidence SET source_id='invented' WHERE mode='direct'")
        with self.assertRaisesRegex(WorldError, 'replay mismatch'): self.w.verify_memory_replay()

    def test_malformed_delivered_claim_detected(self):
        self.battle(); self.deliver()
        self.w.db.execute('DROP TRIGGER immutable_memory_evidence_UPDATE')
        self.w.db.execute("UPDATE memory_evidence SET claim='{}' WHERE mode='delivered'")
        with self.assertRaisesRegex(WorldError, 'provenance'): self.w.verify_memory_replay()

    def test_provenance_depth_is_bounded_at_write(self):
        self.battle(); c = self.w.campaign(); source = self.result_id(); sender = RICK
        for i in range(15):
            recipient = JANICE if sender == RICK else RICK
            source = self.w.deliver_fixture(delivery_id='depth-' + str(i), sender=sender, recipient=recipient, source_memory_id=source, campaign=c['id'], branch=c['active_branch'], cursor=c['cursor'])
            sender = recipient
        self.assertEqual(len(self.w.for_actor(sender).provenance(source)), 16)
        with self.assertRaisesRegex(WorldError, 'depth limit'):
            self.w.deliver_fixture(delivery_id='too-deep', sender=sender, recipient=RICK, source_memory_id=source, campaign=c['id'], branch=c['active_branch'], cursor=c['cursor'])

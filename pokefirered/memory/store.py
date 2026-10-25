"""Actor-owned evidence v1 over the unchanged canonical WORLD schema/reducer.

MemoryStore is the trusted host writer. Give consumers only an ActorView issued
by the host; actor selection and SQL never form model-visible tools.
"""
import hashlib
import json
import time
from pathlib import Path
from world.store import WorldStore, WorldError, dump

VERSION = 1
REDUCER = 1


def digest(value):
    return hashlib.sha256(dump(value).encode()).hexdigest()


def actor_id(world_id):
    return 'trainer:' + world_id


class MemoryStore(WorldStore):
    _supports_memory = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._one("SELECT name FROM sqlite_master WHERE name='social_version'") and not getattr(self, '_supports_social', False):
            self.close()
            raise WorldError('social-enabled database requires SocialStore writer')
        self._restoring = None
        try:
            exists = self._one("SELECT name FROM sqlite_master WHERE name='memory_version'")
            if exists:
                versions = [tuple(r) for r in self.db.execute('SELECT * FROM memory_version')]
                if versions != [(VERSION, REDUCER)]:
                    raise WorldError('unsupported memory schema/reducer')
            else:
                self.db.executescript('BEGIN IMMEDIATE;' + (Path(__file__).parent / 'migrations/001.sql').read_text())
                try:
                    self.db.executemany('INSERT INTO memory_actors VALUES (?,?)',
                                        [(actor_id(w), w) for w in sorted(self.registry['trainers'])])
                    for table in ('memory_evidence', 'memory_sources', 'memory_actors', 'memory_branches', 'memory_checkpoints'):
                        for op in ('UPDATE', 'DELETE'):
                            self.db.execute(f"CREATE TRIGGER immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only memory'); END")
                    self._derive()
                    # Legacy checkpoints gain only source evidence available when
                    # they were published. No delivery/history is invented.
                    for p in self.db.execute('SELECT * FROM checkpoints').fetchall():
                        cutoff = self._one('SELECT COALESCE(MAX(seq),0) n FROM memory_evidence WHERE created_at<=?', (p['created_at'],))['n']
                        self.db.execute('INSERT INTO memory_checkpoints VALUES (?,?)', (p['id'], cutoff))
                    for b in self.db.execute('SELECT * FROM branches').fetchall():
                        first = self._one('SELECT MIN(ingested_at) t FROM events WHERE branch=?', (b['id'],))['t']
                        cutoff = self._one('SELECT COALESCE(MAX(seq),0) n FROM memory_evidence WHERE created_at<?', (first or 0,))['n']
                        self.db.execute('INSERT INTO memory_branches VALUES (?,?)', (b['id'], cutoff))
                    c = self._one('SELECT * FROM campaigns')
                    if c:
                        cutoff = self._maximum()
                        if c['pending_fork']:
                            p = self._one('SELECT m.cutoff FROM checkpoints p JOIN memory_checkpoints m ON m.checkpoint=p.id WHERE p.branch=? AND p.cursor=? ORDER BY p.created_at DESC LIMIT 1', (c['active_branch'], c['cursor']))
                            cutoff = p['cutoff'] if p else 0
                        self.db.execute('INSERT INTO memory_view VALUES (?,?,?)', (c['id'], c['active_branch'], cutoff))
                    self.db.execute('COMMIT')
                except Exception:
                    self.db.execute('ROLLBACK')
                    raise
            expected = [(actor_id(w), w) for w in sorted(self.registry['trainers'])]
            actual = [tuple(r) for r in self.db.execute('SELECT * FROM memory_actors ORDER BY id')]
            if actual != expected:
                raise WorldError('actor registry integrity')
        except Exception:
            self.close()
            raise

    def _maximum(self):
        return self._one('SELECT COALESCE(MAX(seq),0) n FROM memory_evidence')['n']

    def _tx(self, fn):
        if self._one("SELECT name FROM sqlite_master WHERE name='social_version'") and not getattr(self, '_supports_social', False):
            raise WorldError('social-enabled database requires SocialStore writer')
        def action():
            before = self._one('SELECT * FROM memory_view')
            result = fn()
            c = self._one('SELECT * FROM campaigns')
            if not c:
                return result
            if not self._one('SELECT * FROM memory_branches WHERE branch=?', (c['active_branch'],)):
                self.db.execute('INSERT INTO memory_branches VALUES (?,?)', (c['active_branch'], before['cutoff'] if before else 0))
            previous_max = self._maximum()
            self._derive()
            cutoff = before['cutoff'] if before else self._maximum()
            if self._restoring:
                cutoff = self._one('SELECT cutoff FROM memory_checkpoints WHERE checkpoint=?', (self._restoring,))['cutoff']
                future = self._one('SELECT 1 FROM memory_evidence WHERE branch=? AND seq>? LIMIT 1', (c['active_branch'], cutoff))
                if future:
                    self.db.execute('UPDATE campaigns SET pending_fork=1 WHERE id=?', (c['id'],))
            elif self._maximum() > previous_max or (before and c['active_branch'] != before['branch']):
                cutoff = self._maximum()
            # Explicit delivery inserts its evidence in fn, before _derive.
            if getattr(self, '_delivering', False):
                cutoff = self._maximum()
            self.db.execute('INSERT OR REPLACE INTO memory_view VALUES (?,?,?)', (c['id'], c['active_branch'], cutoff))
            self._after_memory_transaction()
            return result
        return super()._tx(action)

    def _after_memory_transaction(self):
        """Protected transactional extension point; runs before COMMIT/ACK."""

    def _deliver_reference(self, *, identity, sender, recipient, source_memory_id,
                           source_kind, source_id, channel):
        """Shared trusted delivery primitive, inside an already-open transaction.

        Subclasses must validate publication/exposure permissions before calling.
        This method is never a consumer/model-facing tool.
        """
        if not self.db.in_transaction:
            raise WorldError('delivery requires atomic domain transaction')
        c = self.campaign()
        if c['status'] not in ('paired', 'imported') or c['pending_fork'] or self.pending_save():
            raise WorldError('delivery requires settled branch and no save barrier')
        rocket = (source_kind, channel) == ('rocket_intel', 'ROCKET_INTEL') and getattr(self, '_supports_virality', False)
        if not rocket and (source_kind, channel) not in [('fixture_delivery', 'development_fixture'), ('post_exposure', 'pokebook')]:
            raise WorldError('unsupported delivery source/channel')
        if source_kind == 'post_exposure' and not getattr(self, '_supports_social', False):
            raise WorldError('publication permission required')
        self.get_actor(recipient)
        view = self.for_actor(sender)
        source = view._find(source_memory_id)
        if rocket:
            self._authorize_rocket_reference(sender, recipient, source)
        old = self._one('SELECT * FROM memory_evidence WHERE id=?', (identity,))
        if old:
            if (old['actor'],old['sender'],old['parent'],old['branch'],old['cursor'],old['source_kind'],old['source_id'],old['channel']) != (recipient,sender,source_memory_id,c['active_branch'],c['cursor'],source_kind,source_id,channel):
                raise WorldError('conflicting duplicate delivery')
            return identity
        if len(view.provenance(source_memory_id)) >= 16:
            raise WorldError('provenance depth limit')
        self._insert(identity=identity, campaign=c['id'], branch=c['active_branch'], cursor=c['cursor'], actor=recipient, claim=json.loads(source['claim']), source_kind=source_kind, source_id=source_id, battle=source['battle'], turn=source['turn'], created_at=time.time(), mode='delivered', sender=sender, parent=source['id'], channel=channel)
        return identity

    def restore(self, save):
        p = self.get_save_checkpoint(save.fingerprint)
        self._restoring = p['id'] if p else None
        try:
            return super().restore(save)
        finally:
            self._restoring = None

    def _checkpoint(self, c, save, kind):
        self._derive()
        cid = super()._checkpoint(c, save, kind)
        view = self._one('SELECT * FROM memory_view WHERE campaign=?', (c['id'],))
        cutoff = view['cutoff'] if view else self._maximum()
        old = self._one('SELECT cutoff FROM memory_checkpoints WHERE checkpoint=?', (cid,))
        if old and old['cutoff'] != cutoff:
            raise WorldError('fingerprint already paired to different memory history')
        if not old:
            self.db.execute('INSERT INTO memory_checkpoints VALUES (?,?)', (cid, cutoff))
        return cid

    def get_actor(self, actor):
        r = self._one('SELECT * FROM memory_actors WHERE id=?', (actor,))
        if not r:
            raise WorldError('unknown actor')
        identity = self.registry['trainers'][r['world_trainer']]
        return {'actorID': actor, 'worldTrainerID': r['world_trainer'],
                'name': identity['sourceRecords'][0]['name'], 'primarySourceID': identity['primarySourceID']}

    def _insert(self, *, identity, campaign, branch, cursor, actor, claim, source_kind,
                source_id, battle, turn, created_at, mode='direct', sender=None,
                parent=None, channel=None):
        self.get_actor(actor)
        self.db.execute('INSERT OR IGNORE INTO memory_evidence(id,campaign,branch,cursor,actor,mode,claim,source_kind,source_id,battle,turn,sender,parent,channel,status,schema,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,\'recorded\',1,?)',
                        (identity, campaign, branch, cursor, actor, mode, dump(claim), source_kind, source_id, battle, turn, sender, parent, channel, created_at))

    def _derive(self):
        sources = self.db.execute("SELECT 'event' kind,id,branch,cursor,origin,record,ingested_at FROM events WHERE id NOT IN (SELECT id FROM memory_sources WHERE kind='event') UNION ALL SELECT 'observation',id,branch,cursor,origin,record,ingested_at FROM observations WHERE id NOT IN (SELECT id FROM memory_sources WHERE kind='observation') ORDER BY ingested_at,id").fetchall()
        for s in sources:
            r = json.loads(s['record'])
            # Match the persisted launch/run/native battle, not a globally reused
            # native battle number or merely the trainer's display name.
            prefix = s['origin'].rsplit(':', 1)[0]
            starts = self.db.execute('SELECT * FROM events WHERE origin LIKE ? AND branch=?', (prefix + ':%', s['branch']))
            start = next((e for e in starts if (x := json.loads(e['record']))['eventType'] == 'BATTLE_STARTED' and x['battleID'] == r['battleID']), None)
            if not start:
                raise WorldError('memory source lacks correlated battle provenance')
            p0 = json.loads(start['record'])['payload']
            trainer = p0['trainerID']
            claims = []
            if trainer:
                world = self.registry['mapping'][str(trainer)]
                if p0['battleFlags'] & ~(4 | 8):
                    raise WorldError('unsupported memory participant mode')
                base = {'battleID': start['battle'], 'trainerID': world}
                p = r['payload']
                if r['eventType'] == 'BATTLE_STARTED':
                    claims = [{'type': 'BATTLE_PARTICIPATION', **base}]
                elif r['eventType'] == 'BATTLE_ENDED':
                    claims = [{'type': 'TRAINER_BATTLE_RESULT', **base, 'nativeOutcome': p['outcome']}]
                elif r['eventType'] == 'BATTLE_OBSERVATION':
                    if p['trainerID'] != trainer or p['observerSide'] != 1:
                        raise WorldError('memory observer correlation')
                    visible = p['opponentActive']
                    species = visible['revealedSpeciesID']
                    claims = [{'type': 'POKEMON_SEEN', **base, 'speciesID': species}]
                    claims += [{'type': 'MOVE_REVEALED', **base, 'speciesID': species, 'moveID': move} for move in sorted(set(visible['revealedMoveIDs']))]
                elif r['eventType'] == 'BATTLE_ACTION_RESOLVED' and p['actorSide'] == 0 and p['resolutionKind'] == 'announced_move':
                    # BRIDGE-02's native used-move text hook explicitly classifies
                    # these two fields as visible; no private slot/action category.
                    claims = [{'type': 'MOVE_REVEALED', **base, 'speciesID': p['visibleActorSpeciesID'], 'moveID': p['announcedMoveID']}]
                campaign = self._one('SELECT campaign FROM branches WHERE id=?', (s['branch'],))['campaign']
                for claim in claims:
                    self._insert(identity=digest([VERSION, actor_id(world), s['kind'], s['id'], claim]), campaign=campaign, branch=s['branch'], cursor=s['cursor'], actor=actor_id(world), claim=claim, source_kind=s['kind'], source_id=s['id'], battle=start['battle'], turn=r['turnID'], created_at=s['ingested_at'])
            self.db.execute('INSERT INTO memory_sources VALUES (?,?)', (s['kind'], s['id']))

    def for_actor(self, actor):
        """Trusted host grant issuance; never expose this factory to a model."""
        self.get_actor(actor)
        c = self.campaign()
        v = self._one('SELECT * FROM memory_view WHERE campaign=?', (c['id'],))
        return ActorView(self, actor, c['id'], c['active_branch'], c['cursor'], v['cutoff'])

    def _scope(self, branch, cursor, cutoff):
        scope = []
        while branch:
            scope.append((branch, cursor, cutoff))
            b = self._one('SELECT * FROM branches WHERE id=?', (branch,))
            m = self._one('SELECT * FROM memory_branches WHERE branch=?', (branch,))
            cursor = min(cursor, b['fork_cursor'])
            cutoff = min(cutoff, m['parent_cutoff'])
            branch = b['parent']
        return scope

    def _rows(self, actor, campaign, branch, cursor, cutoff, after=0, limit=257):
        scopes = self._scope(branch, cursor, cutoff)
        clause = ' OR '.join('(branch=? AND cursor<=? AND seq<=?)' for _ in scopes)
        args = [actor, campaign, after] + [v for s in scopes for v in s] + [limit]
        return self.db.execute(f'SELECT * FROM memory_evidence WHERE actor=? AND campaign=? AND seq>? AND ({clause}) ORDER BY seq LIMIT ?', args).fetchall()

    def deliver_fixture(self, *, delivery_id, sender, recipient, source_memory_id, campaign, branch, cursor):
        """Development-only one-claim targeted delivery. No broadcasts or text."""
        def action():
            c = self.campaign()
            if c['status'] not in ('paired', 'imported') or (campaign, branch, cursor) != (c['id'], c['active_branch'], c['cursor']):
                raise WorldError('stale campaign/branch or future/past delivery cursor')
            if c['pending_fork'] or self.pending_save():
                raise WorldError('delivery requires settled branch and no save barrier')
            if not isinstance(delivery_id, str) or not 1 <= len(delivery_id) <= 64 or not all(x.isalnum() or x in '-_:' for x in delivery_id):
                raise WorldError('delivery identity bounds')
            identity = digest(['fixture-delivery', campaign, delivery_id])
            return self._deliver_reference(identity=identity,sender=sender,recipient=recipient,source_memory_id=source_memory_id,source_kind='fixture_delivery',source_id=delivery_id,channel='development_fixture')
        self._delivering = True
        try:
            return self._tx(action)
        finally:
            self._delivering = False

    def verify_memory_replay(self):
        """Verify stored direct evidence against a fresh deterministic derivation.

        Delivered claims have no canonical effect; validate exact parent claim,
        ownership and same-campaign branch visibility at receipt time.
        """
        import sqlite3
        clone = sqlite3.connect(':memory:', isolation_level=None)
        self.db.backup(clone)
        clone.row_factory = self.db.row_factory
        original = self.db
        try:
            self.db = clone
            expected = [dict(r) for r in clone.execute("SELECT * FROM memory_evidence WHERE mode='direct' ORDER BY id")]
            for table in ('memory_evidence', 'memory_sources'):
                clone.execute(f'DROP TRIGGER immutable_{table}_DELETE')
            clone.execute("DELETE FROM memory_evidence WHERE mode='direct'")
            clone.execute('DELETE FROM memory_sources')
            self._derive()
            actual = [dict(r) for r in clone.execute("SELECT * FROM memory_evidence WHERE mode='direct' ORDER BY id")]
            for rows in (expected, actual):
                for r in rows:
                    r.pop('seq')
            if actual != expected:
                raise WorldError('memory deterministic replay mismatch')
        finally:
            self.db = original
            clone.close()
        for d in self.db.execute("SELECT * FROM memory_evidence WHERE mode='delivered'"):
            p = self._one('SELECT * FROM memory_evidence WHERE id=?', (d['parent'],))
            if not p or p['claim'] != d['claim'] or p['actor'] != d['sender'] or p['campaign'] != d['campaign'] or p['seq'] >= d['seq']:
                raise WorldError('invalid delivery provenance')
            allowed = any(p['branch'] == b and p['cursor'] <= c and p['seq'] <= n for b, c, n in self._scope(d['branch'], d['cursor'], d['seq'] - 1))
            if not allowed:
                raise WorldError('delivery source outside branch')
        context = {actor: self.for_actor(actor).context() for actor in sorted(self.registry_actor_ids())}
        return digest(context)

    def registry_actor_ids(self):
        return [r['id'] for r in self.db.execute('SELECT id FROM memory_actors')]


class ActorView:
    """Actor-bound read capability; no actor/branch parameters on retrieval.

    This is an application boundary, not isolation from arbitrary Python code.
    Future adapters register only context/records/provenance callables.
    """
    def __init__(self, store, actor, campaign, branch, cursor, cutoff):
        self.__store = store
        self.__actor, self.__campaign, self.__branch = actor, campaign, branch
        self.__cursor, self.__cutoff = cursor, cutoff

    def _validate(self, cursor=None):
        c = self.__store.campaign()
        v = self.__store._one('SELECT * FROM memory_view WHERE campaign=?', (c['id'],))
        if c['status'] not in ('paired', 'imported') or (c['id'], c['active_branch']) != (self.__campaign, self.__branch) or c['cursor'] < self.__cursor or v['cutoff'] < self.__cutoff:
            raise WorldError('revoked actor grant after restore/branch/suspension')
        cursor = self.__cursor if cursor is None else cursor
        if type(cursor) != int or not 0 <= cursor <= self.__cursor:
            raise WorldError('actor cursor bounds')
        return cursor

    def _find(self, identity):
        self._validate()
        row = self.__store._one('SELECT * FROM memory_evidence WHERE id=? AND actor=? AND campaign=?', (identity, self.__actor, self.__campaign))
        if row and any(row['branch'] == b and row['cursor'] <= c and row['seq'] <= n for b, c, n in self.__store._scope(self.__branch, self.__cursor, self.__cutoff)):
            return row
        raise WorldError('memory not authorized for actor')

    @staticmethod
    def _public(row):
        source = {'kind': row['source_kind'], 'id': row['source_id'], 'battleID': row['battle'], 'turnID': row['turn'], 'sender': row['sender'], 'parentMemoryID': row['parent'], 'channel': row['channel']}
        if row['source_kind'] == 'post_exposure':
            source = {'kind': 'published_post', 'postID': row['source_id'], 'sender': row['sender'], 'channel': 'pokebook', 'attribution': 'reported'}
        return {'memoryID': row['id'], 'memoryCursor': row['seq'], 'actorID': row['actor'], 'mode': row['mode'], 'claim': json.loads(row['claim']), 'campaignID': row['campaign'], 'branchID': row['branch'], 'worldCursor': row['cursor'], 'schemaVersion': row['schema'], 'status': row['status'], 'source': source}

    def records(self, *, as_of_cursor=None, after=0, limit=128):
        cursor = self._validate(as_of_cursor)
        if type(limit) != int or not 1 <= limit <= 256 or type(after) != int or after < 0:
            raise WorldError('retrieval bounds')
        rows = self.__store._rows(self.__actor, self.__campaign, self.__branch, cursor, self.__cutoff, after, limit + 1)
        return {'records': [self._public(r) for r in rows[:limit]], 'hasMore': len(rows) > limit}

    def provenance(self, memory_id):
        row = self._find(memory_id)
        chain = []
        claim = row['claim']
        for _ in range(16):
            if row['claim'] != claim:
                raise WorldError('provenance claim mismatch')
            chain.append(self._public(row))
            if row['source_kind'] == 'post_exposure':
                return chain # Internal author evidence lineage is audit-only.
            if not row['parent']:
                return chain
            row = self.__store._one('SELECT * FROM memory_evidence WHERE id=?', (row['parent'],))
            if row is None:
                raise WorldError('missing provenance')
        raise WorldError('provenance depth limit')

    def context(self, *, as_of_cursor=None):
        page = self.records(as_of_cursor=as_of_cursor, limit=256)
        groups = {}
        for r in page['records']:
            post = r['source'].get('postID')
            key = dump([r['mode'], r['claim'], r['source']['sender'], post])
            group = groups.setdefault(key, {'mode': r['mode'], 'claim': r['claim'], 'sender': r['source']['sender'], 'occurrencesInWindow': 0, 'evidenceIDs': []})
            if post:
                group['attribution'] = {'kind': 'reported_post', 'author': r['source']['sender'], 'postID': post, 'channel': 'pokebook'}
            group['occurrencesInWindow'] += 1
            if len(group['evidenceIDs']) < 8:
                group['evidenceIDs'].append(r['memoryID'])
        return {'schemaVersion': VERSION, 'actor': self.__store.get_actor(self.__actor), 'campaignID': self.__campaign, 'branchID': self.__branch, 'worldCursor': self._validate(as_of_cursor), 'memoryCutoff': self.__cutoff, 'directObservations': [v for k, v in sorted(groups.items()) if v['mode'] == 'direct'], 'deliveries': [v for k, v in sorted(groups.items()) if v['mode'] == 'delivered'], 'truncated': page['hasMore']}

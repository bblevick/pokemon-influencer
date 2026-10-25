import unittest,struct
import test_hermes01 as domain
DOUG=domain.DOUG
from test_memory01 import RICK,JANICE
from pokebook.viewer import Viewer,pages,SNAPSHOT_IDLE_SECONDS
from pokebook.wire import respond,REQUEST,HEADER
from bridge.ui import INV
from world.store import WorldError

class ViewerTests(unittest.TestCase):
    setUp=domain.PuppeteerTests.setUp
    tearDown=domain.PuppeteerTests.tearDown
    battle=domain.PuppeteerTests.battle
    job=domain.PuppeteerTests.job
    process=domain.PuppeteerTests.process
    save=domain.PuppeteerTests.save
    # Reuse the actual domain setup, not its test suite.
    def hashes(self):return [f() for f in (self.w.verify_replay,self.w.verify_memory_replay,self.w.verify_social_replay,self.w.verify_puppeteer_replay)]
    def test_empty_and_pending(self):
        v=Viewer(self.w);self.assertEqual(v.open(1)['posts'],0);self.battle();self.assertEqual(v.open(2)['posts'],0);self.process();self.assertEqual(v.open(3)['posts'],1)
    def test_public_safe_and_direction_read_only(self):
        self.battle();self.process();v=Viewer(self.w);before=self.hashes();s=v.open(1)
        self.assertEqual((s['posts'],s['followers']),(1,1))
        self.assertEqual(v.query(1,s['snapshot'],4)['rows'][0]['label'],'RICK')
        p=v.query(1,s['snapshot'],3,post=1)
        self.assertEqual(set(p),{'pages','text','author','postID'})
        text=''.join(INV[c] for c in p['text']);self.assertIn('I lost',text);self.assertNotIn('TACKLE',text)
        v.close(1);self.assertEqual(before,self.hashes());self.assertFalse(self.w.trainer_packet(JANICE)['reportedClaims']);self.assertFalse(self.w.trainer_packet(DOUG)['reportedClaims'])
    def test_stable_arrival_refresh(self):
        self.battle();self.process();v=Viewer(self.w);s=v.open(1);p=v.query(1,s['snapshot'],3,post=1)['postID']
        self.battle(first=7,bid=2);self.process();self.assertEqual(p,v.query(1,s['snapshot'],3,post=1)['postID']);self.assertEqual(len(v.query(1,s['snapshot'],2)['rows']),1);self.assertEqual(v.open(2)['posts'],2)
    def test_invalid_handles_ops_page_cancel_expiry(self):
        now=[0];v=Viewer(self.w,lambda:now[0]);s=v.open(1)
        for args in [(2,s['snapshot'],2),(1,999,2),(1,s['snapshot'],6),(1,s['snapshot'],2,1),(1,s['snapshot'],3,0,1)]:
            with self.assertRaises(WorldError):v.query(*args)
        now[0]=SNAPSHOT_IDLE_SECONDS
        with self.assertRaises(WorldError):v.query(1,s['snapshot'],2)
        v.open(3);v.close(3)
        with self.assertRaises(WorldError):v.query(3,2,2)
    def test_restore_revokes_and_late_returns(self):
        early=self.save(2,0);self.battle();self.process();late=self.save(3,6);v=Viewer(self.w);s=v.open(1)
        self.w.authorize_launch(200,early)
        with self.assertRaises(WorldError):v.query(1,s['snapshot'],2)
        self.assertEqual(v.open(2)['posts'],0);self.w.authorize_launch(300,late);self.assertEqual(v.open(3)['posts'],1)
    def test_page_complete_and_controls(self):
        text='I lost to the player. '*40;chunks=pages(text)
        self.assertGreater(len(chunks),1);self.assertEqual(''.join(''.join(INV[c] for c in p if c!=254) for p in chunks),text)
        for text in ['{PLAYER}','bad\x00','a\nprivate','é','a'*4097]:
            with self.assertRaises(WorldError):pages(text)
    def test_wire_limits_error_and_schema(self):
        self.battle();self.process();v=Viewer(self.w)
        raw=respond(v,REQUEST.pack(2,1,1,1,0,0,0,0));s=HEADER.unpack_from(raw)[4]
        for op in (2,3,4):
            raw=respond(v,REQUEST.pack(2,op,2,1,s,1 if op==3 else 0,0,0));self.assertLessEqual(len(raw),96);self.assertEqual(HEADER.unpack_from(raw)[1],op)
        raw=respond(v,REQUEST.pack(2,3,3,1,s,99,0,0));self.assertEqual(HEADER.unpack_from(raw)[1],515)
        for data in [b'',REQUEST.pack(1,1,1,1,0,0,0,0),REQUEST.pack(2,1,1,1,0,0,0,1)]:
            with self.assertRaises(WorldError):respond(v,data)


    def test_private_post_not_in_counts_or_preview(self):
        self.battle();self.process()
        original=self.w.social_state
        def private():
            state=original()
            for p in state['posts'].values():p['visibility']='private';p['body']='PRIVATE CANARY'
            return state
        self.w.social_state=private
        v=Viewer(self.w);s=v.open(1);self.assertEqual(s['posts'],0);self.assertFalse(v.query(1,s['snapshot'],2)['rows'])
        with self.assertRaises(WorldError):v.query(1,s['snapshot'],3,post=1)
    def test_npc_schedule_independent_of_player_view(self):
        self.battle();result=self.process();self.w.tick(1)
        initial=self.w.trainer_packet(JANICE);self.assertFalse(initial['reportedClaims'])
        before=self.hashes();v=Viewer(self.w);s=v.open(1)
        for _ in range(6):v.query(1,s['snapshot'],2);v.query(1,s['snapshot'],3,post=1);v.query(1,s['snapshot'],4)
        self.assertEqual(before,self.hashes());self.assertEqual(initial,self.w.trainer_packet(JANICE))
        self.w.for_social_actor(JANICE).expose(result['postID']);self.assertEqual(len(self.w.trainer_packet(JANICE)['reportedClaims']),2)
        self.assertFalse(self.w.trainer_packet(DOUG)['reportedClaims']);self.assertNotIn('moveID',str(self.w.trainer_packet(JANICE)))
    def test_reopen_host_and_build_compatibility(self):
        self.battle();self.process();before=self.hashes();self.w.close()
        from puppeteer.store import PuppeteerStore
        from test_world01 import BUILD,TAG
        with self.assertRaises(WorldError):PuppeteerStore(self.path,'f'*64,TAG)
        self.w=PuppeteerStore(self.path,BUILD,TAG);self.assertEqual(Viewer(self.w).open(1)['posts'],1);self.assertEqual(before,self.hashes())
    def test_explicit_fixture_never_creates_campaign_records(self):
        from pokebook.fixtures import StoredFixtureViewer
        fixture={'kind':'layout_fixture','label':'Layout fixture','body':'Approved recap. '*20,'sourcePostID':'0'*64,'sourceBuild':'1'*64,'sourceSHA256':'2'*64}
        before=self.hashes();v=StoredFixtureViewer(self.w,fixture);s=v.open(1);all_text=[]
        pages_n=v.query(1,s['snapshot'],3,post=1)['pages']
        for page in range(pages_n):all_text.extend(c for c in v.query(1,s['snapshot'],3,page,1)['text'] if c!=254)
        self.assertEqual(''.join(INV[c] for c in all_text),fixture['body']);self.assertEqual(before,self.hashes());self.assertFalse(self.w.social_state()['posts'])

    def test_follower_direction_dedup_and_no_reciprocal(self):
        self.battle();self.process();original=self.w.social_state
        def duplicates():
            state=original();edge=next(e for e in state['follows'].values() if e['followed']==self.w.player_actor())
            state['follows']['duplicate']=dict(edge)
            state['follows']['outgoing']={'follower':self.w.player_actor(),'followed':JANICE}
            return state
        self.w.social_state=duplicates;v=Viewer(self.w);s=v.open(1)
        self.assertEqual(s['followers'],1);self.assertEqual(v.query(1,s['snapshot'],4)['rows'],[{'reference':1,'label':'RICK'}])
    def test_revoked_visibility_stale_query_rejected(self):
        self.battle();self.process();v=Viewer(self.w);s=v.open(1);original=self.w.social_state
        def revoked():
            state=original()
            for p in state['posts'].values():p['visibility']='private'
            return state
        self.w.social_state=revoked
        with self.assertRaises(WorldError):v.query(1,s['snapshot'],3,post=1)

    def test_duplicate_open_idempotent_and_query_revalidated(self):
        self.battle();self.process();v=Viewer(self.w);s=v.open(1)
        self.assertEqual(s,v.open(1));self.assertEqual(v.query(1,s['snapshot'],3,post=1)['author'],'RICK')
        refreshed=v.open(2);self.assertNotEqual(s['snapshot'],refreshed['snapshot'])
        with self.assertRaises(WorldError):v.query(1,s['snapshot'],2)

    def test_removed_follower_revokes_cached_rows_and_count(self):
        self.battle();self.process();v=Viewer(self.w);s=v.open(1)
        original=self.w.social_state
        def removed():
            state=original();state['follows']={};return state
        self.w.social_state=removed
        with self.assertRaises(WorldError):v.query(1,s['snapshot'],4)
        with self.assertRaises(WorldError):v.open(1)
        self.assertEqual(v.open(2)['followers'],0)

    def test_long_active_browse_renews_only_successful_queries(self):
        self.battle();self.process();now=[0];v=Viewer(self.w,lambda:now[0]);s=v.open(1);before=self.hashes()
        for i in range(1,8):
            now[0]=i*210
            v.query(1,s['snapshot'],2);v.query(1,s['snapshot'],3,post=1)
        self.assertEqual(before,self.hashes())
        deadline=v._views[1]['expiry'];now[0]=deadline-1
        with self.assertRaises(WorldError):v.query(1,s['snapshot'],3,post=999)
        self.assertEqual(deadline,v._views[1]['expiry'])
        now[0]=deadline
        with self.assertRaises(WorldError):v.query(1,s['snapshot'],2)

"""Explicit operator-selected stored-output/layout render fixtures. Never campaign writes."""
from .viewer import Viewer,pages
from world.store import WorldError
class StoredFixtureViewer(Viewer):
    def __init__(self,store,fixture):
        super().__init__(store)
        if set(fixture)!={'kind','label','body','sourcePostID','sourceBuild','sourceSHA256'} or fixture['kind'] not in ('stored_hermes_post','layout_fixture') or fixture['label'] not in ('Stored RICK','Layout fixture'):raise WorldError('fixture identity')
        pages(fixture['body']);self.fixture=fixture
    def open(self,view):
        r=super().open(view);r['posts']=3 if self.fixture['kind']=='layout_fixture' else 1;r['followers']=0;return r
    def query(self,view,snapshot,op,page=0,post=0):
        # Use normal session/scope validation; no author/exposure/store mutation.
        v=self._views.get(view)
        if not v or v['scope']!=self._scope() or v['snapshot']!=snapshot or self._clock()>=v['expiry']:raise WorldError('stale fixture')
        if op==4 and not page and not post:return {'pages':0,'rows':[]}
        count=3 if self.fixture['kind']=='layout_fixture' else 1
        if op==2 and not page and not post:return {'pages':1,'rows':[{'reference':i,'label':self.fixture['label']+(' '+str(i) if count>1 else '')} for i in range(1,count+1)]}
        if op==3 and 1<=post<=count:
            chunks=pages(self.fixture['body'])
            if type(page)==int and 0<=page<len(chunks):return {'pages':len(chunks),'text':chunks[page],'author':self.fixture['label'],'postID':self.fixture['sourcePostID']}
        raise WorldError('fixture reference')

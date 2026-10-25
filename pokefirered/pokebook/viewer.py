"""Trusted player projection. Snapshot handles are references, never grants."""
import time
from world.store import WorldError
from bridge.ui import MAP

SNAPSHOT_IDLE_SECONDS=600
MAX_RECORDS=192
MAX_PAGES=64
LINE=23

def pages(text):
    if not isinstance(text,str) or not text or len(text)>4096 or any(c not in MAP or c=='\n' for c in text):
        raise WorldError('unsupported published text')
    # Conservative 8px per glyph: 23*8=184 within the 208px reader.
    # Preserve every character, including spaces, across page boundaries.
    lines=[text[i:i+LINE] for i in range(0,len(text),LINE)]
    result=[bytes(MAP[c] for c in '\n'.join(lines[i:i+3])) for i in range(0,len(lines),3)]
    if len(result)>MAX_PAGES:raise WorldError('post page bound')
    return result

class Viewer:
    def __init__(self,store,clock=time.monotonic):
        self._store=store;self._clock=clock;self._views={};self._serial=0
    def _scope(self):
        s=self._store;c=s.campaign();v=s._one('SELECT * FROM social_view WHERE campaign=?',(c['id'],))
        if c['status'] not in ('paired','imported') or s.pending_save():raise WorldError('viewer unavailable')
        return (c['id'],c['active_branch'],v['epoch'],s.player_actor())
    def _public(self):
        s=self._store;state=s.social_state();battles=s.state()['battles'];player=s.player_actor()
        delivered={f['postID'] for f in state['feeds'].values() if f['recipient']==player}
        result=[]
        for p in state['posts'].values():
            b=battles.get(p['battleID'])
            involved=b and b['ended'] and b['trainerID'] and p['author']=='trainer:'+b['trainerID']
            if p['visibility']=='public' and (involved or p['postID'] in delivered):
                # Explicit allowlist. No claims/evidence/private episode serialization.
                result.append({'postID':p['postID'],'author':p['author'],'body':p['body']})
        # Replay preserves committed publication order. Content hashes are
        # stable references, not a chronology; sorting them scrambled a larger
        # campaign feed (e.g. Colton between Rick and Janice).
        publication_order={post_id:i for i,post_id in enumerate(state['posts'])}
        result.sort(key=lambda p:publication_order[p['postID']])
        if len(result)>MAX_RECORDS:raise WorldError('feed capacity exceeded')
        return result
    def _name(self,actor):
        name=self._store.get_actor(actor)['name']
        if not isinstance(name,str) or not 1<=len(name)<=18 or any(c not in MAP or c=='\n' for c in name):raise WorldError('unsupported author name')
        return name
    def open(self,view):
        if type(view)!=int or not 0<view<=0xffffffff:raise WorldError('invalid view')
        scope=self._scope();posts=self._public();player=scope[-1]
        followers=sorted({e['follower'] for e in self._store.social_state()['follows'].values() if e['followed']==player})
        if len(followers)>MAX_RECORDS:raise WorldError('follower capacity exceeded')
        old=self._views.get(view)
        if old and old['scope']==scope and self._clock()<old['expiry']:
            current={p['postID'] for p in posts}
            if any(p['postID'] not in current for p in old['posts']) or any(a not in followers for a in old['followers']):raise WorldError('revoked snapshot')
            old['expiry']=self._clock()+SNAPSHOT_IDLE_SECONDS
            return {'snapshot':old['snapshot'],'posts':len(old['posts']),'followers':len(old['followers'])}
        self._serial+=1
        if self._serial>0xffffffff:raise WorldError('snapshot exhausted')
        self._views.clear() # One native owner, no unbounded session cache.
        self._views[view]={'scope':scope,'snapshot':self._serial,'expiry':self._clock()+SNAPSHOT_IDLE_SECONDS,'posts':posts,'followers':followers}
        return {'snapshot':self._serial,'posts':len(posts),'followers':len(followers)}
    def close(self,view):self._views.pop(view,None)
    def query(self,view,snapshot,op,page=0,post=0):
        v=self._views.get(view)
        if not v or v['scope']!=self._scope() or v['snapshot']!=snapshot or self._clock()>=v['expiry']:raise WorldError('stale viewer')
        if type(page)!=int or not 0<=page<MAX_PAGES:raise WorldError('page bound')
        current={p['postID']:p for p in self._public()}
        followers={e['follower'] for e in self._store.social_state()['follows'].values() if e['followed']==v['scope'][-1]}
        if any(actor not in followers for actor in v['followers']):raise WorldError('revoked follower')
        # Revalidate visibility/participation, while keeping the initial stable IDs.
        if any(p['postID'] not in current for p in v['posts']):raise WorldError('revoked post')
        if op in (2,4):
            records=v['posts'] if op==2 else v['followers']
            total=(len(records)+2)//3
            if post or (total and page>=total) or (not total and page):raise WorldError('list page')
            rows=[]
            for index in range(page*3,min(page*3+3,len(records))):
                actor=records[index]['author'] if op==2 else records[index]
                rows.append({'reference':index+1,'label':self._name(actor)})
            v['expiry']=self._clock()+SNAPSHOT_IDLE_SECONDS
            return {'pages':total,'rows':rows}
        if op==3:
            if type(post)!=int or not 1<=post<=len(v['posts']):raise WorldError('post reference')
            p=v['posts'][post-1];chunks=pages(p['body'])
            if page>=len(chunks):raise WorldError('post page')
            author=self._name(p['author'])
            v['expiry']=self._clock()+SNAPSHOT_IDLE_SECONDS
            return {'pages':len(chunks),'text':chunks[page],'author':author,'postID':p['postID']}
        raise WorldError('operation')

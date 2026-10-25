"""Observed normal constructor receipt before qualified native tactical commands."""
import struct
from battle.transport import Handler
from world.store import WorldError

class CampaignHandler(Handler):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.constructions={}
    def recover(self,store):
        if self.recovered:return
        super().recover(store)
        state=store.decision_state()
        commitments={v['encounterID']:v for v in state['commitments'].values()}
        for encounter,installation in state['installations'].items():
            receipt=installation['receipt'];count=receipt.get('cumulativeNativeConstructorCount')
            if count is None:continue
            actor=commitments[encounter]['actor'];trainer=store.content.pack['trainers'][actor]['sourceTrainer']
            key=(receipt['nonce'],receipt['generation'])
            self.constructions[key]=max(self.constructions.get(key,0),count)
            self.constructions[(*key,trainer)]=count
        store.native_constructions=self.constructions
    def receive(self,msg,store,sock):
        if msg.kind==12:
            self.recover(store);store._launch(msg.nonce,msg.generation)
            if msg.typ!=12 or len(msg.payload)!=6:raise WorldError('constructor receipt shape')
            trainer,count=struct.unpack('<HI',msg.payload)
            qualified=self.m.get('qualified_trainers',[102,414])
            if trainer not in qualified or trainer==102 or count<1:raise WorldError('constructor receipt profile')
            previous=self.constructions.get((msg.nonce,msg.generation),0)
            if count==previous and self.constructions.get((msg.nonce,msg.generation,trainer))==count:
                self.log('duplicate-native-authored-constructor',{'trainer':trainer,'count':count,'session':msg.nonce});return
            if count!=previous+1:raise WorldError('constructor receipt sequence')
            self.constructions[(msg.nonce,msg.generation)]=count
            self.constructions[(msg.nonce,msg.generation,trainer)]=count
            store.native_constructions=self.constructions
            self.log('native-authored-constructor',{'trainer':trainer,'count':count,'session':msg.nonce});return
        return super().receive(msg,store,sock)

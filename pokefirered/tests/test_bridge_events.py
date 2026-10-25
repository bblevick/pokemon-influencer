import copy
import struct
import unittest
from bridge.events_wire import Message,Decoder,HEADER
from bridge.events import Consumer,decode_event,EVENT_HEADER,observation_for_context

def event(typ=1,seq=1,battle=1,turn=0,data=None,phase=None):
    if data is None:data=struct.pack('<IHBB',8,101,1,0) if typ==1 else b''
    if phase is None:phase={1:0,2:1,3:2,4:3,5:3,6:1}[typ]
    return Message(1,123,1,seq,456,3,EVENT_HEADER.pack(1,typ,seq,battle,turn,phase,10,len(data),0)+data)
def observation():
    return struct.pack('<HHHHI4H4B HBB4H I',101,13,10,20,0,33,81,0,0,10,10,0,0,1,48,0,33,0,0,0,0)

class EventsTests(unittest.TestCase):
    def setUp(self):self.c=Consumer(123,1,456)
    def test_envelope_roundtrip(self):
        m=event();self.assertEqual(Message.decode(m.encode()[2:]),m)
    def test_fragmented(self):
        m=event();d=Decoder();out=[]
        for b in m.encode():out+=d.feed(bytes([b]))
        self.assertEqual(out,[m])
    def test_transport_version(self):
        b=bytearray(event().encode()[2:]);b[4]=9
        with self.assertRaises(ValueError):Message.decode(b)
    def test_schema_version(self):
        m=event();b=bytearray(m.payload);b[0]=9
        with self.assertRaises(ValueError):decode_event(Message(1,123,1,1,456,3,bytes(b)))
    def test_bad_length(self):
        m=event();b=bytearray(m.payload);b[20]=9
        with self.assertRaises(ValueError):decode_event(Message(1,123,1,1,456,3,bytes(b)))
    def test_unknown_type(self):
        with self.assertRaises(ValueError):decode_event(event(99,phase=0))
    def test_bad_battle_id(self):
        with self.assertRaises(ValueError):decode_event(event(battle=0))
    def test_duplicate_idempotent(self):
        first,ack=self.c.accept(event());duplicate,ack2=self.c.accept(event())
        self.assertIsNone(duplicate);self.assertEqual(ack,ack2);self.assertEqual(self.c.last,1)
    def test_conflicting_duplicate(self):
        self.c.accept(event())
        with self.assertRaises(ValueError):self.c.accept(event(data=struct.pack('<IHBB',8,102,1,0)))
    def test_sequence_gap_explicit(self):
        self.c.accept(event());r,_=self.c.accept(event(2,3,turn=1));self.assertEqual(r['sequenceGap'],1);self.assertTrue(r['streamIncomplete'])
    def test_reused_battle_id(self):
        self.c.accept(event())
        with self.assertRaises(ValueError):self.c.accept(event(seq=2))
    def test_tracking_capacity_rejection_is_atomic(self):
        for i in range(1,33):self.c.accept(event(seq=i,battle=i))
        for i in range(33,40):
            with self.assertRaises(ValueError):self.c.accept(event(seq=i,battle=i))
            self.assertEqual(len(self.c.battles),32)
            self.assertEqual(self.c.last,32)
            self.assertEqual(len(self.c.gaps),0)
    def test_turn_order(self):
        self.c.accept(event())
        with self.assertRaises(ValueError):self.c.accept(event(2,2,turn=2))
    def test_phase_order(self):
        self.c.accept(event());self.c.accept(event(2,2,turn=1));self.c.accept(event(3,3,turn=1,data=struct.pack('<BBHH',0,1,33,1)))
        with self.assertRaises(ValueError):self.c.accept(event(6,4,turn=1,data=observation()))
    def test_invalid_phase(self):
        with self.assertRaises(ValueError):decode_event(event(2,2,turn=1,phase=3))
    def test_observation_bounds(self):
        b=bytearray(observation());b[26]=49
        with self.assertRaises(ValueError):decode_event(event(6,2,turn=1,data=bytes(b)))
    def test_no_false_legal_actions(self):
        b=bytearray(observation());b[27]=1
        with self.assertRaises(ValueError):decode_event(event(6,2,turn=1,data=bytes(b)))
    def test_model_scope(self):
        r=decode_event(event(6,2,turn=1,data=observation()));p=observation_for_context(r)
        self.assertFalse(p['legalActionsComplete']);self.assertNotIn('hp',p['opponentActive']);self.assertEqual(p['opponentActive']['revealedMoveIDs'],[33])
    def test_canonical_not_model_context(self):
        with self.assertRaises(ValueError):observation_for_context(decode_event(event()))
    def test_scope_closed(self):
        p=decode_event(event(6,2,turn=1,data=observation()))['payload']
        self.assertEqual(set(p),{'observerSide','trainerID','ownActive','opponentActive','legalActionsComplete'})
        self.assertEqual(set(p['opponentActive']),{'revealedSpeciesID','publicHPBar','publicHPBarMax','revealedMoveIDs'})
    def test_stale_run(self):
        m=event()
        with self.assertRaises(ValueError):Consumer(123,2,456).accept(m)
    def test_old_sequence(self):
        self.c.accept(event());self.c.cache.clear()
        with self.assertRaises(ValueError):self.c.accept(event())
    def test_payload_maximum(self):
        m=Message(1,123,1,1,456,3,b'x'*96);self.assertEqual(len(m.encode()),134);self.assertEqual(Message.decode(m.encode()[2:]),m)
        with self.assertRaises(ValueError):Message(1,123,1,1,456,3,b'x'*97).encode()
    def test_reset_separates_identity(self):
        self.c.accept(event());c=Consumer(123,2,456);m=event();new=Message(m.kind,m.nonce,2,m.sequence,m.tag,m.typ,m.payload);r,_=c.accept(new)
        self.assertEqual(r['sequence'],1);self.assertEqual(r['run'],2)
    def test_complete_trainer_lifecycle(self):
        records=[event(),event(2,2,turn=1),event(6,3,turn=1,data=observation()),event(3,4,turn=1,data=struct.pack('<BBHH',0,1,33,1)),event(4,5,turn=1,data=struct.pack('<HBB',101,1,1)),event(5,6,turn=1,data=struct.pack('<HBB',101,1,1))]
        for r in records:self.c.accept(r)
        self.assertTrue(self.c.battles[1]['ended'])
    def test_after_end_rejected(self):
        self.c.accept(event());self.c.accept(event(5,2,data=struct.pack('<HBB',101,1,1)))
        with self.assertRaises(ValueError):self.c.accept(event(2,3,turn=1))
    def test_gap_start_incomplete(self):
        r,_=self.c.accept(event(2,3,turn=1));self.assertTrue(r['streamIncomplete'])
    def test_wild_kind(self):
        r=decode_event(event(data=struct.pack('<IHBB',4,0,0,0)));self.assertEqual(r['payload']['battleKind'],'wild')
    def test_wrong_trainer(self):
        self.c.accept(event());self.c.accept(event(2,2,turn=1))
        with self.assertRaises(ValueError):self.c.accept(event(4,3,turn=1,data=struct.pack('<HBB',102,1,1)))
class ContextCompatibility(unittest.TestCase):
    def test_partial_visible_schema(self):
        import json
        from pathlib import Path
        from jsonschema import Draft202012Validator
        root=Path(__file__).resolve().parents[1]
        schema=json.loads((root/'schemas/ai/battle_request.schema.json').read_text())
        projection=observation_for_context(decode_event(event(6,2,turn=1,data=observation())))
        visible={'mode':'single_trainer','ownActive':projection['ownActive'],'opponentActive':projection['opponentActive']}
        Draft202012Validator(schema['properties']['visibleState']).validate(visible)
        self.assertNotIn('weather',visible)
        self.assertNotIn('status',visible['opponentActive'])
        self.assertFalse(projection['legalActionsComplete'])

if __name__=='__main__':unittest.main()

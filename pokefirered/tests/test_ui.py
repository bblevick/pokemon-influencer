import unittest,struct
from bridge.ui import Command,text_encode,text_decode,decode_response,Responses,RESPONSE
from bridge.events_wire import Message,Decoder

class UiTests(unittest.TestCase):
 def command(self,kind=2):return Command(81,9,kind,'Do you want to send this test response?',((11,'YES'),(22,'NO')) if kind==2 else ())
 def response(self,result=0,choice=22,run=3):return Message(5,2,run,81,4,7,RESPONSE.pack(1,2,81,9,result,choice))
 def test_notice_roundtrip(self):
  c=Command(81,9,1,'Bridge test message received.');self.assertEqual(Command.decode(c.message(2,3,4)).payload(),c.payload())
 def test_choice_roundtrip(self):
  c=self.command();self.assertEqual(Command.decode(Message.decode(c.message(2,3,4).encode()[2:])).payload(),c.payload())
 def test_text_allowlist(self):
  for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !?.-,/\'':self.assertEqual(text_decode(text_encode(c)),c)
 def test_wrap(self):self.assertEqual(text_decode(text_encode('Bridge test message received.')),'Bridge test message\nreceived.')
 def test_normalize(self):self.assertEqual(text_encode('a\r\nb'),text_encode('a\nb'))
 def test_maximum(self):self.assertEqual(len(text_encode('a'*24+'\n'+'b'*23)),48)
 def test_length_reject(self):
  for t in ['a'*49,'a'*24+'\n'+'b'*24,'a\nb\nc','a\n','\na','']:
   with self.subTest(t=t),self.assertRaises(ValueError):text_encode(t)
 def test_unsupported(self):
  for t in ['é','😀','{PLAYER}','a\t','a\0','a\r','a\x1b']:
   with self.subTest(t=t),self.assertRaises(ValueError):text_encode(t)
 def test_malformed_utf8(self):
  with self.assertRaises(UnicodeDecodeError):text_encode(b'\xc0\xaf')
 def test_encoded_controls(self):
  for c in [0xfc,0xfd,0xff,0xfa,0xfb,1,0x7f]:
   with self.subTest(c=c),self.assertRaises(ValueError):text_decode(bytes([c]))
 def test_choice_bounds(self):
  for choices in [(),((1,'YES'),),((1,'YES'),(2,'NO'),(3,'OTHER')),((1,'Y\0ES'),(2,'NO')),((1,'YES'),(1,'NO')),((0,'YES'),(2,'NO')),((65536,'YES'),(2,'NO'))]:
   with self.subTest(choices=choices),self.assertRaises(ValueError):Command(1,1,2,'hello',choices).payload()
 def test_expiry(self):
  for ttl in [0,59,901]:
   with self.assertRaises(ValueError):Command(1,1,1,'hello',ttl=ttl).payload()
 def test_response(self):self.assertEqual(decode_response(self.response(),self.command(),2,3,4)['choiceID'],22)
 def test_invalid_response(self):
  for choice in [0,1,12,65535]:
   with self.assertRaises(ValueError):decode_response(self.response(choice=choice),self.command(),2,3,4)
 def test_cancellation_timeout_busy(self):
  for status in [2,3,4,5,6,7]:self.assertEqual(decode_response(self.response(status,0),self.command(),2,3,4)['result'],status)
 def test_run_reset_rollback(self):
  for run in [1,2,4]:
   with self.assertRaises(ValueError):decode_response(self.response(run=run),self.command(),2,3,4)
 def test_duplicate_response(self):
  cache=Responses();self.assertIsNotNone(cache.accept(self.response(),self.command(),2,3,4));self.assertIsNone(cache.accept(self.response(),self.command(),2,3,4))
  with self.assertRaises(ValueError):cache.accept(self.response(choice=11),self.command(),2,3,4)
 def test_schema(self):
  c=self.command();m=c.message(2,3,4);bad=b'\x02'+m.payload[1:]
  with self.assertRaises(ValueError):Command.decode(Message(4,2,3,81,4,6,bad))
 def test_lengths(self):
  m=self.command().message(2,3,4)
  for data in [m.payload[:-1],m.payload+b'\0',m.payload[:8]]:
   with self.assertRaises(ValueError):Command.decode(Message(4,2,3,81,4,6,data))
 def test_transport_oversize(self):
  with self.assertRaises(ValueError):Message(4,2,3,81,4,6,b'\0'*97).encode()
  with self.assertRaises(ValueError):Decoder().feed(struct.pack('<H',133))

 def test_ui_is_not_npc_knowledge(self):
  from bridge.events import observation_for_context
  row=decode_response(self.response(),self.command(),2,3,4)
  with self.assertRaises(ValueError):observation_for_context(row)

class UiManifestTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import sys,json
  from pathlib import Path
  cls.root=Path(__file__).resolve().parents[1]
  sys.path.insert(0,str(cls.root/'tools'))
  from phase1_ui_build import verify_ui
  cls.verify=staticmethod(verify_ui)
  cls.manifest=json.loads((cls.root/'evidence/phase2/pokebook01/manifest-enabled.json').read_text())
 def altered(self):
  import copy
  return copy.deepcopy(self.manifest)
 def test_valid_actual_ELF_UI_manifest(self):self.verify(self.manifest)
 def test_forged_UI_address(self):
  m=self.altered();m['ui_mailbox']['address']+=4
  with self.assertRaises(ValueError):self.verify(m)
 def test_forged_UI_size(self):
  m=self.altered();m['ui_mailbox']['size']-=4
  with self.assertRaises(ValueError):self.verify(m)
 def test_forged_UI_payload_offset(self):
  m=self.altered();m['ui_mailbox']['fields']['payload']['offset']+=1
  with self.assertRaises(ValueError):self.verify(m)
 def test_forged_UI_harness_hash(self):
  m=self.altered();m['overlay_sha256']['bridge/ui_mgba.lua']='0'*64
  with self.assertRaises(ValueError):self.verify(m)

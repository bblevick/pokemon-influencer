import dataclasses
import socket
import struct
import unittest
from bridge.protocol import Decoder,Message,Responder,HEADER

class ProtocolTests(unittest.TestCase):
    def setUp(self):self.q=Message(1,12,3,1,99,1,b'POKE');self.r=Responder(12,3,99)
    def test_valid(self):self.assertEqual(self.r.handle(self.q).payload,b'PONG')
    def test_duplicate(self):self.assertEqual(self.r.handle(self.q),self.r.handle(self.q))
    def test_conflicting_duplicate(self):
        self.r.handle(self.q)
        with self.assertRaises(ValueError):self.r.handle(dataclasses.replace(self.q,payload=b'BAD!'))
    def test_magic(self):
        body=bytearray(self.q.encode()[2:]);body[0]=0
        with self.assertRaisesRegex(ValueError,'magic'):Message.decode(body)
    def test_version(self):
        body=bytearray(self.q.encode()[2:]);body[4]=2
        with self.assertRaisesRegex(ValueError,'version'):Message.decode(body)
    def test_oversized(self):
        with self.assertRaises(ValueError):dataclasses.replace(self.q,payload=b'x'*65).encode()
        with self.assertRaises(ValueError):Decoder().feed(struct.pack('<H',101))
    def test_corrupt_integrity(self):
        body=bytearray(self.q.encode()[2:]);body[-1]^=1
        with self.assertRaisesRegex(ValueError,'checksum'):Message.decode(body)
    def test_fragmented(self):
        d=Decoder();got=[]
        for byte in self.q.encode():got+=d.feed(bytes([byte]))
        self.assertEqual(got,[self.q])
    def test_multiple_frames(self):self.assertEqual(Decoder().feed(self.q.encode()*2),[self.q,self.q])
    def test_truncated_length(self):
        body=bytearray(self.q.encode()[2:]);body[26]=5
        with self.assertRaises(ValueError):Message.decode(body)
    def test_session_generation_build(self):
        for change in [{'nonce':13},{'generation':4},{'tag':100}]:
            with self.assertRaises(ValueError):self.r.handle(dataclasses.replace(self.q,**change))
    def test_stale_sequence(self):
        self.r.handle(dataclasses.replace(self.q,sequence=2))
        with self.assertRaises(ValueError):self.r.handle(self.q)
    def test_wraparound(self):
        self.r.handle(dataclasses.replace(self.q,sequence=0xffffffff))
        with self.assertRaises(ValueError):self.r.handle(self.q)
    def test_zero(self):
        with self.assertRaises(ValueError):self.r.handle(dataclasses.replace(self.q,sequence=0))
    def test_cache_bound(self):
        for i in range(1,65):self.r.handle(dataclasses.replace(self.q,sequence=i))
        with self.assertRaises(ValueError):self.r.handle(dataclasses.replace(self.q,sequence=65))
    def test_receive_bound(self):
        with self.assertRaises(ValueError):Decoder().feed(b'x'*257)
    def test_host_unavailable(self):
        # A local ephemeral port closed before connect; no network service assumed.
        s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
        with self.assertRaises(OSError):socket.create_connection(('127.0.0.1',port),timeout=.1)
    def test_host_disconnect(self):
        a,b=socket.socketpair();b.close()
        with a:self.assertEqual(a.recv(1),b'')
    def test_host_timeout(self):
        a,b=socket.socketpair();a.settimeout(.01)
        with a,b:
            with self.assertRaises(socket.timeout):a.recv(1)
if __name__=='__main__':unittest.main()

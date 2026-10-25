"""Compiled native validator and isolated host copies, not emulator substitutes."""
import unittest,json,copy,tempfile,sqlite3,subprocess,re,struct
from pathlib import Path
from system1.native import encode_plan,verify_build,NativePreparationStore
from tests.test_prep01 import BUILD,TAG,flash,BROCK
from prep.store import PrepStore
from prep.domain import resolve_preparation_envelope,generate_preparation_candidates
from world.saves import fingerprint
from system1.provider import run_selection,FixtureDecisionProvider
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase3/system1_01a'
class NativeContractTests(unittest.TestCase):
    def test_all_sixteen_exact_wire_choices_and_native_validator(self):
        r=json.loads((E/'rick-request.json').read_text())['request'];c=json.loads((E/'commitment.json').read_text());m=json.loads((E/'manifest-native.json').read_text());src=(ROOT/'native/system1_01a/pi_preparation.c').read_text();a=src.index('static bool8 Valid(void)');b=src.index('\nvoid PiPreparation_Init',a);header=(ROOT/'native/system1_01a/pi_preparation.h').read_text().replace('#include "global.h"','').replace('u8 PiPreparation_CreateParty(struct Pokemon *party,u16 trainer);','')
        code='#include <stdint.h>\n#include <stdio.h>\n#include <stddef.h>\ntypedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;typedef uint8_t bool8;\n#define TRUE 1\n#define FALSE 0\n#define PI_BUILD_TAG '+str(m['build_tag'])+'u\n#include "constants/species.h"\n#include "constants/moves.h"\n#include "constants/trainers.h"\n'+header+'\nvolatile struct PiPreparationMailbox gPiPreparation;struct {u32 nonce,generation;} gPiMailbox;\n'+src[a:b]+'\nint main(void){while(fread((void*)&gPiPreparation,168,1,stdin)==1){gPiMailbox.nonce=gPiPreparation.nonce;gPiMailbox.generation=gPiPreparation.generation;printf("%d\\n",Valid());}return 0;}'
        plans=[]
        for candidate in r['bundle']['candidateSet']['candidates']:
            packet=encode_plan({**c,'candidate':candidate},123,1,1,m['build_tag']);self.assertEqual(len(packet),168);plans.append(packet)
            installing=bytearray(packet);installing[59]=2;plans.append(bytes(installing))
            for i,lineage in enumerate(candidate['order']):
                p=next(p for p in candidate['party'] if p['lineage']==lineage);wire=struct.unpack_from('<HBB6H',packet,72+16*i);self.assertEqual(list(wire[3:7]),p['moves']);self.assertEqual(wire[0],p['species']);self.assertEqual(wire[1],p['level'])
        corrupt=bytearray(plans[0]);corrupt[80]^=1;badtag=bytearray(plans[0]);badtag[4]^=1;plans+= [bytes(corrupt),bytes(badtag)]
        with tempfile.TemporaryDirectory() as td:
            cfile=Path(td)/'valid.c';exe=Path(td)/'valid';cfile.write_text(code);subprocess.run(['clang','-Werror','-I',str(ROOT/'include'),str(cfile),'-o',str(exe)],check=True);result=subprocess.check_output([str(exe)],input=b''.join(plans)).decode().splitlines()
        self.assertEqual(result,['1']*32+['0']*2)
    def test_brock_real_sole_candidate_skips_model(self):
        layout=json.loads((ROOT/'config/prep_save_layout.json').read_text())
        with tempfile.TemporaryDirectory() as td,PrepStore(Path(td)/'w.sqlite3',BUILD,TAG) as w:
            save=fingerprint(flash(),layout['sectionSizes']);w.import_save(save);w.authorize_launch(123,save);w.activate_preparation();battery=Path(td)/'normal.sav';battery.write_bytes(flash(2));intent=w.begin_save(123,save);w.finish_save_with_progression(intent,battery,{'event':'savedataUpdated','nonce':123,'run':1,'eventCounter':0,'ack':0,'depth':0,'state':0,'drops':0,'counter':2});bundle={'candidateSet':generate_preparation_candidates(resolve_preparation_envelope(w,BROCK,'first'))};self.assertEqual(len(bundle['candidateSet']['candidates']),1)
            class Sink:
                def finish_selection(self,p,r,source):return {'request':p,'result':r,'source':source}
            candidates=bundle['candidateSet']['candidates'];choice=candidates[0]['candidateID'];provider=FixtureDecisionProvider('must-not-call');result=run_selection(Sink(),{'status':'active','request':{'choices':{choice:'Authored Geodude 12 and Onix 14.'}}},provider);self.assertEqual(provider.calls,0);self.assertEqual(result['source'],'sole');self.assertEqual(result['result']['choiceID'],choice)
    def test_explicit_resume_rejects_unrelated_history_and_nonce_reuse(self):
        from system1.provider import FixtureDecisionProvider,run_selection
        from world.saves import layout_from_build
        def save_identity(path):return fingerprint(Path(path).read_bytes(),layout_from_build(ROOT/json.loads((E/'manifest-native.json').read_text())['rom_path']))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'copy.sqlite3';src=sqlite3.connect(ROOT/'.local/strategy01-memo/world.sqlite3');dst=sqlite3.connect(path);src.backup(dst);src.close();dst.close()
            with NativePreparationStore(path,E/'manifest-native.json') as w:
                actor='trainer:fr:trainer:0102';job=w.begin_selection(actor);d=run_selection(w,job,FixtureDecisionProvider(job['request']['fallbackCandidateID']),source='mock');c=w.commit_preparation(d['decisionID']);save=save_identity(ROOT/'.local/strategy01-memo/after-live-memo.sav');w.resume_unpaired_preparation(2026100401,save);self.assertEqual(w.locked_preparation(actor),c)
                with self.assertRaises(ValueError):w.resume_unpaired_preparation(2026100401,save)
                w._tx(lambda:w._append_decision('NATIVE_PROVENANCE','test-advance',{'nativeDelivery':{'fixture':True}}))
                with self.assertRaises(ValueError):w.resume_unpaired_preparation(2026100402,save)
    def test_build_checks_and_wrong_tag(self):
        proof,m=verify_build(E/'manifest-native.json');self.assertNotEqual(proof['baselineROM'],proof['nativeROM']);self.assertEqual(m['preparation_checks']['changed'],[])
        from tests.test_world01 import msg
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'copy.sqlite3';src=sqlite3.connect(ROOT/'.local/system1_01a/world.sqlite3');dst=sqlite3.connect(path);src.backup(dst);src.close();dst.close()
            with NativePreparationStore(path,E/'manifest-native.json') as w,self.assertRaises(ValueError):w.ingest(msg(1,1))

"""Explicit controlled-build compatibility, not a general save/ROM migration."""
import json,struct,hashlib,uuid
from pathlib import Path
from dataclasses import replace
from roster.extract import file_hash,digest
from world.saves import layout_from_build
from world.store import WorldError
from .store import PreparationDecisionStore
ROOT=Path(__file__).resolve().parents[1]
def verify_build(manifest):
    m=json.loads(Path(manifest).read_text());rom=ROOT/m['rom_path'];old=json.loads((ROOT/'evidence/phase2/pokebook01/manifest-enabled.json').read_text());baseline=ROOT/old['rom_path'];dest=rom.parent
    if file_hash(rom)!=m['rom_sha256'] or file_hash(rom.with_suffix('.elf'))!=m['elf_sha256']:raise ValueError('controlled native build checksum mismatch')
    if file_hash(baseline)!=old['rom_sha256']:raise ValueError('baseline build changed')
    if list(layout_from_build(rom))!=list(layout_from_build(baseline)):raise ValueError('save section incompatibility')
    layout=json.loads((ROOT/'config/prep_save_layout.json').read_text())
    for path,sha in layout['sourceFiles'].items():
        if file_hash(ROOT/path)!=sha or file_hash(dest/path)!=sha:raise ValueError('native save/progression source differs')
    for path in ('src/pokemon.c','src/battle_ai_script_commands.c','src/data/trainers.h','src/data/trainer_parties.h'):
        if file_hash(dest/path)!=file_hash(baseline.parent/path):raise ValueError('native constructors/AI/authored parties differ')
    for path,sha in m['preparation_sources'].items():
        if file_hash(dest/path)!=sha:raise ValueError('controlled overlay mismatch')
    if not all(m['preparation_checks'][k] for k in ('priorRAMSymbolsUnchanged','size168','saveSectionSizesUnchanged')):raise ValueError('native allocation checks')
    catalog=json.loads((ROOT/'config/roster_catalog.json').read_text())
    for source in catalog['sources']:
        path=source['path']
        if file_hash(ROOT/path)!=source['sha256']:raise ValueError('source catalog changed')
        if path.startswith('config/'):continue # host registry, not compiled ROM data
        if path=='src/battle_main.c':
            body=(dest/path).read_text().replace('#include "pi_preparation.h"\n','').replace('    u8 preparedCount = PiPreparation_CreateParty(party, trainerNum);\n','').replace('    if (preparedCount) return preparedCount;\n','')
            if hashlib.sha256(body.encode()).hexdigest()!=source['sha256']:raise ValueError('unqualified trainer constructor edits')
        elif file_hash(dest/path)!=source['sha256']:raise ValueError('native mechanical catalog source differs: '+path)
    return {'schemaVersion':1,'baselineROM':old['rom_sha256'],'baselineTag':old['build_tag'],'nativeROM':m['rom_sha256'],'nativeTag':m['build_tag'],'manifestSHA256':file_hash(manifest),'saveLayoutSHA256':digest(layout),'catalogSHA256':catalog['catalogSHA256'],'catalogSourcesVerified':len(catalog['sources']),'scope':'controlled SYSTEM1-01A build only; unchanged SaveBlock/flags/section sources; baseline catalog remains authoritative'},m
class NativePreparationStore(PreparationDecisionStore):
    def __init__(self,path,manifest):
        self.compatibility,self.native_manifest=verify_build(manifest)
        super().__init__(path,self.compatibility['baselineROM'],self.compatibility['baselineTag'])
    def resume_unpaired_preparation(self,nonce,save):
        """Explicit first installation continuation, never ordinary restore.
        Only host selection/commitment may have advanced since the exact battery.
        Every other timeline prefix must still equal its paired checkpoint.
        """
        def action():
            cp=self.get_save_checkpoint(save.fingerprint);c=self.campaign()
            if not cp or (cp['campaign'],cp['branch'],cp['cursor'])!=(c['id'],c['active_branch'],c['cursor']) or c['pending_fork'] or self.pending_save():raise WorldError('preparation continuation checkpoint mismatch')
            if hashlib.sha256(json.dumps(self.state(),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=cp['state_sha256']:raise WorldError('unsaved canonical events')
            for name in ('memory','social','puppeteer','strategy','prep'):
                paired=self._one('SELECT cutoff FROM '+name+'_checkpoints WHERE checkpoint=?',(cp['id'],));active=self._one('SELECT cutoff FROM '+name+'_view')
                if not paired or paired['cutoff']!=active['cutoff']:raise WorldError('unsaved '+name+' history')
            baseline=super(PreparationDecisionStore,self).preparation_state()
            if digest(baseline)!=self._one('SELECT state_sha FROM prep_checkpoints WHERE checkpoint=?',(cp['id'],))['state_sha']:raise WorldError('unsaved baseline preparation')
            old=self._one('SELECT cutoff FROM preparation_decision_checkpoints WHERE checkpoint=?',(cp['id'],))['cutoff']
            tail=[e for e in self._decision_events() if e['seq']>old]
            if any(e['kind']=='NATIVE_PROVENANCE' and not e['payload'].get('explicitPreparationContinuation') for e in tail):raise WorldError('native session already advanced')
            events=[e for e in tail if e['kind']!='NATIVE_PROVENANCE']
            if len(events)!=2 or [e['kind'] for e in events]!=['DECISION','COMMITMENT'] or any(e['cursor']!=cp['cursor'] for e in events):raise WorldError('only one new preparation may be continued')
            if type(nonce)!=int or not 0<nonce<=0xffffffff or self._one('SELECT 1 FROM launches WHERE nonce=?',(nonce,)):raise WorldError('fresh continuation nonce required')
            origin=str(uuid.uuid4());self.db.execute("UPDATE launches SET status='inactive' WHERE campaign=?",(c['id'],));self.db.execute('INSERT INTO launches VALUES(?,?,?,?,?)',(origin,nonce,c['id'],save.fingerprint,'active'))
            self._append_decision('NATIVE_PROVENANCE','continuation:'+str(nonce),{'compatibility':self.compatibility,'explicitPreparationContinuation':True,'checkpoint':cp['id'],'saveFingerprint':save.fingerprint,'nonce':nonce,'previousDecisionCutoff':old,'commitmentID':events[-1]['payload']['commitmentID']})
            return origin
        return self._tx(action)
    def _tx(self,action):
        if self.db.in_transaction:return action()
        return super()._tx(action)
    def ingest(self,message):
        if message.tag!=self.compatibility['nativeTag']:raise WorldError('controlled native transport build mismatch')
        def action():
            result=super(NativePreparationStore,self).ingest(replace(message,tag=self.tag))
            self._append_decision('NATIVE_PROVENANCE',f'{message.nonce}:{message.generation}:{message.sequence}',{'compatibility':self.compatibility,'nativeDelivery':{'nonce':message.nonce,'generation':message.generation,'sequence':message.sequence,'tag':message.tag,'wireSHA256':digest(message.encode().hex())},'normalizedLogicalBuild':self.build})
            return result
        return self._tx(action)

def encode_plan(commitment,nonce,generation,sequence,tag):
    if not commitment.get('locked') or commitment['phase']!='COMMITTED':raise ValueError('locked commitment required')
    c=commitment['candidate'];rows={x['lineage']:x for x in c['party']};env={x['lineage']:x for x in commitment['requestEnvelopeCompanions']} if 'requestEnvelopeCompanions' in commitment else None
    if commitment['actor']!='trainer:fr:trainer:0102' or len(rows)!=2 or c['acquisitionCount'] or any(c['battleItems']):raise ValueError('unsupported prepared native envelope')
    payload=bytearray(168);struct.pack_into('<6I',payload,0,0x50525031,tag,nonce,generation,sequence,0);payload[24:56]=bytes.fromhex(commitment['commitmentID'].split(':')[1]);struct.pack_into('<HBB',payload,56,102,2,1)
    for i,lineage in enumerate(c['order']):
        p=rows[lineage];original={0:13,1:10}[int(p['origin'].split(':')[1])]
        if p['heldItem'] or p['fixedIV']!=0 or not 6<=p['level']<=10:raise ValueError('native opening representation unsupported')
        struct.pack_into('<HBB6H',payload,72+16*i,p['species'],p['level'],p['fixedIV'],*p['moves'],p['heldItem'],original)
    h=2166136261
    for value in payload[8:20]+payload[24:59]+payload[72:]:h=((h^value)*16777619)&0xffffffff
    struct.pack_into('<I',payload,20,h);return bytes(payload)

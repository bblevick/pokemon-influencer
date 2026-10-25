"""Discard-only sink for explicitly owned synthetic Hermes qualification DBs.

Retrieval, envelope adaptation and domain validation are production code. Only
the final transaction sink differs: it has no publication/episode/delivery call.
"""
import json, sqlite3, uuid
from contextlib import closing
from pathlib import Path
from puppeteer.store import PuppeteerStore
from world.store import WorldError, dump
from memory.store import digest

class QualificationStore(PuppeteerStore):
    qualification_only=True
    def __init__(self,path,*args,**kwargs):
        path=Path(path).resolve()
        if not path.is_file():raise WorldError('qualification requires an existing owned synthetic fixture')
        try:
            with closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)) as db:
                row=db.execute('SELECT namespace,database_path,campaign FROM hermes_qualification_owner').fetchone()
                campaign=db.execute('SELECT id FROM campaigns').fetchone()
                meta={k:json.loads(v) for k,v in db.execute('SELECT * FROM metadata')}
            if not row or row[1]!=str(path) or not campaign or row[2]!=campaign[0]:raise WorldError('qualification fixture identity')
            uuid.UUID(row[0].removeprefix('hermes-qualification:'))
            if not row[0].startswith('hermes-qualification:') or meta['build']!='a'*64 or meta['tag']!=123:raise WorldError('qualification fixture namespace/build')
        except (sqlite3.Error,ValueError,KeyError) as error:raise WorldError('not an owned synthetic qualification database') from error
        self.qualification_namespace=row[0]
        super().__init__(path,*args,**kwargs)

    def _finish_discard(self,job,result=None,reason=None,model=None):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            _,scope=self._job(job,allow_expired=result is None)
            if result is not None:self._validate_result(scope,result)
            outcome={'qualificationValid':result is not None,'committed':False,'producer':'hermes_qualification','namespace':self.qualification_namespace,'jobID':job,'result':result,'resultSHA256':digest(result) if result is not None else None,'inputScopeSHA256':digest(scope),'model':model,'reason':reason}
            self.db.execute("UPDATE puppeteer_jobs SET status='completed',result_sha=?,outcome=? WHERE id=?",(outcome['resultSHA256'],dump(outcome),job))
            self.audit(job,'qualification-discard',outcome)
            self.db.execute('COMMIT');return outcome
        except Exception:
            self.db.execute('ROLLBACK');raise

    def settle_job(self,job_id,result,*,producer,reason=None,model=None,fail=False):
        if producer!='hermes' or fail:raise WorldError('qualification has no campaign commit path')
        return self._finish_discard(job_id,result,model=model)

    def fallback(self,job_id,reason='qualification_failed'):
        # Even failure cannot publish or create a private episode in this sink.
        return self._finish_discard(job_id,reason=reason)

def open_qualification(path):
    return QualificationStore(path,'a'*64,123)

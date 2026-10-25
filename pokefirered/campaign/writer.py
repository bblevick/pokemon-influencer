"""Serialize fresh Hermes tools onto the managed host's SQLite owner thread."""
import queue
from concurrent.futures import Future,TimeoutError
from contextlib import contextmanager
from world.store import WorldError

class WriterMailbox:
    def __init__(self):self.requests=queue.Queue(maxsize=32);self.closed=False
    def call(self,operation):
        if self.closed:raise WorldError('campaign_writer_closed')
        result=Future();self.requests.put((operation,result),timeout=1)
        try:return result.result(timeout=5)
        except TimeoutError:
            result.cancel();raise WorldError('campaign_writer_rpc_timeout') from None
    def drain(self,store):
        for _ in range(16):
            try:operation,result=self.requests.get_nowait()
            except queue.Empty:break
            if result.done():continue
            try:result.set_result(operation(store))
            except Exception as error:result.set_exception(error)
    @contextmanager
    def open(self,path):yield Proxy(self)
    def close(self):
        self.closed=True
        while not self.requests.empty():
            _,result=self.requests.get_nowait()
            if not result.done():result.set_exception(WorldError('campaign_writer_closed'))

class Tools:
    def __init__(self,mailbox,job):self.mailbox=mailbox;self.job=job
    def __getattr__(self,name):
        if name not in ('get_battle_evidence','recall_puppeteer_memory','get_actor_context','submit_recap_and_memory_result'):raise AttributeError(name)
        return lambda *a,**kw:self.mailbox.call(lambda w:getattr(w.job_tools(self.job),name)(*a,**kw))

class Proxy:
    def __init__(self,mailbox):self.mailbox=mailbox
    def __getattr__(self,name):
        if name not in ('_job','_one','audit','recover_job','fallback','finish_recall_job'):raise AttributeError(name)
        return lambda *a,**kw:self.mailbox.call(lambda w:getattr(w,name)(*a,**kw))
    def job_tools(self,job):return Tools(self.mailbox,job)

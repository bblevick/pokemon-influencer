"""Version-aware generic campaign writer; faction delivery remains ViralityMixin."""
from dataclasses import asdict
from .expansion import ExpansionStore
from content.rocket import RocketContent
from prep.companions import authored_companions

class RocketStore(ExpansionStore):
 content_type=RocketContent
 def _select_content(self):
  receipt=self.preparation_state().get('contentExtension')
  if not receipt:self.content=self._base_content;return
  for content in (self._expanded_content,self._expanded_content.previous):
   if receipt['contentSHA256']==content.hash:self.content=content;return
  raise ValueError('campaign content changed; explicit future version adoption required')
 def adopt_content(self):
  def action():
   current=self.preparation_state().get('contentExtension');extension=self._expanded_content
   if current and current['contentSHA256']==extension.hash:return current
   if not current or current['contentSHA256']!=extension.previous.hash:raise ValueError('accepted ordinary content parent required')
   self._writable()
   if self.pending_save() or not all(self.preparation_state()['progression']['flags'].values()):raise ValueError('settled paired Boulder progression required')
   receipt={'contentSHA256':extension.hash,'baseContentSHA256':self._base_content.hash,'version':extension.extension['version'],'packID':extension.extension['packID']}
   self._append_prep('CONTENT_ADOPTED',receipt['packID'],receipt)
   for actor,t in extension.delta['trainers'].items():
    self._append_prep('INITIALIZED',actor,{'actor':actor,'companions':[asdict(c) for c in authored_companions(extension.cat,actor,t['sourceTrainer'])],'resources':{'owner':actor,'stock':[],'categories':t['resources']['categories'],'restock':False,'contentSHA256':extension.hash,'sourceTrainer':t['sourceTrainer']},'sourceTrainer':t['sourceTrainer'],'retainedOrigins':t['retainedOrigins'],'active':True})
   return receipt
  return self._tx(action)

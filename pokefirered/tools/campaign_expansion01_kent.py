#!/usr/bin/env python3
"""Same final campaign; optional explicit read-only nine-post native fixture."""
import os,sys
os.environ['POKEINFLUENCER_EXPERIMENT']='campaign_expansion01'
os.environ['POKEINFLUENCER_CAMPAIGN_FINAL']='1'
from campaign_expansion01 import main
if '--pagination-fixture' in sys.argv:
 if sys.argv[1]!='host' or '--live' in sys.argv:raise ValueError('fixture requires offline host')
 sys.argv.remove('--pagination-fixture')
 import strategy01_host
 from pokebook.viewer import Viewer
 class PaginationFixture(Viewer):
  def _public(self):
   posts=super()._public()
   assert len(posts) in (8,9), 'C3/current pre-Kent fixture only'
   return posts+[{'postID':'fixture-only-not-a-campaign-post-'+str(i),'author':'trainer:fr:trainer:0108','body':'READ ONLY TEST FIXTURE '+str(i+1)+'. '+('Safe pagination text. '*8)} for i in range(12-len(posts))]
 strategy01_host.Viewer=PaginationFixture
if __name__=='__main__':main()

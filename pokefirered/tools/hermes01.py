#!/usr/bin/env python3
"""Trusted HERMES acceptance/admin tools. These are not Hermes tool grants."""
import argparse,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from memory01 import manifest,save_identity
from puppeteer.store import PuppeteerStore
E=ROOT/'evidence/phase2/hermes01'
RICK='trainer:fr:trainer:0102';JANICE='trainer:fr:trainer:0116';DOUG='trainer:fr:trainer:0103'


def open_store(path):
    m=manifest();return PuppeteerStore(path,m['rom_sha256'],m['build_tag'])


def offline_store(path):
    with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:
        meta={k:json.loads(v) for k,v in db.execute('SELECT * FROM metadata')}
    return PuppeteerStore(path,meta['build'],meta['tag'])


def snapshot(w):
    state=w.social_state()
    return {'campaign':w.campaign(),'canonicalSHA256':w.verify_replay(),'memorySHA256':w.verify_memory_replay(),'socialSHA256':w.verify_social_replay(),'social':state,
            'puppeteer':w.puppeteer_state(),'puppeteerSHA256':w.verify_puppeteer_replay(),'trainerPackets':{a:w.trainer_packet(a) for a in (RICK,JANICE,DOUG)},
            'playerFollowerCount':sum(e['followed']==w.player_actor() for e in state['follows'].values()),
            'rick':w.for_actor(RICK).context(),'janice':w.for_actor(JANICE).context(),'doug':w.for_actor(DOUG).context(),
            'janiceFeedMetadata':w.for_social_actor(JANICE).feed_metadata(),
            'counts':{t:w._one('SELECT COUNT(*) n FROM '+t)['n'] for t in ('events','observations','memory_evidence','social_log')},'romSHA256':w.build}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['import','activate','snapshot','tick','expose','retry','save-begin'])
    p.add_argument('--database',type=Path,default=ROOT/'.local/hermes01/world.sqlite3')
    p.add_argument('--save',type=Path);p.add_argument('--output',type=Path);p.add_argument('--post');p.add_argument('--tick',type=int)
    a=p.parse_args();a.database.parent.mkdir(parents=True,exist_ok=True)
    with (open_store(a.database) if a.command in ('import','save-begin') else offline_store(a.database)) as w:
        if a.command=='import':result=w.import_save(save_identity(a.save))
        elif a.command=='activate':result=w.activate_puppeteer()
        elif a.command=='tick':w.tick(a.tick);result=snapshot(w)
        elif a.command=='expose':
            post=a.post or next(iter(w.social_state()['posts']))
            exposure=w.for_social_actor(JANICE).expose(post)
            view=w.for_actor(JANICE)
            result={'snapshot':snapshot(w),'exposure':exposure,'publicPost':w.for_social_actor(JANICE).read_post(post),'recipientProvenance':[view.provenance(i) for i in exposure['memoryIDs']]}
        elif a.command=='retry':
            state=w.social_state();w.tick(state['tick'])
            post=a.post or next(iter(state['posts']))
            w.for_social_actor(JANICE).expose(post);result=snapshot(w)
        elif a.command=='save-begin':
            cfg=json.loads((ROOT/'.local/social01-launch.json').read_text());result={'intent':w.begin_save(cfg['nonce'],save_identity(a.save or cfg['save']))}
        else:result=snapshot(w)
    text=json.dumps(result,indent=2)+'\n'
    if a.output:a.output.write_text(text)
    print(text)

#!/usr/bin/env python3
"""Bounded native walking from pinned collision data; no game memory writes.

Read-only current-position diagnostics are test automation, never PREP inputs.
Pause at battles/map transitions/blocked steps for a reviewed native response.
"""
from __future__ import annotations
import json,re,struct,collections,argparse,hashlib,heapq
from prep01 import ROOT,E,open_store
from prep01_input import segment

def position(label):
    records=[json.loads(x) for x in (E/'emulator.jsonl').read_text().splitlines()]
    p=next(x for x in reversed(records) if x['event']=='prep-position' and x['detail'].startswith(label+' '))
    m=next(x for x in reversed(records) if x['event']=='prep-map' and x['detail'].startswith(label+' '))
    xy=tuple(map(int,re.search(r'x=(-?\d+) y=(-?\d+)',p['detail']).groups()))
    group,num=map(int,re.search(r'group=(\d+) num=(\d+)',m['detail']).groups())
    groups=json.loads((ROOT/'data/maps/map_groups.json').read_text())
    return groups[groups['group_order'][group]][num],xy

def walk(mapname,goal,label,bound=40,config_path=None):
    cfg=json.loads((config_path or ROOT/'.local/prep01-launch.json').read_text())
    spec=json.loads((ROOT/f'data/maps/{mapname}/map.json').read_text())
    layout=next(x for x in json.loads((ROOT/'data/layouts/layouts.json').read_text())['layouts'] if x.get('id')==spec['layout'])
    width,height=layout['width'],layout['height'];raw=(ROOT/layout['blockdata_filepath']).read_bytes();tiles=struct.unpack('<'+str(width*height)+'H',raw)
    blocked={(x['x'],x['y']) for x in spec['object_events']}|{(x['x'],x['y']) for x in spec['warp_events'] if (x['x'],x['y'])!=goal}
    # Native forest acceptance path prefers dry ground using source attributes.
    attrs=None
    if mapname in ('ViridianForest','Route3','Route4','MtMoon_1F','MtMoon_B1F','MtMoon_B2F'):
        attrs=[]
        secondary={'ViridianForest':'viridian_forest','Route3':'pewter_city','Route4':'cerulean_city','MtMoon_1F':'cave','MtMoon_B1F':'cave','MtMoon_B2F':'cave'}[mapname]
        for part in ('primary/general','secondary/'+secondary):
            data=(ROOT/f'data/tilesets/{part}/metatile_attributes.bin').read_bytes();attrs.append(struct.unpack('<'+str(len(data)//4)+'I',data))
    def travel_cost(tile):
        if attrs is None:return 1
        index=tile&0x3ff;attr=attrs[0][index] if index<640 else attrs[1][index-640]
        return 101 if ((attr>>24)&7) else 1
    def edge_allowed(start,end):
        # Pinned IsMetatileDirectionallyImpassable: current opposite face,
        # destination entry face. Collision bits alone do not describe cave cliffs.
        if attrs is None:return True
        def behavior(p):
            index=tiles[p[1]*width+p[0]]&0x3ff
            return (attrs[0][index] if index<640 else attrs[1][index-640])&0x1ff
        blocked_faces={'east':{0x30,0x34,0x36},'west':{0x31,0x35,0x37},'north':{0x32,0x34,0x35},'south':{0x33,0x36,0x37}}
        outgoing,incoming={(0,1):('south','north'),(0,-1):('north','south'),(1,0):('west','east'),(-1,0):('east','west')}[(end[0]-start[0],end[1]-start[1])]
        return behavior(start) not in blocked_faces[outgoing] and behavior(end) not in blocked_faces[incoming]
    history=[]
    for i in range(bound):
        shot=f'{label}-{i}';segment(shot,['key 9 0 2']);actual,start=position(shot)
        if actual!=mapname:return {'status':'map-transition','map':actual,'position':start,'steps':history}
        if start==goal:return {'status':'reached','map':actual,'position':start,'steps':history}
        with open_store(cfg['database']) as w:
            if any(not b['ended'] for b in w.state()['battles'].values()):return {'status':'battle','map':actual,'position':start,'steps':history}
        queue=[(0,start)];distance={start:0};back={start:None}
        while queue:
            cost,p=heapq.heappop(queue)
            if cost!=distance[p]:continue
            if p==goal:break
            for dx,dy in ((0,-1),(-1,0),(1,0),(0,1)):
                n=p[0]+dx,p[1]+dy
                if 0<=n[0]<width and 0<=n[1]<height and (not tiles[n[1]*width+n[0]]&0xc00 or n==goal and any((e['x'],e['y'])==goal for e in spec['warp_events'])) and n not in blocked and edge_allowed(p,n):
                    next_cost=cost+travel_cost(tiles[n[1]*width+n[0]])
                    if next_cost<distance.get(n,10**9):distance[n]=next_cost;back[n]=p;heapq.heappush(queue,(next_cost,n))
        if goal not in back:raise ValueError('no source collision route')
        path=[];p=goal
        while p!=start:path.append(p);p=back[p]
        path=path[::-1];dx,dy=path[0][0]-start[0],path[0][1]-start[1];count=1
        for a,b in zip(path,path[1:]):
            if (b[0]-a[0],b[1]-a[1])!=(dx,dy) or count==8:break
            count+=1
        key={(0,-1):6,(0,1):7,(-1,0):5,(1,0):4}[dx,dy]
        move=f'{label}-move-{i}';segment(move,[f'key {key} {count*16} 90']);aftermap,after=position(move)
        history.append({'from':start,'to':after,'map':aftermap,'command':f'key {key} {count*16} 90','collisionSHA256':hashlib.sha256(raw).hexdigest()})
        if after==start: return {'status':'blocked-native','map':aftermap,'position':after,'steps':history}
    return {'status':'bound','steps':history}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('map');p.add_argument('x',type=int);p.add_argument('y',type=int);p.add_argument('--label',required=True);a=p.parse_args();out=walk(a.map,(a.x,a.y),a.label);(E/(a.label+'-route.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

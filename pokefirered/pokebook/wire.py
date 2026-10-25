"""Viewer schema2 within BRIDGE-03 kind3; old schema1 notices unchanged."""
import struct
from bridge.ui import MAP
from world.store import WorldError
HEADER=struct.Struct('<HHIIIIHH') # schema,op/status,request,view,snapshot,post,page,pages
REQUEST=struct.Struct('<HHIIIIHH')

def respond(viewer,payload):
    if len(payload)!=24:raise WorldError('viewer request length')
    ver,op,req,view,snap,post,page,reserved=REQUEST.unpack(payload)
    if ver!=2 or op not in (1,2,3,4,5) or not req or not view or reserved:raise WorldError('viewer schema/identity')
    body=b'';total=0
    try:
        if op==1:
            if snap or post or page:raise WorldError('open arguments')
            result=viewer.open(view);snap=result['snapshot'];total=result['posts'];body=struct.pack('<I',result['followers'])
        elif op==5:
            viewer.close(view)
        else:
            result=viewer.query(view,snap,op,page,post);total=result['pages']
            if op==3:body=result['text']
            else:
                for row in result['rows']:
                    label=bytes(MAP[c] for c in row['label'])
                    body+=struct.pack('<I',row['reference'])+label+b'\xff'+bytes(18-len(label))
        status=0
    except (WorldError,KeyError):
        status=2;body=b'';total=0
    result=HEADER.pack(2,op|(status<<8),req,view,snap,post,page,total)+body
    if len(result)>96:raise WorldError('viewer payload overflow')
    return result

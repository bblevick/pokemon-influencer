"""Host-owned recap envelope over the unchanged canonical domain schema."""
import copy, json
from pathlib import Path
from world.store import WorldError

SCHEMA_PATH=Path(__file__).resolve().parents[1]/'schemas/hermes_recap_v1.json'
SCHEMA=json.loads(SCHEMA_PATH.read_text())
RECAP_VERSION=SCHEMA['properties']['schemaVersion']['const']
HOST_FIELDS=('schemaVersion','obligationID','battleID','actorID')
PROMPT_VERSION=3

def model_result_schema():
    schema=copy.deepcopy(SCHEMA)
    schema.pop('$id',None)
    for key in HOST_FIELDS:
        schema['properties'].pop(key)
        schema['required'].remove(key)
    return schema

def build_submission(content,scope):
    """Accept content or compatible old envelopes; never trust an override."""
    if not isinstance(content,dict) or set(content)-set(SCHEMA['properties']):
        raise WorldError('invalid recap content fields')
    envelope={'schemaVersion':RECAP_VERSION,**{key:scope[key] for key in HOST_FIELDS[1:]}}
    for key,value in envelope.items():
        if key in content and (type(content[key]) is not type(value) or content[key]!=value):
            raise WorldError('conflicting host recap envelope: '+key)
    required=set(SCHEMA['required'])-set(HOST_FIELDS)
    if not required<=set(content):raise WorldError('missing recap content fields')
    return {**copy.deepcopy(content),**envelope}

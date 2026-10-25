"""Credential-free failure classification; never retain exception prose or packets."""
import json,re,time,socket,subprocess,urllib.error
from roster.hashes import digest

def failure_diagnostics(error,*,job=None,binding=None,stage='unknown',packet=None,elapsed=None):
    inherited=getattr(error,'diagnostics',None)
    if isinstance(inherited,dict):return inherited
    raw=str(error);code=raw if re.fullmatch(r'[a-z][a-z0-9_]{0,95}',raw) else 'unspecified'
    status=getattr(error,'code',None)
    if type(status)!=int:status=int(code[5:]) if re.fullmatch(r'http_\d{3}',code) else None
    if status is not None:category='rate_limit' if status==429 else 'http_rejection'
    elif isinstance(error,(TimeoutError,socket.timeout,subprocess.TimeoutExpired)) or 'deadline' in code or code=='request_timeout':category='timeout'
    elif isinstance(error,(OSError,urllib.error.URLError)) or code=='provider_transport_failure':category='transport'
    elif isinstance(error,json.JSONDecodeError) or code.startswith(('malformed_','invalid_','one_choice','incomplete_','provider_response')):category='malformed_response'
    elif stage in ('configuration','route_metadata','request_serialization'):category='preflight_rejection'
    else:category='adapter_rejection'
    scope=(packet or {}).get('scope',{})
    return {'schemaVersion':1,'jobID':job,'actor':scope.get('actor'),'campaign':scope.get('campaignID',scope.get('campaign')),'branch':scope.get('branchID',scope.get('branch')),'contextID':(packet or {}).get('contextID'),'generation':scope.get('restore_epoch',scope.get('generation')),'cutoff':scope.get('cutoff'),'scopeSHA256':digest(scope),'provider':(binding or {}).get('provider'),'model':(binding or {}).get('model'),'stage':stage,'errorClass':type(error).__name__,'code':code,'category':category,'httpStatus':status,'retryable':category in ('rate_limit','timeout','transport') or (status is not None and status>=500),'recordedAtUnix':time.time(),'latencySeconds':elapsed,'requestID':None,'requestIDAvailability':'not captured','modelInputSHA256':digest((packet or {}).get('modelInput',packet or {}))}

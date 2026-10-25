"""Mocked HTTP wire validation; no network, credentials or live requests."""
import unittest,tempfile,json,time,copy
from pathlib import Path
from unittest.mock import patch
from strategy.provider import OpenRouterProvider,Limits,ProviderError,LiveBudget
from strategy.domain import SCHEMA
class Response:
 def __init__(self,value):self.value=value
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):return json.dumps(self.value).encode()[:n]
class ProviderTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.budget=Path(self.tmp.name)/'budget.json';self.binding={'provider':'openrouter_chat','model':'fixture:free','adapterVersion':1};self.route={'checkedAtUnix':time.time(),'model':'fixture:free','providerName':'Fixture','endpoint':{'supported_parameters':[]}}
  self.value={'schemaVersion':2};self.response={'model':'fixture:free','choices':[{'message':{'tool_calls':[{'type':'function','function':{'name':'submit_strategic_posture','arguments':json.dumps(self.value)}}],'reasoning':'DO NOT PERSIST'}}],'usage':{'completion_tokens':30,'prompt_tokens':40,'total_tokens':70,'cost':0}}
  self.provider=OpenRouterProvider(self.binding,'dummy-key',self.route,self.budget,'test')
 def tearDown(self):self.tmp.cleanup()
 def test_exact_typed_wire_no_response_format(self):
  def http(req,timeout):
   body=json.loads(req.data);self.assertNotIn('response_format',body);self.assertEqual(body['tool_choice']['function']['name'],'submit_strategic_posture');self.assertEqual(len(body['tools']),1);self.assertTrue(body['provider']['allow_fallbacks']);self.assertNotIn('models',body);self.assertEqual(body['provider']['only'],['Fixture']);self.assertEqual(body['provider']['max_price'],{'prompt':0,'completion':0});return Response(self.response)
  with patch('urllib.request.urlopen',http):value,diagnostics=self.provider.structured({'fictional':True},SCHEMA,Limits())
  self.assertEqual(value,self.value);self.assertNotIn('reasoning',json.dumps(diagnostics));self.assertEqual(len(json.loads(self.budget.read_text())['attempts']),1)
 def test_verified_canonical_alias_only(self):
  self.route['catalog']={'canonical_slug':'fixture-versioned'};self.response['model']='fixture-versioned'
  with patch('urllib.request.urlopen',return_value=Response(self.response)):value,d=self.provider.structured({},SCHEMA,Limits())
  self.assertEqual(d['resolvedModel'],'fixture-versioned');self.assertEqual(d['requestedModel'],'fixture:free')
 def test_catalog_equivalent_serving_alias_preserves_free_routing(self):
  self.route['canonicalAliases']=['fixture','fixture:free'];self.response['model']='fixture'
  with patch('urllib.request.urlopen',return_value=Response(self.response)):value,d=self.provider.structured({},SCHEMA,Limits())
  self.assertEqual(d['resolvedModel'],'fixture');self.assertEqual(d['costUSD'],0)
 def test_error_envelope_normalized_without_model_substitution(self):
  response={'error':{'code':502,'message':'upstream unavailable'}}
  with patch('urllib.request.urlopen',return_value=Response(response)),self.assertRaisesRegex(ProviderError,'provider_error_502'):self.provider.structured({},SCHEMA,Limits())
  audit=json.loads(self.budget.read_text())['attempts'][0]['response'];self.assertEqual(audit['error']['code'],502);self.assertEqual(audit['keys'],['error'])
 def test_malformed_root_and_usage_fail_closed(self):
  for response in ([],{'usage':[]}):
   with patch('urllib.request.urlopen',return_value=Response(response)),self.assertRaises(ProviderError):self.provider.structured({},SCHEMA,Limits())
 def test_hard_limit_configuration(self):
  for kwargs in ({'attempts':4},{'job_seconds':121},{'output_tokens':1801},{'input_bytes':24577}):
   with self.assertRaises(ValueError):Limits(**kwargs)
 def test_reject_model_mismatch(self):
  self.response['model']='substitute'
  with patch('urllib.request.urlopen',return_value=Response(self.response)),self.assertRaises(ProviderError):self.provider.structured({},SCHEMA,Limits())
 def test_reject_cost_unknown_or_paid(self):
  for value in (None,1):
   self.response['usage']['cost']=value
   with patch('urllib.request.urlopen',return_value=Response(self.response)),self.assertRaises(ProviderError):self.provider.structured({},SCHEMA,Limits())
 def test_reject_extra_tool(self):
  self.response['choices'][0]['message']['tool_calls']*=2
  with patch('urllib.request.urlopen',return_value=Response(self.response)),self.assertRaises(ProviderError):self.provider.structured({},SCHEMA,Limits())
 def test_reject_output_tokens(self):
  self.response['usage']['completion_tokens']=99999
  with patch('urllib.request.urlopen',return_value=Response(self.response)),self.assertRaises(ProviderError):self.provider.structured({},SCHEMA,Limits())
 def test_expired_route_no_charge(self):
  self.route['checkedAtUnix']=0
  with patch('urllib.request.urlopen') as http,self.assertRaises(ProviderError):self.provider.structured({},SCHEMA,Limits())
  http.assert_not_called();self.assertFalse(self.budget.exists())
 def test_input_limit_no_charge(self):
  with patch('urllib.request.urlopen') as http,self.assertRaises(ProviderError):self.provider.structured({'oversize':'x'*25000},SCHEMA,Limits())
  http.assert_not_called();self.assertFalse(self.budget.exists())
 def test_response_limit(self):
  self.response['filler']='x'*70000
  with patch('urllib.request.urlopen',return_value=Response(self.response)),self.assertRaises(ProviderError):self.provider.structured({},SCHEMA,Limits())
 def test_transport_failure_counted(self):
  with patch('urllib.request.urlopen',side_effect=OSError('dummy')),self.assertRaises(ProviderError):self.provider.structured({},SCHEMA,Limits())
  self.assertEqual(len(json.loads(self.budget.read_text())['attempts']),1)
 def test_no_simultaneous_request(self):
  with LiveBudget(self.budget):
   with patch('urllib.request.urlopen') as http,self.assertRaises(BlockingIOError):self.provider.structured({},SCHEMA,Limits())
   http.assert_not_called()

 def test_same_model_failover_only_preflighted_providers(self):
  self.route['providerNames']=['Fixture','Second']
  def http(req,timeout):
   body=json.loads(req.data);self.assertEqual(body['model'],'fixture:free');self.assertEqual(body['provider']['only'],['Fixture','Second']);self.assertTrue(body['provider']['allow_fallbacks']);self.assertNotIn('models',body);return Response(self.response)
  with patch('urllib.request.urlopen',http):self.provider.structured({},SCHEMA,Limits())
 def test_http_502_retains_metadata_and_charge(self):
  import urllib.error
  with patch('urllib.request.urlopen',side_effect=urllib.error.HTTPError('https://fixture',502,'upstream',{},None)),self.assertRaisesRegex(ProviderError,'http_502'):self.provider.structured({},SCHEMA,Limits())
  a=json.loads(self.budget.read_text())['attempts'];self.assertEqual(len(a),1);self.assertEqual(a[0]['response']['httpStatus'],502)
 def test_success_audit_preserves_typed_submission_only(self):
  self.response['provider']='Fixture'
  with patch('urllib.request.urlopen',return_value=Response(self.response)):self.provider.structured({},SCHEMA,Limits())
  a=json.loads(self.budget.read_text())['attempts'][0];self.assertEqual(a['response']['toolSubmission']['arguments'],self.value);self.assertEqual(a['response']['servingProvider'],'Fixture');self.assertNotIn('DO NOT PERSIST',json.dumps(a));self.assertNotIn('dummy-key',json.dumps(a))

 def test_http_error_body_retained_with_credential_redaction(self):
  import urllib.error,io
  body={'error':{'message':'rate limited dummy-key','metadata':{'provider_name':'Fixture'}}}
  error=urllib.error.HTTPError('https://fixture',429,'quota',{},io.BytesIO(json.dumps(body).encode()))
  with patch('urllib.request.urlopen',side_effect=error),self.assertRaisesRegex(ProviderError,'http_429'):self.provider.structured({},SCHEMA,Limits())
  audit=json.loads(self.budget.read_text())['attempts'][0]['response'];self.assertEqual(audit['httpStatus'],429);self.assertEqual(audit['error']['providerName'],'Fixture');self.assertNotIn('dummy-key',json.dumps(audit));self.assertIn('<redacted>',audit['error']['message'])

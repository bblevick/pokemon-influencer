#!/usr/bin/env python3
"""Bounded public GET qualification; never dispatch generation or change state."""
import argparse, json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from strategy.provider import live_configuration, public_get, qualify_text_route, text_route_health

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-number', type=int, choices=(2, 3), required=True)
    args = parser.parse_args()
    output = ROOT / 'evidence/phase8/rival01-dots-renewal'
    prior = json.loads((output / f'health-check-{args.check_number - 1}.json').read_text())
    first = json.loads((output / 'health-check-1.json').read_text())
    if first.get('qualified') or not first.get('transientTransportFailure') or prior.get('qualified'):
        raise ValueError('renewal retry not authorized by preceding results')
    target = output / f'health-check-{args.check_number}.json'
    if target.exists():
        raise ValueError('refuse overwrite qualification evidence')
    model = live_configuration()[0]['model']
    if model != 'dots-studio/dots-3-note-preview:free':
        raise ValueError('configured Dots model changed')
    report = dict(authorization='8a2fb2ff-6104-4b83-94a4-253742b267a6',
                  checkedAtUnix=time.time(), model=model, generationCalls=0,
                  httpMethods=['GET'], checkNumber=args.check_number)
    try:
        catalog = public_get('https://openrouter.ai/api/v1/models')
        endpoints = public_get('https://openrouter.ai/api/v1/models/' + model + '/endpoints')
        report.update(catalogRows=[r for r in catalog['data'] if r['id'] == model],
                      endpointResponse=endpoints,
                      endpointQualification=[dict(provider=e.get('provider_name'), tag=e.get('tag'),
                          status=e.get('status'), pricing=e.get('pricing'), health=text_route_health(e),
                          supportedParameters=e.get('supported_parameters'))
                          for e in endpoints['data']['endpoints']])
        try:
            report.update(qualified=True, route=qualify_text_route(model, catalog, endpoints))
        except Exception as error:
            report.update(qualified=False, failureClass=type(error).__name__, failureCode=str(error),
                          failureCategory='endpoint_metadata_ineligible', transientTransportFailure=False)
    except Exception as error:
        report.update(qualified=False, failureClass=type(error).__name__, failureCode=str(error)[:200],
                      failureCategory='metadata_transport_or_service', transientTransportFailure=True)
    target.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:report.get(k) for k in ('checkNumber','qualified','failureCode',
        'failureCategory','endpointQualification','generationCalls')}))
    return 0 if report['qualified'] else 2

if __name__ == '__main__':
    raise SystemExit(main())

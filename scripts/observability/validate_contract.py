#!/usr/bin/env python3
"""Validate the declared stack boundary; does not certify deployed access controls."""
import json
import sys
from pathlib import Path

EXPECTED = {
    'Codestra-Prometheus', 'Codestra-Alertmanager', 'Codestra-Grafana-',
    'Codestra-Telemetry', 'Codestra-Alloy', 'Codestra-Loki', 'Codestra-Tempo',
    'Codestra-Node-Exporter', 'Codestra-cAdvisor', 'Codestra-Redis-Exporter',
    'Codestra-Blackbox-Exporter', 'Codestra-Postgres-Exporter', 'Superset',
    'Codestra-OpenBao',
}


def validate(contract):
    errors = []
    components = contract['components']
    names = [c['repository'].removeprefix('appolon1908-hue/') for c in components]
    if set(names) != EXPECTED or len(names) != len(EXPECTED):
        errors.append('Exactly the 14 approved stack repositories are required')
    for c in components:
        if not c['repository'].startswith('appolon1908-hue/'):
            errors.append('Repository owner must be appolon1908-hue')
        if c.get('odoo_business_write') is not False:
            errors.append('Monitoring, analytics and secrets components cannot write Odoo business data')
        if c.get('secret_source') != 'Codestra-OpenBao':
            errors.append('All stack components must use OpenBao for secrets')
    if contract.get('odoo_write_authority') != 'Middleware-':
        errors.append('Middleware must be the sole Odoo business write authority')
    if contract.get('analytics') != {
        'repository': 'Superset', 'data_access': 'read_only', 'source': 'business_read_model'
    }:
        errors.append('Superset must query a read-only business read model')
    if contract.get('secrets') != {
        'owner': 'Codestra-OpenBao', 'delivery': 'read_only_files',
        'odoo_credentials_consumers': ['Middleware-'],
    }:
        errors.append('Odoo credentials must be delivered only to Middleware using secret files')
    allowed = set()
    for name in EXPECTED:
        if name.endswith('Exporter') or name == 'Codestra-cAdvisor':
            allowed.add((name, 'Codestra-Prometheus', 'metrics'))
    for name in ('Codestra-Alloy', 'Codestra-Telemetry'):
        for target, signal in [('Codestra-Prometheus', 'metrics'),
                               ('Codestra-Loki', 'logs'), ('Codestra-Tempo', 'traces')]:
            allowed.add((name, target, signal))
    for name in ('Codestra-Prometheus', 'Codestra-Loki'):
        allowed.add((name, 'Codestra-Alertmanager', 'alerts'))
    allowed.update({('Codestra-Alertmanager', 'Middleware-', 'operational_events'),
                    ('Middleware-', 'Odoo', 'business_write'),
                    ('Superset', 'business_read_model', 'query')})
    for name in ('Codestra-Prometheus', 'Codestra-Loki', 'Codestra-Tempo'):
        allowed.add(('Codestra-Grafana-', name, 'query'))
    flows = [(e['source'], e['target'], e['signal']) for e in contract['flows']]
    if set(flows) != allowed or len(flows) != len(allowed):
        errors.append('Flows must match the approved signal pipeline and Middleware write boundary')
    if contract.get('schema_version') != 1:
        errors.append('Unsupported schema version')
    return errors


def main():
    default = Path(__file__).resolve().parents[2] / 'deploy/observability/stack-contract.json'
    try:
        errors = validate(json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else default).read_text()))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f'Invalid stack contract: {exc}', file=sys.stderr)
        return 1
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('Stack contract valid: 14 components; Middleware-only Odoo business writes')
    return 0


if __name__ == '__main__':
    sys.exit(main())

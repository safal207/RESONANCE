"""Run development checks and write an auditable, explicitly bounded receipt."""
import argparse
import contextlib
import hashlib
import io
import json
import platform
import unittest
from pathlib import Path

import build_demo
import integration_check
import test_paired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('results'))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent), pattern='test_*.py')
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (args.out / 'unit-tests.log').write_text(log.getvalue(), encoding='utf-8')
    if not result.wasSuccessful():
        raise SystemExit(log.getvalue())
    bridge = integration_check.check()
    payload = build_demo.build(args.out / 'paired-feedback.html')
    expected = ['SUPPORTED', 'SUPPORTED', 'SUPPORTED', 'SUPPORTED', 'UNKNOWN', 'REFUTED', 'SUPPORTED', 'CONFLICTS']
    for e, verdict in zip(payload['data'], expected, strict=True):
        final = e['snapshots'][-1]['card']
        assert final['proof']['verdict'] == verdict, e['name']
        assert not final['reply_required'] and not final['external_action_authorized']
    root = Path(__file__).resolve().parent
    source_files = sorted(root.glob('*.py'))
    source_files += sorted(integration_check.UPSTREAM.glob('*.py'))
    hashes = {str(p.relative_to(root.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    report = {'schema': 'resonance.r5p.dev-verification.v1', 'python': platform.python_version(),
              'synthetic': True, 'unit_tests_run': result.testsRun, 'unit_tests_passed': result.testsRun,
              'temporal_cases_reused': bridge['cases_reused'], 'trace_scenarios': len(payload['data']),
              'trace_endpoint_checks': len(expected), 'llm_runs': 0, 'human_participants': 0,
              'token_savings_measured': False, 'pressure_reduction_measured': False,
              'independent_reviewers': 0, 'live_connector_calls': 0,
              'boundary': 'Open developer-authored contracts; overlapping fixtures; not population accuracy or efficacy.',
              'source_sha256': hashes, 'trace_fingerprint': payload['input_fingerprint']}
    (args.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (args.out / 'temporal-bridge.json').write_text(json.dumps(bridge, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

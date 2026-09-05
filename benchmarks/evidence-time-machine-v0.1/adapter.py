"""Read-only GitHub observation -> bounded temporal evidence. Python stdlib only.

A run result is historical evidence for THAT run and commit, never merge authority.
Live capture makes GET requests only; offline replay is the default. No LLM calls.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'temporal-evidence-interim-2026-09-05'
sys.path.insert(0, str(PRIOR))
import baseline as policy
import hardening

REPO = 'safal207/RESONANCE'
SOURCE_SHA = '0bf8f4095a8048d9a2ee145d71c10c9214d72a8c'
MERGE_SHA = 'd3f79f9e192b2df3a745fa123e0d24f2be2444fa'
CHECK_ID = 101291849079
APP_ID = 15368
SCHEMA = 'resonance.github-check-observation.v1'
HEX40 = re.compile(r'^[0-9a-f]{40}$')
REPO_RE = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def exact_int(value, label):
    if type(value) is not int or value <= 0:
        raise ValueError(f'{label} must be a positive integer')
    return value


def check_sha(value):
    if not isinstance(value, str) or not HEX40.fullmatch(value):
        raise ValueError('full lowercase commit SHA required')
    return value


def context(repository, sha):
    if not isinstance(repository, str) or not REPO_RE.fullmatch(repository):
        raise ValueError('owner/repository required')
    return dict(system=repository, environment='github-actions', version=check_sha(sha), region='not-region-scoped')


def claim(check_id):
    return f'github.check_run_passed:{exact_int(check_id,"check id")}'


def normalize(observation: dict) -> dict:
    """Pure normalization. Trust rests on the supplied observation, not this JSON.

    Source event time and local availability time stay distinct. Unexpected or
    incomplete conclusions yield no Boolean assertion; missing data is not failure.
    Context remains exact. This does not infer a repository's required-check policy.
    """
    if observation.get('schema') != SCHEMA:
        raise ValueError('unsupported observation schema')
    repository = observation.get('repository')
    context(repository, SOURCE_SHA)
    known = policy.timestamp(observation['recorded_at'])
    rows = observation.get('check_runs')
    if not isinstance(rows, list):
        raise ValueError('check_runs must be a list')
    ids, records = set(), []
    for row in rows:
        rid = exact_int(row.get('id'), 'check id')
        if rid in ids:
            raise ValueError('duplicate check id: preserve observations separately')
        ids.add(rid)
        app_id = exact_int(row.get('app', {}).get('id'), 'app id')
        sha = check_sha(row.get('head_sha'))
        if not isinstance(row.get('name'), str) or not row['name']:
            raise ValueError('check name required')
        link = row.get('html_url', '')
        parsed = urlsplit(link)
        if parsed.scheme != 'https' or parsed.netloc != 'github.com' or not parsed.path.startswith('/'+repository+'/') or parsed.username or parsed.password:
            raise ValueError('check URL must point into the declared repository')
        start = row.get('started_at')
        end = row.get('completed_at')
        if start is None:
            raise ValueError('source started_at required for this adapter')
        start_dt = policy.timestamp(start)
        end_dt = policy.timestamp(end) if end else None
        if start_dt > known or (end_dt and (end_dt < start_dt or end_dt > known)):
            raise ValueError('impossible observation chronology')
        status = row.get('status')
        if status not in {'queued','in_progress','requested','waiting','pending','completed'}:
            raise ValueError('unknown check status')
        if status == 'completed' and end is None:
            raise ValueError('completed check requires completed_at')
        if status != 'completed' and (end is not None or row.get('conclusion') is not None):
            raise ValueError('noncompleted check cannot carry a final result')
        conclusion = row.get('conclusion')
        if status == 'completed' and conclusion not in {'action_required','cancelled','failure','neutral','success','skipped','stale','timed_out','startup_failure'}:
            raise ValueError('unknown completed conclusion')
        r = dict(id=f'github-check-{rid}', kind='event', source_id=f'github-app:{app_id}',
                 origin_id=f'github-check-run:{rid}', derived_from=[], event_at=end or start,
                 known_at=observation['recorded_at'], valid_from=end or start, valid_until=None,
                 context=context(repository,sha), source_url=link, source_name=row['name'])
        if status == 'completed' and conclusion in {'success','failure'}:
            r.update(kind='assertion', claim=claim(rid), value=(conclusion=='success'))
        records.append(r)
    episode = dict(episode_id='github-observation', synthetic=False,
                   task='Evaluate only the specified historical check-run result for the exact commit and information cutoff. Never authorize a merge or release.',
                   policy=dict(accepted_sources=[f'github-app:{APP_ID}'], retraction_authorities=[],
                               dependency_rule='All derivation parents must remain usable; this policy does not authenticate source JSON.'),
                   records=records, checkpoints=[])
    return episode


def checkpoint(observation: dict, *, sha=SOURCE_SHA, check_id=CHECK_ID, known_at=None, valid_at=None, repository=REPO) -> dict:
    when = observation['recorded_at']
    return dict(id='query', known_at=known_at or when, valid_at=valid_at or when,
                context=context(repository,sha), query_type='claim', claim=claim(check_id))


def replay(observation: dict, cp: dict) -> dict:
    e=normalize(observation)
    e['checkpoints']=[copy.deepcopy(cp)]
    policy.validate_episode(e)
    result=hardening.evaluate(e,cp)
    result['action_authorized']=False
    result['evidence_kind']='connector-observation; source truth not independently attested'
    return result


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def capture_live(repository: str, sha: str, check_id: int | None = None) -> dict:
    """Capture public GitHub checks, using an optional read token in memory only.

    Bounded pagination; GET only; credentials are not written to disk or logs.
    Snapshots are not atomic across pages. Collection completeness is recorded.
    The offline fixture was obtained using the connected GitHub tool, not this path.
    """
    context(repository,sha)
    if check_id is not None: exact_int(check_id,'check id')
    token=os.environ.get('GITHUB_TOKEN')
    headers={'Accept':'application/vnd.github+json','User-Agent':'RESONANCE-readonly-evidence-demo','X-GitHub-Api-Version':'2022-11-28'}
    if token: headers['Authorization']='Bearer '+token
    opener=build_opener(NoRedirect())
    all_rows=[]; total=None; endpoints=[]; complete=False
    for page in range(1,101):
        endpoint=f'https://api.github.com/repos/{repository}/commits/{sha}/check-runs?filter=all&per_page=100&page={page}'
        endpoints.append(endpoint)
        with opener.open(Request(endpoint,headers=headers,method='GET'),timeout=25) as response:
            raw=response.read(8_000_001)
            if len(raw)>8_000_000: raise ValueError('response exceeds capture limit')
            data=json.loads(raw)
        total=data.get('total_count')
        rows=data.get('check_runs')
        if type(total) is not int or total<0 or not isinstance(rows,list): raise ValueError('invalid GitHub response')
        all_rows.extend(rows)
        if len(rows)<100:
            complete=(len(all_rows)==total)
            break
    if not complete: raise ValueError('incomplete or changing paginated source: retry as a new observation')
    selected=[r for r in all_rows if check_id is None or r.get('id')==check_id]
    if check_id is not None and not selected: raise ValueError('requested check not present in the collected response')
    result=dict(schema=SCHEMA, repository=repository, recorded_at=utc_now(),
                transport='stdlib HTTPS GET, full GitHub selected check objects',source_endpoint=endpoints[0],
                source_endpoints=endpoints,observed_total_count=total,collection_complete=check_id is None,
                selection='All collected runs' if check_id is None else f'Check id {check_id} selected; other runs intentionally omitted.',
                check_runs=selected,boundary='Read-only source observation; not atomic across pages, not a signature, not release authority.')
    normalize(result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['replay','capture'])
    parser.add_argument('--input',type=Path,default=HERE/'source_observation.json')
    parser.add_argument('--out',type=Path)
    parser.add_argument('--repo',default=REPO)
    parser.add_argument('--sha',default=SOURCE_SHA)
    parser.add_argument('--check-id',type=int,default=CHECK_ID)
    args=parser.parse_args()
    try:
        if args.command=='capture':
            if not args.out: parser.error('capture needs --out; never overwrite the fixture implicitly')
            result=capture_live(args.repo,args.sha,args.check_id)
        else:
            observation=json.loads(args.input.read_text())
            result=replay(observation,checkpoint(observation,sha=args.sha,check_id=args.check_id,repository=args.repo))
        text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if args.out: args.out.write_text(text,encoding='utf8')
        else: print(text,end='')
    except (ValueError,KeyError,OSError,HTTPError,URLError) as exc:
        # No request headers or tokens in error output.
        print(f'Capture/replay failed: {type(exc).__name__}: {str(exc)[:200]}',file=sys.stderr)
        raise SystemExit(2)

if __name__=='__main__': main()

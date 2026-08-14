#!/usr/bin/env python3
"""Validate the Neo Resonance repository manifest.

The structural check is offline and deterministic. Remote head checks are
optional and fail closed when requested: a changed head is HOLD, while an
unavailable remote check is INCOMPLETE.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_REPOSITORY_KEYS = {"id", "full_name", "role", "default_branch", "observed_head"}
REQUIRED_EDGE_KEYS = {"from", "to", "contract", "evidence", "status", "claim_limit"}
REQUIRED_CONTROL_PLANE_KEYS = {
    "repository",
    "default_branch",
    "observed_head",
    "role",
    "in_primary_proof_route",
    "semantic_authority",
    "current_system_007_execution",
    "claim_limit",
}
VALIDATION_SCHEMA = "neo.resonance.manifest-validation.v0.1"


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("manifest root must be an object")
    return value


def structural_errors(manifest: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema") != "neo.resonance.system-manifest.v0.1":
        errors.append("unexpected schema")
    if manifest.get("manifest_status") != "OBSERVED_SNAPSHOT":
        errors.append("manifest_status must be OBSERVED_SNAPSHOT")

    repositories = manifest.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        errors.append("repositories must be a non-empty list")
        repositories = []

    repository_ids: set[str] = set()
    repository_names: set[str] = set()
    for index, repository in enumerate(repositories):
        if not isinstance(repository, dict):
            errors.append(f"repositories[{index}] must be an object")
            continue
        missing = REQUIRED_REPOSITORY_KEYS - repository.keys()
        if missing:
            errors.append(f"repositories[{index}] missing: {sorted(missing)}")
        repo_id = repository.get("id")
        full_name = repository.get("full_name")
        roles = repository.get("role")
        if not isinstance(repo_id, str) or not repo_id:
            errors.append(f"repositories[{index}].id must be non-empty")
        elif repo_id in repository_ids:
            errors.append(f"duplicate repository id: {repo_id}")
        else:
            repository_ids.add(repo_id)
        if not isinstance(full_name, str) or not full_name.count("/") == 1:
            errors.append(f"repositories[{index}].full_name must be owner/name")
        elif full_name in repository_names:
            errors.append(f"duplicate repository full_name: {full_name}")
        else:
            repository_names.add(full_name)
        if not isinstance(roles, list) or not roles or not all(isinstance(item, str) for item in roles):
            errors.append(f"repositories[{index}].role must be a non-empty string list")
        if not isinstance(repository.get("default_branch"), str) or not repository.get("default_branch"):
            errors.append(f"repositories[{index}].default_branch must be non-empty")
        if not isinstance(repository.get("observed_head"), str) or not SHA_RE.fullmatch(repository["observed_head"]):
            errors.append(f"repositories[{index}].observed_head must be a 40-character lowercase SHA")

    edges = manifest.get("edges")
    if not isinstance(edges, list):
        errors.append("edges must be a list")
        edges = []
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edges[{index}] must be an object")
            continue
        missing = REQUIRED_EDGE_KEYS - edge.keys()
        if missing:
            errors.append(f"edges[{index}] missing: {sorted(missing)}")
        if edge.get("from") not in repository_ids:
            errors.append(f"edges[{index}].from is not a known repository id")
        if edge.get("to") not in repository_ids:
            errors.append(f"edges[{index}].to is not a known repository id")
        if not isinstance(edge.get("claim_limit"), str) or not edge["claim_limit"]:
            errors.append(f"edges[{index}].claim_limit must be explicit")

    control_planes = manifest.get("adjacent_control_planes", [])
    if not isinstance(control_planes, list):
        errors.append("adjacent_control_planes must be a list")
        control_planes = []
    for index, control_plane in enumerate(control_planes):
        if not isinstance(control_plane, dict):
            errors.append(f"adjacent_control_planes[{index}] must be an object")
            continue
        missing = REQUIRED_CONTROL_PLANE_KEYS - control_plane.keys()
        if missing:
            errors.append(f"adjacent_control_planes[{index}] missing: {sorted(missing)}")
        if not isinstance(control_plane.get("repository"), str) or control_plane["repository"].count("/") != 1:
            errors.append(f"adjacent_control_planes[{index}].repository must be owner/name")
        if not isinstance(control_plane.get("observed_head"), str) or not SHA_RE.fullmatch(control_plane["observed_head"]):
            errors.append(f"adjacent_control_planes[{index}].observed_head must be a 40-character lowercase SHA")
        if control_plane.get("in_primary_proof_route") is not False:
            errors.append(f"adjacent_control_planes[{index}] must be outside the primary proof route")
        if not isinstance(control_plane.get("claim_limit"), str) or not control_plane["claim_limit"]:
            errors.append(f"adjacent_control_planes[{index}].claim_limit must be explicit")

    next_transition = manifest.get("next_transition")
    if not isinstance(next_transition, dict):
        errors.append("next_transition must be an object")
    else:
        for key in ("id", "action_class", "action", "completion_signal", "stop_condition"):
            if not isinstance(next_transition.get(key), str) or not next_transition[key]:
                errors.append(f"next_transition.{key} must be explicit")

    return errors


def fetch_default_head(full_name: str, branch: str) -> str:
    url = f"https://api.github.com/repos/{full_name}/commits/{branch}"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "neo-resonance-manifest-validator/0.1",
        },
    )
    with urlopen(request, timeout=15) as response:
        payload = json.load(response)
    sha = payload.get("sha")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise ValueError(f"remote response for {full_name} did not contain a valid SHA")
    return sha


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def check_remote_heads(
    manifest: dict,
    fetcher: Callable[[str, str], str] = fetch_default_head,
) -> tuple[str, list[dict[str, str]]]:
    """Return a fail-closed status and one addressable result per repository."""

    records: list[dict[str, str]] = []
    moved = False
    incomplete = False
    for repository in manifest["repositories"]:
        name = repository["full_name"]
        expected = repository["observed_head"]
        record = {
            "id": repository["id"],
            "full_name": name,
            "branch": repository["default_branch"],
            "expected_head": expected,
        }
        try:
            current = fetcher(name, repository["default_branch"])
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            record.update({"status": "INCOMPLETE", "error": str(exc)})
            incomplete = True
        else:
            record["current_head"] = current
            if current != expected:
                record["status"] = "HOLD"
                moved = True
            else:
                record["status"] = "PASS"
        records.append(record)

    if incomplete:
        return "INCOMPLETE", records
    if moved:
        return "HOLD", records
    return "PASS", records


def write_report(path: Path | None, report: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_report(
    manifest_path: Path,
    structure_status: str,
    structure_errors: list[str],
    remote_requested: bool,
    remote_required: bool,
    remote_status: str,
    remote_records: list[dict[str, str]],
    exit_code: int,
) -> dict:
    return {
        "schema": VALIDATION_SCHEMA,
        "checked_at": utc_now(),
        "manifest": {
            "path": str(manifest_path),
            "sha256": sha256_file(manifest_path),
        },
        "structure": {
            "status": structure_status,
            "errors": structure_errors,
        },
        "remote": {
            "requested": remote_requested,
            "required": remote_required,
            "status": remote_status,
            "repositories": remote_records,
        },
        "exit_code": exit_code,
        "authority": "advisory only; this report does not authorize merge, deployment, production, or external effects",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--check-remote",
        action="store_true",
        help="compare every observed_head with the current remote default branch",
    )
    parser.add_argument(
        "--require-remote",
        action="store_true",
        help="return INCOMPLETE when the remote check is not executed or unavailable",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="write a machine-readable validation report to this path",
    )
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"STRUCTURE INCOMPLETE: {exc}")
        write_report(
            args.json_output,
            build_report(
                args.manifest,
                "INCOMPLETE",
                [str(exc)],
                args.check_remote,
                args.require_remote,
                "NOT_RUN",
                [],
                3,
            ),
        )
        return 3

    errors = structural_errors(manifest)
    if errors:
        print("STRUCTURE INCOMPLETE")
        for error in errors:
            print(f"- {error}")
        write_report(
            args.json_output,
            build_report(
                args.manifest,
                "INCOMPLETE",
                errors,
                args.check_remote,
                args.require_remote,
                "NOT_RUN",
                [],
                3,
            ),
        )
        return 3
    print("STRUCTURE PASS")

    if not args.check_remote:
        print("REMOTE NOT_RUN")
        exit_code = 3 if args.require_remote else 0
        write_report(
            args.json_output,
            build_report(
                args.manifest,
                "PASS",
                [],
                False,
                args.require_remote,
                "NOT_RUN",
                [],
                exit_code,
            ),
        )
        return exit_code

    remote_status, remote_records = check_remote_heads(manifest)
    if remote_status == "INCOMPLETE":
        print("REMOTE INCOMPLETE")
        for record in remote_records:
            if record["status"] == "INCOMPLETE":
                print(f"- {record['full_name']}: {record['error']}")
        write_report(
            args.json_output,
            build_report(
                args.manifest,
                "PASS",
                [],
                True,
                args.require_remote,
                remote_status,
                remote_records,
                3,
            ),
        )
        return 3
    if remote_status == "HOLD":
        print("REMOTE HOLD")
        for record in remote_records:
            if record["status"] == "HOLD":
                print(
                    f"- {record['full_name']}: observed {record['expected_head']} "
                    f"current {record['current_head']}"
                )
        write_report(
            args.json_output,
            build_report(
                args.manifest,
                "PASS",
                [],
                True,
                args.require_remote,
                remote_status,
                remote_records,
                2,
            ),
        )
        return 2
    print("REMOTE PASS")
    write_report(
        args.json_output,
        build_report(
            args.manifest,
            "PASS",
            [],
            True,
            args.require_remote,
            remote_status,
            remote_records,
            0,
        ),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

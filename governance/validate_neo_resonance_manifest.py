#!/usr/bin/env python3
"""Validate the Neo Resonance repository manifest.

The structural check is offline and deterministic. Remote head checks are
optional and fail closed when requested: a changed head is HOLD, while an
unavailable remote check is INCOMPLETE.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_REPOSITORY_KEYS = {"id", "full_name", "role", "default_branch", "observed_head"}
REQUIRED_EDGE_KEYS = {"from", "to", "contract", "evidence", "status", "claim_limit"}


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
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"STRUCTURE INCOMPLETE: {exc}")
        return 3

    errors = structural_errors(manifest)
    if errors:
        print("STRUCTURE INCOMPLETE")
        for error in errors:
            print(f"- {error}")
        return 3
    print("STRUCTURE PASS")

    if not args.check_remote:
        print("REMOTE NOT_RUN")
        return 3 if args.require_remote else 0

    remote_errors: list[str] = []
    moved: list[str] = []
    for repository in manifest["repositories"]:
        name = repository["full_name"]
        try:
            current = fetch_default_head(name, repository["default_branch"])
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            remote_errors.append(f"{name}: {exc}")
            continue
        if current != repository["observed_head"]:
            moved.append(
                f"{name}: observed {repository['observed_head']} current {current}"
            )

    if remote_errors:
        print("REMOTE INCOMPLETE")
        for error in remote_errors:
            print(f"- {error}")
        return 3
    if moved:
        print("REMOTE HOLD")
        for item in moved:
            print(f"- {item}")
        return 2
    print("REMOTE PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

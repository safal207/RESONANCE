#!/usr/bin/env python3
"""Process-crash fault injection for Recovery Integrity v0.1.

This harness uses a real SQLite authority store plus an atomically replaced JSON
projection. A child process is terminated with os._exit() at selected boundaries,
then a fresh verifier process observes the on-disk state and emits a
RecoveryIntegrityRecord-compatible verdict.

This is process-crash fault injection, not a claim of full power-loss semantics
for storage hardware or filesystems.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from validate import validate

CRASH_EXIT = 91
CRASH_POINTS = (
    "before_authority_commit",
    "after_authority_commit",
    "after_projection_temp_fsync",
    "after_projection_commit",
)

EXPECTED = {
    "before_authority_commit": (1, 1, "HEALTHY", "NO_REBUILD", False),
    "after_authority_commit": (2, 1, "STALE", "ALLOW_REBUILD", False),
    "after_projection_temp_fsync": (2, 1, "STALE", "ALLOW_REBUILD", True),
    "after_projection_commit": (2, 2, "HEALTHY", "NO_REBUILD", False),
}


def digest_payload(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fsync_dir(path: Path) -> None:
    """Persist directory metadata where Python exposes a portable-enough fd path."""
    if os.name == "nt":
        # Windows does not support opening directories with os.open in the same
        # way. The harness remains useful there but makes no directory-fsync claim.
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_projection_atomic(
    root: Path,
    generation: int,
    payload: str,
    crash_point: str | None = None,
) -> None:
    projection = root / "projection.json"
    temp = root / "projection.json.tmp"
    data = {
        "generation": generation,
        "payload": payload,
        "payload_sha256": digest_payload(payload),
    }

    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())

    if crash_point == "after_projection_temp_fsync":
        os._exit(CRASH_EXIT)

    os.replace(temp, projection)
    fsync_dir(root)


def initialize(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    db = root / "authority.sqlite3"
    connection = sqlite3.connect(db)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS authority_state (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                generation INTEGER NOT NULL,
                payload TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL
            )
            """
        )
        payload = "baseline"
        connection.execute(
            """
            INSERT OR REPLACE INTO authority_state
                (id, generation, payload, payload_sha256)
            VALUES (1, ?, ?, ?)
            """,
            (1, payload, digest_payload(payload)),
        )
        connection.commit()
    finally:
        connection.close()

    write_projection_atomic(root, 1, "baseline")


def child_mutate(root: Path, crash_point: str) -> None:
    """Advance authority/projection from generation 1 to 2 and crash on cue."""
    connection = sqlite3.connect(root / "authority.sqlite3")
    try:
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("BEGIN IMMEDIATE")
        payload = "next"
        connection.execute(
            """
            UPDATE authority_state
               SET generation = ?, payload = ?, payload_sha256 = ?
             WHERE id = 1
            """,
            (2, payload, digest_payload(payload)),
        )

        if crash_point == "before_authority_commit":
            os._exit(CRASH_EXIT)

        connection.commit()
    finally:
        connection.close()

    if crash_point == "after_authority_commit":
        os._exit(CRASH_EXIT)

    write_projection_atomic(root, 2, "next", crash_point=crash_point)

    if crash_point == "after_projection_commit":
        os._exit(CRASH_EXIT)


def read_authority(root: Path) -> dict:
    connection = sqlite3.connect(root / "authority.sqlite3")
    try:
        row = connection.execute(
            "SELECT generation, payload, payload_sha256 FROM authority_state WHERE id = 1"
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise RuntimeError("authority row missing")
    generation, payload, digest = row
    return {
        "generation": generation,
        "payload": payload,
        "payload_sha256": digest,
    }


def read_projection(root: Path) -> tuple[dict | None, str | None]:
    path = root / "projection.json"
    if not path.exists():
        return None, None
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # pragma: no cover - exercised by future corrupt fixtures
        return None, f"{type(exc).__name__}: {exc}"


def classify(authority: dict, projection: dict | None, projection_error: str | None) -> tuple[str, str]:
    if projection_error:
        return "CORRUPT", "ALLOW_REBUILD"
    if projection is None:
        return "MISSING", "ALLOW_REBUILD"

    authority_generation = authority["generation"]
    projection_generation = projection.get("generation")
    if projection_generation == authority_generation:
        return "HEALTHY", "NO_REBUILD"
    if isinstance(projection_generation, int) and projection_generation < authority_generation:
        return "STALE", "ALLOW_REBUILD"
    return "UNPROVABLE", "HOLD"


def observe(root: Path, crash_point: str) -> dict:
    authority = read_authority(root)
    projection, projection_error = read_projection(root)
    projection_state, rebuild = classify(authority, projection, projection_error)
    temp_path = root / "projection.json.tmp"

    preserved_ref = None
    if projection_state in {"STALE", "CORRUPT"}:
        # No repair is performed. The disputed original remains addressable in place.
        preserved_ref = str(root / "projection.json")

    record = {
        "protocol_version": "recovery-integrity-v0.1",
        "recovery_id": f"process-crash-{crash_point}",
        "source_case_ref": f"local://process-crash/{crash_point}",
        "authority": {
            "source_ref": str(root / "authority.sqlite3"),
            "generation": authority["generation"],
            "integrity": "VALID",
        },
        "projection": {
            "source_ref": str(root / "projection.json"),
            "generation": None if projection is None else projection.get("generation"),
            "state": projection_state,
            "preserved_broken_ref": preserved_ref,
        },
        "rollout": {
            "source_ref": None,
            "integrity": "UNKNOWN",
            "continuation_proof": "NOT_PROVEN",
        },
        "last_committed_action_ref": None,
        "pending_action_ref": None,
        "external_side_effect_state": "UNKNOWN",
        "current_authority_proof": "NOT_PROVEN",
        "decision": {
            "rebuild_projection": rebuild,
            "execution_continuation": "HOLD",
        },
        "evidence_refs": [
            f"authority_generation={authority['generation']}",
            f"projection_generation={None if projection is None else projection.get('generation')}",
            f"projection_temp_present={temp_path.exists()}",
            f"projection_parse_error={projection_error}",
        ],
        "verifier": {
            "verifier_id": "recovery-integrity-process-crash-harness-v0.1",
            "mode": "read-only",
        },
        "pre_recovery_snapshot_ref": str(root),
        "post_recovery_snapshot_ref": None,
        "observed_outcome": {
            "status": "HELD",
            "outcome_ref": "classification-only; no rebuild or continuation executed",
        },
    }

    return {
        "record": record,
        "authority_payload_sha256": authority["payload_sha256"],
        "projection_payload_sha256": None if projection is None else projection.get("payload_sha256"),
        "temp_projection_present": temp_path.exists(),
        "validation_errors": validate(record),
    }


def run_one(crash_point: str, root: Path) -> dict:
    initialize(root)
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "child-mutate",
        str(root),
        "--crash-point",
        crash_point,
    ]
    result = subprocess.run(command, check=False)
    if result.returncode != CRASH_EXIT:
        raise RuntimeError(
            f"{crash_point}: expected child exit {CRASH_EXIT}, got {result.returncode}"
        )
    return observe(root, crash_point)


def assert_expected(crash_point: str, observed: dict) -> None:
    expected_authority, expected_projection, expected_state, expected_rebuild, expected_temp = EXPECTED[crash_point]
    record = observed["record"]
    actual = (
        record["authority"]["generation"],
        record["projection"]["generation"],
        record["projection"]["state"],
        record["decision"]["rebuild_projection"],
        observed["temp_projection_present"],
    )
    expected = (
        expected_authority,
        expected_projection,
        expected_state,
        expected_rebuild,
        expected_temp,
    )
    if actual != expected:
        raise AssertionError(f"{crash_point}: expected {expected}, got {actual}")
    if observed["validation_errors"]:
        raise AssertionError(
            f"{crash_point}: semantic validator errors: {observed['validation_errors']}"
        )


def run_matrix() -> int:
    print("crash_point                         auth proj projection rebuild          temp validator")
    print("---------------------------------------------------------------------------------------")
    with tempfile.TemporaryDirectory(prefix="recovery-integrity-fi-") as temp_root:
        base = Path(temp_root)
        for crash_point in CRASH_POINTS:
            observed = run_one(crash_point, base / crash_point)
            assert_expected(crash_point, observed)
            record = observed["record"]
            print(
                f"{crash_point:<35} "
                f"{record['authority']['generation']!s:<4} "
                f"{record['projection']['generation']!s:<4} "
                f"{record['projection']['state']:<10} "
                f"{record['decision']['rebuild_projection']:<16} "
                f"{str(observed['temp_projection_present']):<5} PASS"
            )
    print("PASS process-crash fault-injection matrix 4/4")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("matrix")

    child = sub.add_parser("child-mutate")
    child.add_argument("root")
    child.add_argument("--crash-point", required=True, choices=CRASH_POINTS)

    args = parser.parse_args()
    if args.command in {None, "matrix"}:
        return run_matrix()
    if args.command == "child-mutate":
        child_mutate(Path(args.root), args.crash_point)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())

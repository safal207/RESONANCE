from __future__ import annotations

import argparse
import json
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

INITIAL_VERSION = 100
OPERATION_ID = "op-1"


@dataclass
class WorkerOutcome:
    node: str
    observed_state: str
    observed_version: int
    transition: str
    returned_state: str | None
    returned_version: int | None
    reconciled_state: str | None
    reconciled_version: int | None
    reconciled_effects: int | None
    duration_seconds: float


def db_connect(dsn: str):
    return psycopg.connect(dsn, autocommit=False)


def init_schema(dsn: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS operations (
                    id text PRIMARY KEY,
                    state text NOT NULL,
                    version integer NOT NULL,
                    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS effects (
                    id bigserial PRIMARY KEY,
                    operation_id text NOT NULL,
                    node text NOT NULL,
                    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
                )
                """
            )
        conn.commit()


def reset_world(dsn: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE effects RESTART IDENTITY")
            cur.execute("DELETE FROM operations")
            cur.execute(
                "INSERT INTO operations(id, state, version) VALUES (%s, 'absent', %s)",
                (OPERATION_ID, INITIAL_VERSION),
            )
        conn.commit()


def read_state(conn) -> tuple[str, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT state, version FROM operations WHERE id=%s", (OPERATION_ID,))
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("operation row missing")
        return str(row[0]), int(row[1])


def count_effects(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM effects WHERE operation_id=%s", (OPERATION_ID,))
        return int(cur.fetchone()[0])


def unsafe_worker(dsn: str, node: str, barrier: threading.Barrier, sink: list[WorkerOutcome], lock: threading.Lock) -> None:
    started = time.monotonic()
    conn = db_connect(dsn)
    try:
        state, version = read_state(conn)
        conn.commit()
        barrier.wait(timeout=10)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE operations SET state='committed', version=version+1, updated_at=clock_timestamp() WHERE id=%s RETURNING state, version",
                (OPERATION_ID,),
            )
            row = cur.fetchone()
            cur.execute("INSERT INTO effects(operation_id, node) VALUES (%s, %s)", (OPERATION_ID, node))
        conn.commit()
        outcome = WorkerOutcome(
            node=node,
            observed_state=state,
            observed_version=version,
            transition="unconditional_commit",
            returned_state=str(row[0]),
            returned_version=int(row[1]),
            reconciled_state=None,
            reconciled_version=None,
            reconciled_effects=None,
            duration_seconds=round(time.monotonic() - started, 6),
        )
        with lock:
            sink.append(outcome)
    finally:
        conn.close()


def safe_worker(dsn: str, node: str, barrier: threading.Barrier, sink: list[WorkerOutcome], lock: threading.Lock) -> None:
    started = time.monotonic()
    conn = db_connect(dsn)
    try:
        state, version = read_state(conn)
        conn.commit()
        barrier.wait(timeout=10)

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE operations
                SET state='committed', version=version+1, updated_at=clock_timestamp()
                WHERE id=%s AND state='absent' AND version=%s
                RETURNING state, version
                """,
                (OPERATION_ID, version),
            )
            row = cur.fetchone()
            if row is not None:
                cur.execute("INSERT INTO effects(operation_id, node) VALUES (%s, %s)", (OPERATION_ID, node))
                conn.commit()
                outcome = WorkerOutcome(
                    node=node,
                    observed_state=state,
                    observed_version=version,
                    transition="commit_winner",
                    returned_state=str(row[0]),
                    returned_version=int(row[1]),
                    reconciled_state=None,
                    reconciled_version=None,
                    reconciled_effects=None,
                    duration_seconds=round(time.monotonic() - started, 6),
                )
            else:
                conn.rollback()
                reconciled_state, reconciled_version = read_state(conn)
                reconciled_effects = count_effects(conn)
                conn.commit()
                outcome = WorkerOutcome(
                    node=node,
                    observed_state=state,
                    observed_version=version,
                    transition="precondition_failed",
                    returned_state=None,
                    returned_version=None,
                    reconciled_state=reconciled_state,
                    reconciled_version=reconciled_version,
                    reconciled_effects=reconciled_effects,
                    duration_seconds=round(time.monotonic() - started, 6),
                )
        with lock:
            sink.append(outcome)
    finally:
        conn.close()


def run_pair(dsn: str, mode: str) -> dict[str, Any]:
    reset_world(dsn)
    outcomes: list[WorkerOutcome] = []
    sink_lock = threading.Lock()
    barrier = threading.Barrier(2)
    worker = unsafe_worker if mode == "unsafe" else safe_worker
    threads = [
        threading.Thread(target=worker, args=(dsn, node, barrier, outcomes, sink_lock), daemon=True)
        for node in ("A", "B")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    if any(thread.is_alive() for thread in threads):
        raise RuntimeError(f"{mode} worker did not finish")
    if len(outcomes) != 2:
        raise RuntimeError(f"{mode} expected two worker outcomes, got {len(outcomes)}")

    with db_connect(dsn) as conn:
        final_state, final_version = read_state(conn)
        effects = count_effects(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT node FROM effects WHERE operation_id=%s ORDER BY id", (OPERATION_ID,))
            effect_nodes = [str(row[0]) for row in cur.fetchall()]
        conn.commit()

    return {
        "mode": mode,
        "workers": [outcome.__dict__ for outcome in sorted(outcomes, key=lambda x: x.node)],
        "final_state": final_state,
        "final_version": final_version,
        "effect_count": effects,
        "effect_nodes": effect_nodes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    parser.add_argument("--out", default="benchmark-results/postgresql-transactional-trust-adapter-v1.0")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    init_schema(args.dsn)
    with db_connect(args.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW server_version")
            server_version = str(cur.fetchone()[0])
            cur.execute("SHOW server_version_num")
            server_version_num = int(cur.fetchone()[0])
        conn.commit()

    unsafe = run_pair(args.dsn, "unsafe")
    safe = run_pair(args.dsn, "safe")

    safe_transitions = sorted(worker["transition"] for worker in safe["workers"])
    stale_worker = next((w for w in safe["workers"] if w["transition"] == "precondition_failed"), None)
    winner = next((w for w in safe["workers"] if w["transition"] == "commit_winner"), None)

    checks = [
        {
            "id": "real_postgresql_service_observed",
            "points": 2,
            "pass": bool(server_version and server_version_num > 0),
            "evidence": {"server_version": server_version, "server_version_num": server_version_num},
        },
        {
            "id": "unsafe_two_connection_duplicate_reproduced",
            "points": 2,
            "pass": unsafe["effect_count"] == 2 and unsafe["final_version"] == 102,
            "evidence": unsafe,
        },
        {
            "id": "conditional_update_allows_single_winner",
            "points": 2,
            "pass": safe["effect_count"] == 1 and safe_transitions == ["commit_winner", "precondition_failed"],
            "evidence": {"effect_count": safe["effect_count"], "transitions": safe_transitions, "winner": winner},
        },
        {
            "id": "stale_writer_reconciles_committed_state",
            "points": 2,
            "pass": bool(stale_worker and stale_worker["reconciled_state"] == "committed" and stale_worker["reconciled_version"] == 101 and stale_worker["reconciled_effects"] == 1),
            "evidence": stale_worker,
        },
        {
            "id": "final_database_invariant_proved",
            "points": 2,
            "pass": safe["final_state"] == "committed" and safe["final_version"] == 101 and safe["effect_count"] == 1,
            "evidence": {"final_state": safe["final_state"], "final_version": safe["final_version"], "effect_count": safe["effect_count"], "effect_nodes": safe["effect_nodes"]},
        },
    ]
    score = sum(item["points"] for item in checks if item["pass"])

    result = {
        "benchmark": "RESONANCE PostgreSQL Transactional Trust Adapter",
        "benchmark_version": "1.0",
        "protocol": "RESONANCE Transactional Trust Protocol v1.0",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "database": {"server_version": server_version, "server_version_num": server_version_num},
        "score": score,
        "max_score": 10,
        "classification": "PostgreSQL atomic state-version adapter passes" if score == 10 else "PostgreSQL adapter requires review",
        "unsafe": unsafe,
        "safe": safe,
        "checks": checks,
        "invariant": "Two independent readers may observe the same legal snapshot, but at most one version-bound mutation may commit an effect.",
        "scope": "Real PostgreSQL service container and two independent client connections; local synthetic operation/effects tables only.",
        "external_safety_certification": False,
    }

    (out_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = [
        "# PostgreSQL Transactional Trust Adapter v1.0",
        "",
        f"**Score:** {score}/10",
        f"**PostgreSQL:** {server_version}",
        f"**Unsafe effects:** {unsafe['effect_count']}",
        f"**Safe effects:** {safe['effect_count']}",
        f"**Safe final state:** {safe['final_state']} / version {safe['final_version']}",
        f"**Safe worker transitions:** {', '.join(safe_transitions)}",
    ]
    (out_dir / "RESULT.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))

    if score != 10:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

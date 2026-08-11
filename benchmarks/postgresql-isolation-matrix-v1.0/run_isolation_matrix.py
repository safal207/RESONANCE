from __future__ import annotations

import argparse
import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg
from psycopg.errors import SerializationFailure

INITIAL_VERSION = 100
OPERATION_ID = "op-1"
LEVELS = {
    "read_committed": "READ COMMITTED",
    "repeatable_read": "REPEATABLE READ",
    "serializable": "SERIALIZABLE",
}


@dataclass
class WorkerOutcome:
    node: str
    isolation: str
    observed_state: str
    observed_version: int
    transition: str
    sqlstate: str | None
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
                    isolation_level text NOT NULL,
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


def set_isolation(conn, isolation_sql: str) -> None:
    with conn.cursor() as cur:
        cur.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_sql}")


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


def reconcile_fresh(dsn: str) -> tuple[str, int, int]:
    with db_connect(dsn) as conn:
        state, version = read_state(conn)
        effects = count_effects(conn)
        conn.commit()
        return state, version, effects


def unsafe_worker(dsn: str, node: str, barrier: threading.Barrier, sink: list[WorkerOutcome], lock: threading.Lock) -> None:
    started = time.monotonic()
    conn = db_connect(dsn)
    try:
        set_isolation(conn, "READ COMMITTED")
        state, version = read_state(conn)
        barrier.wait(timeout=10)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE operations SET state='committed', version=version+1, updated_at=clock_timestamp() WHERE id=%s RETURNING state, version",
                (OPERATION_ID,),
            )
            row = cur.fetchone()
            cur.execute(
                "INSERT INTO effects(operation_id, node, isolation_level) VALUES (%s, %s, 'READ COMMITTED')",
                (OPERATION_ID, node),
            )
        conn.commit()
        outcome = WorkerOutcome(
            node=node,
            isolation="READ COMMITTED",
            observed_state=state,
            observed_version=version,
            transition="unconditional_commit",
            sqlstate=None,
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


def matrix_worker(
    dsn: str,
    node: str,
    isolation_name: str,
    isolation_sql: str,
    barrier: threading.Barrier,
    sink: list[WorkerOutcome],
    lock: threading.Lock,
) -> None:
    started = time.monotonic()
    conn = db_connect(dsn)
    state = "unknown"
    version = -1
    try:
        set_isolation(conn, isolation_sql)
        state, version = read_state(conn)
        barrier.wait(timeout=10)
        try:
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
                    cur.execute(
                        "INSERT INTO effects(operation_id, node, isolation_level) VALUES (%s, %s, %s)",
                        (OPERATION_ID, node, isolation_sql),
                    )
                    conn.commit()
                    outcome = WorkerOutcome(
                        node=node,
                        isolation=isolation_sql,
                        observed_state=state,
                        observed_version=version,
                        transition="commit_winner",
                        sqlstate=None,
                        returned_state=str(row[0]),
                        returned_version=int(row[1]),
                        reconciled_state=None,
                        reconciled_version=None,
                        reconciled_effects=None,
                        duration_seconds=round(time.monotonic() - started, 6),
                    )
                else:
                    conn.rollback()
                    r_state, r_version, r_effects = reconcile_fresh(dsn)
                    outcome = WorkerOutcome(
                        node=node,
                        isolation=isolation_sql,
                        observed_state=state,
                        observed_version=version,
                        transition="precondition_failed",
                        sqlstate=None,
                        returned_state=None,
                        returned_version=None,
                        reconciled_state=r_state,
                        reconciled_version=r_version,
                        reconciled_effects=r_effects,
                        duration_seconds=round(time.monotonic() - started, 6),
                    )
        except SerializationFailure as exc:
            sqlstate = exc.sqlstate
            conn.rollback()
            r_state, r_version, r_effects = reconcile_fresh(dsn)
            outcome = WorkerOutcome(
                node=node,
                isolation=isolation_sql,
                observed_state=state,
                observed_version=version,
                transition="serialization_failure",
                sqlstate=sqlstate,
                returned_state=None,
                returned_version=None,
                reconciled_state=r_state,
                reconciled_version=r_version,
                reconciled_effects=r_effects,
                duration_seconds=round(time.monotonic() - started, 6),
            )

        with lock:
            sink.append(outcome)
    finally:
        conn.close()


def finalize_run(dsn: str, mode: str, isolation_sql: str, outcomes: list[WorkerOutcome]) -> dict[str, Any]:
    with db_connect(dsn) as conn:
        final_state, final_version = read_state(conn)
        effects = count_effects(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT node, isolation_level FROM effects WHERE operation_id=%s ORDER BY id",
                (OPERATION_ID,),
            )
            effect_rows = [{"node": str(row[0]), "isolation": str(row[1])} for row in cur.fetchall()]
        conn.commit()

    return {
        "mode": mode,
        "isolation": isolation_sql,
        "workers": [asdict(outcome) for outcome in sorted(outcomes, key=lambda x: x.node)],
        "final_state": final_state,
        "final_version": final_version,
        "effect_count": effects,
        "effects": effect_rows,
    }


def run_unsafe_baseline(dsn: str) -> dict[str, Any]:
    reset_world(dsn)
    outcomes: list[WorkerOutcome] = []
    lock = threading.Lock()
    barrier = threading.Barrier(2)
    threads = [
        threading.Thread(target=unsafe_worker, args=(dsn, node, barrier, outcomes, lock), daemon=True)
        for node in ("A", "B")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    if any(thread.is_alive() for thread in threads) or len(outcomes) != 2:
        raise RuntimeError("unsafe baseline workers did not finish cleanly")
    return finalize_run(dsn, "unsafe", "READ COMMITTED", outcomes)


def run_level(dsn: str, isolation_name: str, isolation_sql: str) -> dict[str, Any]:
    reset_world(dsn)
    outcomes: list[WorkerOutcome] = []
    lock = threading.Lock()
    barrier = threading.Barrier(2)
    threads = [
        threading.Thread(
            target=matrix_worker,
            args=(dsn, node, isolation_name, isolation_sql, barrier, outcomes, lock),
            daemon=True,
        )
        for node in ("A", "B")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    if any(thread.is_alive() for thread in threads) or len(outcomes) != 2:
        raise RuntimeError(f"{isolation_name} workers did not finish cleanly: {len(outcomes)} outcomes")
    return finalize_run(dsn, "safe", isolation_sql, outcomes)


def loser(run: dict[str, Any]) -> dict[str, Any] | None:
    return next((w for w in run["workers"] if w["transition"] != "commit_winner"), None)


def winner(run: dict[str, Any]) -> dict[str, Any] | None:
    return next((w for w in run["workers"] if w["transition"] == "commit_winner"), None)


def common_safe(run: dict[str, Any]) -> bool:
    l = loser(run)
    w = winner(run)
    return bool(
        w
        and l
        and all(worker["observed_state"] == "absent" and worker["observed_version"] == INITIAL_VERSION for worker in run["workers"])
        and run["effect_count"] == 1
        and run["final_state"] == "committed"
        and run["final_version"] == INITIAL_VERSION + 1
        and l["reconciled_state"] == "committed"
        and l["reconciled_version"] == INITIAL_VERSION + 1
        and l["reconciled_effects"] == 1
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    parser.add_argument("--out", default="benchmark-results/postgresql-isolation-matrix-v1.0")
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

    unsafe = run_unsafe_baseline(args.dsn)
    matrix = {name: run_level(args.dsn, name, sql) for name, sql in LEVELS.items()}

    rc = matrix["read_committed"]
    rr = matrix["repeatable_read"]
    ser = matrix["serializable"]
    rc_loser = loser(rc)
    rr_loser = loser(rr)
    ser_loser = loser(ser)

    checks = [
        {
            "id": "real_postgresql_service_and_unsafe_baseline",
            "points": 2,
            "pass": bool(server_version_num > 0 and unsafe["effect_count"] == 2 and unsafe["final_version"] == 102),
            "evidence": {"server_version": server_version, "unsafe": unsafe},
        },
        {
            "id": "read_committed_single_winner_zero_row_conflict",
            "points": 2,
            "pass": bool(common_safe(rc) and rc_loser and rc_loser["transition"] == "precondition_failed"),
            "evidence": rc,
        },
        {
            "id": "repeatable_read_single_winner_serialization_failure",
            "points": 2,
            "pass": bool(common_safe(rr) and rr_loser and rr_loser["transition"] == "serialization_failure" and rr_loser["sqlstate"] == "40001"),
            "evidence": rr,
        },
        {
            "id": "serializable_single_winner_serialization_failure",
            "points": 2,
            "pass": bool(common_safe(ser) and ser_loser and ser_loser["transition"] == "serialization_failure" and ser_loser["sqlstate"] == "40001"),
            "evidence": ser,
        },
        {
            "id": "ttp_retry_classification_preserves_one_effect_across_matrix",
            "points": 2,
            "pass": all(common_safe(run) for run in matrix.values()),
            "evidence": {
                name: {
                    "loser_signal": loser(run)["transition"] if loser(run) else None,
                    "sqlstate": loser(run)["sqlstate"] if loser(run) else None,
                    "reconciled_state": loser(run)["reconciled_state"] if loser(run) else None,
                    "final_effect_count": run["effect_count"],
                }
                for name, run in matrix.items()
            },
        },
    ]
    score = sum(item["points"] for item in checks if item["pass"])

    result = {
        "benchmark": "RESONANCE PostgreSQL Isolation-Level Matrix",
        "benchmark_version": "1.0",
        "protocol": "RESONANCE Transactional Trust Protocol v1.0",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "database": {"server_version": server_version, "server_version_num": server_version_num},
        "score": score,
        "max_score": 10,
        "classification": "PostgreSQL isolation-level TTP matrix passes" if score == 10 else "PostgreSQL isolation matrix requires review",
        "unsafe_baseline": unsafe,
        "matrix": matrix,
        "checks": checks,
        "signal_taxonomy": {
            "READ COMMITTED": "precondition_failed (conditional UPDATE returned 0 rows)",
            "REPEATABLE READ": "serialization_failure / SQLSTATE 40001",
            "SERIALIZABLE": "serialization_failure / SQLSTATE 40001",
        },
        "retry_rule": "A database conflict signal is not permission to blindly replay the mutation. Abort/close the failed transaction, re-observe authoritative state, re-verify/re-bind preconditions, and retry only if the operation is still absent and legal.",
        "invariant": "Isolation-level conflict signals differ, but TTP recovery must preserve at most one committed effect and re-enter from fresh state before any retry.",
        "scope": "Real PostgreSQL service container with two concurrent independent client connections per isolation level; local synthetic operation/effects tables only.",
        "external_safety_certification": False,
    }

    (out_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = [
        "# PostgreSQL Isolation-Level Matrix v1.0",
        "",
        f"**Score:** {score}/10",
        f"**PostgreSQL:** {server_version}",
        f"**Unsafe baseline effects:** {unsafe['effect_count']}",
    ]
    for name, run in matrix.items():
        l = loser(run)
        summary.append(
            f"**{run['isolation']}:** effects={run['effect_count']}; loser={l['transition'] if l else 'missing'}; sqlstate={l['sqlstate'] if l else None}; reconciled={l['reconciled_state'] if l else None}/v{l['reconciled_version'] if l else None}"
        )
    (out_dir / "RESULT.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())

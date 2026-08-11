from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

OPERATION_ID = "op-1"
INITIAL_VERSION = 100
OUTBOX_ID = "outbox-op-1"
STABLE_KEY = "op-1:external-effect:v1"


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
                CREATE TABLE IF NOT EXISTS outbox (
                    id text PRIMARY KEY,
                    operation_id text NOT NULL,
                    idempotency_key text NOT NULL UNIQUE,
                    status text NOT NULL,
                    delivery_attempts integer NOT NULL DEFAULT 0,
                    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
                    delivered_at timestamptz
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS external_effects (
                    id bigserial PRIMARY KEY,
                    operation_id text NOT NULL,
                    idempotency_key text NOT NULL UNIQUE,
                    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
                )
                """
            )
        conn.commit()


def reset_world(dsn: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE external_effects RESTART IDENTITY")
            cur.execute("DELETE FROM outbox")
            cur.execute("DELETE FROM operations")
            cur.execute(
                "INSERT INTO operations(id, state, version) VALUES (%s, 'absent', %s)",
                (OPERATION_ID, INITIAL_VERSION),
            )
        conn.commit()


def snapshot(dsn: str) -> dict[str, Any]:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT state, version FROM operations WHERE id=%s", (OPERATION_ID,))
            operation = cur.fetchone()
            cur.execute(
                "SELECT id, idempotency_key, status, delivery_attempts FROM outbox WHERE operation_id=%s ORDER BY id",
                (OPERATION_ID,),
            )
            outbox_rows = [
                {
                    "id": str(row[0]),
                    "idempotency_key": str(row[1]),
                    "status": str(row[2]),
                    "delivery_attempts": int(row[3]),
                }
                for row in cur.fetchall()
            ]
            cur.execute(
                "SELECT id, idempotency_key FROM external_effects WHERE operation_id=%s ORDER BY id",
                (OPERATION_ID,),
            )
            effects = [
                {"id": int(row[0]), "idempotency_key": str(row[1])}
                for row in cur.fetchall()
            ]
        conn.commit()
    return {
        "operation": {"state": str(operation[0]), "version": int(operation[1])},
        "outbox": outbox_rows,
        "external_effects": effects,
        "external_effect_count": len(effects),
    }


def commit_business_only(dsn: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE operations
                SET state='committed', version=version+1, updated_at=clock_timestamp()
                WHERE id=%s AND state='absent' AND version=%s
                RETURNING version
                """,
                (OPERATION_ID, INITIAL_VERSION),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("business-only transition precondition failed")
        conn.commit()


def commit_business_with_outbox(dsn: str, *, crash_before_commit: bool = False) -> None:
    conn = db_connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE operations
                SET state='committed', version=version+1, updated_at=clock_timestamp()
                WHERE id=%s AND state='absent' AND version=%s
                RETURNING version
                """,
                (OPERATION_ID, INITIAL_VERSION),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("outbox transition precondition failed")
            cur.execute(
                """
                INSERT INTO outbox(id, operation_id, idempotency_key, status)
                VALUES (%s, %s, %s, 'pending')
                """,
                (OUTBOX_ID, OPERATION_ID, STABLE_KEY),
            )
            if crash_before_commit:
                raise RuntimeError("synthetic crash before database commit")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def external_apply(dsn: str, idempotency_key: str) -> str:
    """Synthetic external service: stable idempotency key is unique at its own boundary."""
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO external_effects(operation_id, idempotency_key)
                VALUES (%s, %s)
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING id
                """,
                (OPERATION_ID, idempotency_key),
            )
            row = cur.fetchone()
        conn.commit()
    return "applied" if row is not None else "deduplicated"


def external_status(dsn: str, idempotency_key: str) -> str:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM external_effects WHERE operation_id=%s AND idempotency_key=%s",
                (OPERATION_ID, idempotency_key),
            )
            count = int(cur.fetchone()[0])
        conn.commit()
    return "committed" if count == 1 else "absent" if count == 0 else "conflict"


def increment_attempt(dsn: str) -> int:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE outbox
                SET delivery_attempts=delivery_attempts+1
                WHERE id=%s
                RETURNING delivery_attempts
                """,
                (OUTBOX_ID,),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("outbox row missing")
        conn.commit()
    return int(row[0])


def mark_delivered(dsn: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE outbox
                SET status='delivered', delivered_at=clock_timestamp()
                WHERE id=%s
                """,
                (OUTBOX_ID,),
            )
        conn.commit()


def scenario_unsafe_boundary(dsn: str) -> dict[str, Any]:
    reset_world(dsn)
    commit_business_only(dsn)

    first_key = "unsafe:attempt:1"
    second_key = "unsafe:attempt:2"
    first = external_apply(dsn, first_key)
    # Synthetic crash/ack loss occurs after the external service committed effect #1.
    # Recovery has no durable outbox identity and generates a new request key.
    second = external_apply(dsn, second_key)
    world = snapshot(dsn)
    return {
        "first_delivery": first,
        "synthetic_failure": "crash_after_external_commit_before_ack",
        "retry_delivery": second,
        "retry_identity_reused": False,
        "world": world,
    }


def scenario_outbox_atomicity(dsn: str) -> dict[str, Any]:
    reset_world(dsn)
    rolled_back = False
    try:
        commit_business_with_outbox(dsn, crash_before_commit=True)
    except RuntimeError:
        rolled_back = True
    after_crash = snapshot(dsn)

    commit_business_with_outbox(dsn)
    after_commit = snapshot(dsn)
    return {
        "synthetic_precommit_crash_rolled_back": rolled_back,
        "after_precommit_crash": after_crash,
        "after_atomic_commit": after_commit,
    }


def scenario_safe_redelivery(dsn: str) -> dict[str, Any]:
    reset_world(dsn)
    commit_business_with_outbox(dsn)

    attempt_1 = increment_attempt(dsn)
    first = external_apply(dsn, STABLE_KEY)
    # ACK is lost: leave outbox pending.
    after_ack_loss = snapshot(dsn)

    attempt_2 = increment_attempt(dsn)
    second = external_apply(dsn, STABLE_KEY)
    reconciled = external_status(dsn, STABLE_KEY)
    if reconciled == "committed":
        mark_delivered(dsn)
    final = snapshot(dsn)
    return {
        "attempt_1": attempt_1,
        "first_delivery": first,
        "synthetic_failure": "ack_lost_after_external_commit",
        "after_ack_loss": after_ack_loss,
        "attempt_2": attempt_2,
        "second_delivery": second,
        "reconciled_external_status": reconciled,
        "final": final,
    }


def scenario_safe_reconcile_before_retry(dsn: str) -> dict[str, Any]:
    reset_world(dsn)
    commit_business_with_outbox(dsn)

    attempt_1 = increment_attempt(dsn)
    first = external_apply(dsn, STABLE_KEY)
    # ACK is lost. On recovery we reconcile before any second external apply call.
    status = external_status(dsn, STABLE_KEY)
    second_external_call_made = False
    if status == "committed":
        mark_delivered(dsn)
    else:
        second_external_call_made = True
        external_apply(dsn, STABLE_KEY)
    final = snapshot(dsn)
    return {
        "attempt_1": attempt_1,
        "first_delivery": first,
        "synthetic_failure": "ack_lost_after_external_commit",
        "reconciled_external_status": status,
        "second_external_call_made": second_external_call_made,
        "final": final,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dsn",
        default=os.environ.get(
            "DATABASE_URL",
            "postgresql://resonance:resonance@127.0.0.1:5432/resonance",
        ),
    )
    parser.add_argument(
        "--out",
        default="benchmark-results/postgresql-transactional-outbox-v1.0",
    )
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

    unsafe = scenario_unsafe_boundary(args.dsn)
    atomicity = scenario_outbox_atomicity(args.dsn)
    redelivery = scenario_safe_redelivery(args.dsn)
    reconcile = scenario_safe_reconcile_before_retry(args.dsn)

    after_crash = atomicity["after_precommit_crash"]
    after_commit = atomicity["after_atomic_commit"]
    redelivery_final = redelivery["final"]
    reconcile_final = reconcile["final"]

    checks = [
        {
            "id": "unsafe_db_external_boundary_duplicate_reproduced",
            "points": 2,
            "pass": bool(
                server_version_num > 0
                and unsafe["world"]["operation"] == {"state": "committed", "version": 101}
                and unsafe["world"]["external_effect_count"] == 2
                and unsafe["retry_identity_reused"] is False
            ),
            "evidence": {"server_version": server_version, **unsafe},
        },
        {
            "id": "business_state_and_outbox_intent_are_atomic",
            "points": 2,
            "pass": bool(
                atomicity["synthetic_precommit_crash_rolled_back"]
                and after_crash["operation"] == {"state": "absent", "version": 100}
                and len(after_crash["outbox"]) == 0
                and after_commit["operation"] == {"state": "committed", "version": 101}
                and len(after_commit["outbox"]) == 1
                and after_commit["outbox"][0]["status"] == "pending"
                and after_commit["outbox"][0]["idempotency_key"] == STABLE_KEY
            ),
            "evidence": atomicity,
        },
        {
            "id": "stable_idempotency_key_dedupes_redelivery",
            "points": 2,
            "pass": bool(
                redelivery["first_delivery"] == "applied"
                and redelivery["second_delivery"] == "deduplicated"
                and redelivery["attempt_1"] == 1
                and redelivery["attempt_2"] == 2
                and redelivery["reconciled_external_status"] == "committed"
                and redelivery_final["external_effect_count"] == 1
                and redelivery_final["outbox"][0]["status"] == "delivered"
            ),
            "evidence": redelivery,
        },
        {
            "id": "ambiguous_ack_reconciles_before_external_retry",
            "points": 2,
            "pass": bool(
                reconcile["first_delivery"] == "applied"
                and reconcile["reconciled_external_status"] == "committed"
                and reconcile["second_external_call_made"] is False
                and reconcile_final["external_effect_count"] == 1
                and reconcile_final["outbox"][0]["delivery_attempts"] == 1
                and reconcile_final["outbox"][0]["status"] == "delivered"
            ),
            "evidence": reconcile,
        },
        {
            "id": "final_cross_boundary_invariant_proved",
            "points": 2,
            "pass": bool(
                redelivery_final["operation"] == {"state": "committed", "version": 101}
                and redelivery_final["external_effect_count"] == 1
                and reconcile_final["operation"] == {"state": "committed", "version": 101}
                and reconcile_final["external_effect_count"] == 1
            ),
            "evidence": {
                "redelivery_final": redelivery_final,
                "reconcile_before_retry_final": reconcile_final,
            },
        },
    ]
    score = sum(item["points"] for item in checks if item["pass"])

    result = {
        "benchmark": "RESONANCE PostgreSQL Transactional Outbox Boundary",
        "benchmark_version": "1.0",
        "protocol": "RESONANCE Transactional Trust Protocol v1.0",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "database": {"server_version": server_version, "server_version_num": server_version_num},
        "score": score,
        "max_score": 10,
        "classification": "Transactional outbox cross-boundary protocol passes" if score == 10 else "Transactional outbox boundary requires review",
        "unsafe": unsafe,
        "transactional_outbox_atomicity": atomicity,
        "safe_redelivery": redelivery,
        "safe_reconcile_before_retry": reconcile,
        "checks": checks,
        "invariants": [
            "Business-state commit and durable delivery intent must share one database transaction.",
            "DB COMMITTED does not imply external effect acknowledged or absent.",
            "External redelivery must reuse a stable idempotency identity or equivalent deduplication boundary.",
            "Ambiguous external acknowledgement must reconcile external state before business re-execution.",
            "One logical business transition should prove at most one external committed effect under the declared adapter contract.",
        ],
        "scope": "Real PostgreSQL service container; business/outbox state in PostgreSQL; synthetic external service ledger reached through separate database transactions to model the DB-to-external-effect boundary.",
        "external_safety_certification": False,
    }

    (out_dir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = [
        "# PostgreSQL Transactional Outbox Boundary v1.0",
        "",
        f"**Score:** {score}/10",
        f"**PostgreSQL:** {server_version}",
        f"**Unsafe external effects:** {unsafe['world']['external_effect_count']}",
        f"**Safe redelivery external effects:** {redelivery_final['external_effect_count']}",
        f"**Reconcile-before-retry external effects:** {reconcile_final['external_effect_count']}",
        f"**Stable redelivery result:** {redelivery['second_delivery']}",
        f"**Second external call after reconciliation:** {reconcile['second_external_call_made']}",
    ]
    (out_dir / "RESULT.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())

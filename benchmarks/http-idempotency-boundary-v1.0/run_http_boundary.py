from __future__ import annotations

import argparse
import http.client
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

INITIAL_VERSION = 100


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
        conn.commit()


def prepare_operation(dsn: str, operation_id: str, outbox_id: str, stable_key: str) -> dict[str, Any]:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM outbox WHERE operation_id=%s OR id=%s", (operation_id, outbox_id))
            cur.execute("DELETE FROM operations WHERE id=%s", (operation_id,))
            cur.execute(
                "INSERT INTO operations(id, state, version) VALUES (%s, 'absent', %s)",
                (operation_id, INITIAL_VERSION),
            )
            cur.execute(
                """
                UPDATE operations
                SET state='committed', version=version+1, updated_at=clock_timestamp()
                WHERE id=%s AND state='absent' AND version=%s
                RETURNING state, version
                """,
                (operation_id, INITIAL_VERSION),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("business transition precondition failed")
            cur.execute(
                """
                INSERT INTO outbox(id, operation_id, idempotency_key, status)
                VALUES (%s, %s, %s, 'pending')
                """,
                (outbox_id, operation_id, stable_key),
            )
        conn.commit()
    return db_snapshot(dsn, operation_id)


def increment_attempt(dsn: str, outbox_id: str) -> int:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE outbox SET delivery_attempts=delivery_attempts+1 WHERE id=%s RETURNING delivery_attempts",
                (outbox_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("outbox row missing")
        conn.commit()
    return int(row[0])


def mark_delivered(dsn: str, outbox_id: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE outbox SET status='delivered', delivered_at=clock_timestamp() WHERE id=%s",
                (outbox_id,),
            )
        conn.commit()


def db_snapshot(dsn: str, operation_id: str) -> dict[str, Any]:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT state, version FROM operations WHERE id=%s", (operation_id,))
            operation = cur.fetchone()
            cur.execute(
                "SELECT id, idempotency_key, status, delivery_attempts FROM outbox WHERE operation_id=%s",
                (operation_id,),
            )
            outbox = cur.fetchone()
        conn.commit()
    if operation is None:
        raise RuntimeError("operation missing")
    return {
        "operation": {"state": str(operation[0]), "version": int(operation[1])},
        "outbox": None
        if outbox is None
        else {
            "id": str(outbox[0]),
            "idempotency_key": str(outbox[1]),
            "status": str(outbox[2]),
            "delivery_attempts": int(outbox[3]),
        },
    }


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def post_effect(base_url: str, operation_id: str, idempotency_key: str, *, drop_ack: bool) -> dict[str, Any]:
    body = json.dumps({"operation_id": operation_id}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/effects",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "X-Operation-Id": operation_id,
            "Idempotency-Key": idempotency_key,
            "X-Drop-Ack": "1" if drop_ack else "0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return {"outcome": "acknowledged", "http_status": response.status, "payload": payload}
    except (http.client.RemoteDisconnected, urllib.error.URLError, ConnectionResetError, BrokenPipeError, TimeoutError) as exc:
        if not drop_ack:
            raise
        return {"outcome": "ack_unknown", "error_type": type(exc).__name__}


def external_status(base_url: str, operation_id: str) -> dict[str, Any]:
    quoted = urllib.parse.quote(operation_id, safe="")
    return get_json(f"{base_url.rstrip('/')}/status/{quoted}")


def scenario_unsafe_new_identity(dsn: str, base_url: str) -> dict[str, Any]:
    operation_id = "http-unsafe-op"
    outbox_id = "outbox-http-unsafe"
    logical_key = "http-unsafe-op:effect:v1"
    after_commit = prepare_operation(dsn, operation_id, outbox_id, logical_key)

    attempt_1 = increment_attempt(dsn, outbox_id)
    first = post_effect(base_url, operation_id, "http-unsafe:attempt:1", drop_ack=True)

    attempt_2 = increment_attempt(dsn, outbox_id)
    second = post_effect(base_url, operation_id, "http-unsafe:attempt:2", drop_ack=False)
    status = external_status(base_url, operation_id)
    mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "logical_outbox_key": logical_key,
        "after_db_commit": after_commit,
        "attempt_1": attempt_1,
        "first_post": first,
        "synthetic_failure": "remote_effect_committed_then_http_connection_closed_before_response",
        "attempt_2": attempt_2,
        "second_post": second,
        "http_status_after_retry": status,
        "retry_identity_reused": False,
        "final_db": db_snapshot(dsn, operation_id),
    }


def scenario_safe_redelivery(dsn: str, base_url: str) -> dict[str, Any]:
    operation_id = "http-safe-redelivery-op"
    outbox_id = "outbox-http-safe-redelivery"
    stable_key = "http-safe-redelivery-op:effect:v1"
    after_commit = prepare_operation(dsn, operation_id, outbox_id, stable_key)

    attempt_1 = increment_attempt(dsn, outbox_id)
    first = post_effect(base_url, operation_id, stable_key, drop_ack=True)
    status_after_ack_loss = external_status(base_url, operation_id)

    attempt_2 = increment_attempt(dsn, outbox_id)
    second = post_effect(base_url, operation_id, stable_key, drop_ack=False)
    final_status = external_status(base_url, operation_id)
    if final_status["status"] == "committed" and final_status["effect_count"] == 1:
        mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "stable_key": stable_key,
        "after_db_commit": after_commit,
        "attempt_1": attempt_1,
        "first_post": first,
        "synthetic_failure": "remote_effect_committed_then_http_connection_closed_before_response",
        "status_after_ack_loss": status_after_ack_loss,
        "attempt_2": attempt_2,
        "second_post": second,
        "final_http_status": final_status,
        "final_db": db_snapshot(dsn, operation_id),
    }


def scenario_safe_reconcile(dsn: str, base_url: str) -> dict[str, Any]:
    operation_id = "http-safe-reconcile-op"
    outbox_id = "outbox-http-safe-reconcile"
    stable_key = "http-safe-reconcile-op:effect:v1"
    after_commit = prepare_operation(dsn, operation_id, outbox_id, stable_key)

    attempt_1 = increment_attempt(dsn, outbox_id)
    first = post_effect(base_url, operation_id, stable_key, drop_ack=True)
    status = external_status(base_url, operation_id)
    second_post_made = False
    if status["status"] == "committed" and status["effect_count"] == 1:
        mark_delivered(dsn, outbox_id)
    else:
        second_post_made = True
        post_effect(base_url, operation_id, stable_key, drop_ack=False)

    return {
        "operation_id": operation_id,
        "stable_key": stable_key,
        "after_db_commit": after_commit,
        "attempt_1": attempt_1,
        "first_post": first,
        "synthetic_failure": "remote_effect_committed_then_http_connection_closed_before_response",
        "reconciled_http_status": status,
        "second_post_made": second_post_made,
        "final_db": db_snapshot(dsn, operation_id),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dsn",
        default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"),
    )
    parser.add_argument("--base-url", default=os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18080"))
    parser.add_argument("--out", default="benchmark-results/http-idempotency-boundary-v1.0")
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

    health = get_json(f"{args.base_url.rstrip('/')}/health")
    unsafe = scenario_unsafe_new_identity(args.dsn, args.base_url)
    redelivery = scenario_safe_redelivery(args.dsn, args.base_url)
    reconcile = scenario_safe_reconcile(args.dsn, args.base_url)

    unsafe_http = unsafe["http_status_after_retry"]
    redelivery_http = redelivery["final_http_status"]
    reconcile_http = reconcile["reconciled_http_status"]

    checks = [
        {
            "id": "real_postgresql_and_separate_http_service_boundary",
            "points": 2,
            "pass": bool(
                server_version_num > 0
                and health.get("status") == "ok"
                and health.get("service") == "resonance-external-http"
                and int(health.get("pid", -1)) == 1
            ),
            "evidence": {
                "postgresql": {"server_version": server_version, "server_version_num": server_version_num},
                "http_service": health,
                "http_service_image": os.environ.get("HTTP_SERVICE_IMAGE", "unknown"),
                "http_service_image_digest": os.environ.get("HTTP_SERVICE_IMAGE_DIGEST", "unknown"),
            },
        },
        {
            "id": "unsafe_http_ack_loss_new_identity_duplicates_remote_effect",
            "points": 2,
            "pass": bool(
                unsafe["first_post"]["outcome"] == "ack_unknown"
                and unsafe["second_post"]["outcome"] == "acknowledged"
                and unsafe["second_post"]["payload"]["delivery"] == "applied"
                and unsafe["retry_identity_reused"] is False
                and unsafe_http["status"] == "conflict"
                and unsafe_http["effect_count"] == 2
                and unsafe["final_db"]["operation"] == {"state": "committed", "version": 101}
            ),
            "evidence": unsafe,
        },
        {
            "id": "stable_idempotency_key_dedupes_real_http_redelivery",
            "points": 2,
            "pass": bool(
                redelivery["first_post"]["outcome"] == "ack_unknown"
                and redelivery["status_after_ack_loss"]["status"] == "committed"
                and redelivery["status_after_ack_loss"]["effect_count"] == 1
                and redelivery["second_post"]["outcome"] == "acknowledged"
                and redelivery["second_post"]["payload"]["delivery"] == "deduplicated"
                and redelivery_http["effect_count"] == 1
                and redelivery_http["post_requests"] == 2
                and redelivery["final_db"]["outbox"]["delivery_attempts"] == 2
                and redelivery["final_db"]["outbox"]["status"] == "delivered"
            ),
            "evidence": redelivery,
        },
        {
            "id": "http_status_reconciliation_avoids_second_post",
            "points": 2,
            "pass": bool(
                reconcile["first_post"]["outcome"] == "ack_unknown"
                and reconcile_http["status"] == "committed"
                and reconcile_http["effect_count"] == 1
                and reconcile_http["post_requests"] == 1
                and reconcile["second_post_made"] is False
                and reconcile["final_db"]["outbox"]["delivery_attempts"] == 1
                and reconcile["final_db"]["outbox"]["status"] == "delivered"
            ),
            "evidence": reconcile,
        },
        {
            "id": "ttp_http_boundary_final_invariant",
            "points": 2,
            "pass": bool(
                redelivery["final_db"]["operation"] == {"state": "committed", "version": 101}
                and redelivery_http["effect_count"] == 1
                and reconcile["final_db"]["operation"] == {"state": "committed", "version": 101}
                and reconcile_http["effect_count"] == 1
                and unsafe_http["effect_count"] == 2
            ),
            "evidence": {
                "unsafe_external_effects": unsafe_http["effect_count"],
                "safe_redelivery_external_effects": redelivery_http["effect_count"],
                "safe_reconcile_external_effects": reconcile_http["effect_count"],
            },
        },
    ]

    score = sum(item["points"] for item in checks if item["pass"])
    result = {
        "benchmark": "RESONANCE HTTP Idempotency Boundary",
        "benchmark_version": "1.0",
        "protocol": "RESONANCE Transactional Trust Protocol v1.0",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "database": {"server_version": server_version, "server_version_num": server_version_num},
        "http_service": health,
        "http_service_image": os.environ.get("HTTP_SERVICE_IMAGE", "unknown"),
        "http_service_image_digest": os.environ.get("HTTP_SERVICE_IMAGE_DIGEST", "unknown"),
        "score": score,
        "max_score": 10,
        "classification": "HTTP idempotency boundary protocol passes" if score == 10 else "HTTP idempotency boundary requires review",
        "unsafe": unsafe,
        "safe_redelivery": redelivery,
        "safe_reconcile_before_retry": reconcile,
        "checks": checks,
        "invariants": [
            "HTTP ACK loss does not imply remote effect absence.",
            "A retry of the same logical effect must preserve one stable idempotency identity when the remote contract supports it.",
            "A real HTTP redelivery may occur more than once while the remote committed effect remains one.",
            "If remote status can be queried authoritatively, reconcile before making another consequential POST after an ambiguous acknowledgement.",
            "Database state, outbox state, HTTP request identity, remote status and final effect count belong in one proof trajectory.",
        ],
        "scope": "Real PostgreSQL service container plus a separate Dockerized HTTP service; remote effect state is in the HTTP service process and is outside the PostgreSQL transaction boundary.",
        "external_safety_certification": False,
    }

    (out_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = [
        "# HTTP Idempotency Boundary v1.0",
        "",
        f"**Score:** {score}/10",
        f"**PostgreSQL:** {server_version}",
        f"**HTTP service:** {health.get('service')} / hostname `{health.get('hostname')}` / pid `{health.get('pid')}`",
        f"**Unsafe external effects:** {unsafe_http['effect_count']}",
        f"**Safe redelivery external effects:** {redelivery_http['effect_count']}",
        f"**Safe reconcile external effects:** {reconcile_http['effect_count']}",
        "",
        "## Observed HTTP trajectories",
        "",
        f"- Unsafe: ACK unknown → new key → remote effect count `{unsafe_http['effect_count']}`.",
        f"- Safe redelivery: ACK unknown → same key → `{redelivery['second_post']['payload']['delivery']}` → remote effect count `{redelivery_http['effect_count']}`.",
        f"- Safe reconcile: ACK unknown → GET status `{reconcile_http['status']}` → second POST `{reconcile['second_post_made']}`.",
    ]
    (out_dir / "RESULT.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if score == 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())

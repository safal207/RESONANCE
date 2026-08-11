from __future__ import annotations

import argparse
import http.client
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

CONTAINER_NAME = "resonance-external-http-ttl"
VOLUME_NAME = "resonance-idempotency-ttl-v1"
HTTP_IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18082")
SERVICE_SCRIPT = Path("benchmarks/idempotency-ttl-replay-v1.0/external_service.py").resolve()
RECOVERY_DELAY_SECONDS = 120
UNSAFE_TTL_SECONDS = 60
SAFE_TTL_SECONDS = 300


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
                    delivered_at timestamptz
                )
                """
            )
        conn.commit()


def reset_local(dsn: str, operation_id: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM outbox WHERE operation_id=%s", (operation_id,))
            cur.execute("DELETE FROM operations WHERE id=%s", (operation_id,))
            cur.execute("INSERT INTO operations(id, state, version) VALUES (%s, 'absent', 100)", (operation_id,))
        conn.commit()


def commit_business_with_outbox(dsn: str, operation_id: str, outbox_id: str, key: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE operations
                SET state='committed', version=101, updated_at=clock_timestamp()
                WHERE id=%s AND state='absent' AND version=100
                RETURNING version
                """,
                (operation_id,),
            )
            if cur.fetchone() is None:
                raise RuntimeError("business precondition failed")
            cur.execute(
                "INSERT INTO outbox(id, operation_id, idempotency_key, status) VALUES (%s, %s, %s, 'pending')",
                (outbox_id, operation_id, key),
            )
        conn.commit()


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


def local_snapshot(dsn: str, operation_id: str) -> dict[str, Any]:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT state, version FROM operations WHERE id=%s", (operation_id,))
            op = cur.fetchone()
            cur.execute(
                "SELECT id, idempotency_key, status, delivery_attempts FROM outbox WHERE operation_id=%s",
                (operation_id,),
            )
            outbox = cur.fetchone()
        conn.commit()
    return {
        "operation": {"state": str(op[0]), "version": int(op[1])},
        "outbox": {
            "id": str(outbox[0]),
            "idempotency_key": str(outbox[1]),
            "status": str(outbox[2]),
            "delivery_attempts": int(outbox[3]),
        },
    }


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check)


def stop_service() -> None:
    run("docker", "rm", "-f", CONTAINER_NAME, check=False)


def prepare_volume() -> None:
    stop_service()
    run("docker", "volume", "rm", "-f", VOLUME_NAME, check=False)
    run("docker", "volume", "create", VOLUME_NAME)


def start_service() -> dict[str, Any]:
    stop_service()
    run(
        "docker", "run", "-d", "--name", CONTAINER_NAME,
        "-p", "18082:8080",
        "-e", "STATE_DB=/state/remote.db",
        "-e", "PYTHONUNBUFFERED=1",
        "-v", f"{VOLUME_NAME}:/state",
        "-v", f"{SERVICE_SCRIPT}:/app/external_service.py:ro",
        HTTP_IMAGE,
        "python", "/app/external_service.py", "--host", "0.0.0.0", "--port", "8080",
    )
    last_error: Exception | None = None
    for _ in range(40):
        try:
            health = get_json("/health", logical_time=None)
            if health.get("status") == "ok":
                return health
        except Exception as exc:
            last_error = exc
        time.sleep(0.25)
    logs = run("docker", "logs", CONTAINER_NAME, check=False).stdout
    raise RuntimeError(f"HTTP TTL service failed to become healthy: {last_error}; logs={logs}")


def request_json(
    method: str,
    path: str,
    *,
    logical_time: int | None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    merged = {"Content-Type": "application/json", **(headers or {})}
    if logical_time is not None:
        merged["X-Logical-Time"] = str(logical_time)
    req = urllib.request.Request(
        BASE_URL + path,
        data=b"{}" if method == "POST" else None,
        method=method,
        headers=merged,
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(path: str, *, logical_time: int | None) -> dict[str, Any]:
    return request_json("GET", path, logical_time=logical_time)


def post_effect(operation_id: str, key: str, *, now: int, ttl: int, drop_ack: bool) -> dict[str, Any]:
    headers = {
        "X-Operation-Id": operation_id,
        "Idempotency-Key": key,
        "X-Idempotency-TTL": str(ttl),
        "X-Drop-Ack": "1" if drop_ack else "0",
    }
    try:
        payload = request_json("POST", "/effects", logical_time=now, headers=headers)
        return {"outcome": "acknowledged", "payload": payload}
    except (http.client.RemoteDisconnected, ConnectionResetError, BrokenPipeError, urllib.error.URLError) as exc:
        return {"outcome": "ack_unknown", "error_type": type(exc).__name__}


def status(operation_id: str, now: int) -> dict[str, Any]:
    return get_json(f"/status/{operation_id}", logical_time=now)


def setup_operation(dsn: str, operation_id: str) -> tuple[str, str]:
    outbox_id = f"outbox-{operation_id}"
    key = f"{operation_id}:effect:v1"
    reset_local(dsn, operation_id)
    commit_business_with_outbox(dsn, operation_id, outbox_id, key)
    return outbox_id, key


def scenario_unsafe_ttl_expiry(dsn: str) -> dict[str, Any]:
    operation_id = "ttl-unsafe-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 1_000_000
    retry_at = t0 + RECOVERY_DELAY_SECONDS

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, ttl=UNSAFE_TTL_SECONDS, drop_ack=True)
    initial_remote = status(operation_id, t0)
    expired_remote = status(operation_id, retry_at)
    attempt_2 = increment_attempt(dsn, outbox_id)
    second_post = post_effect(operation_id, key, now=retry_at, ttl=UNSAFE_TTL_SECONDS, drop_ack=False)
    final_remote = status(operation_id, retry_at)
    mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "retry_at": retry_at,
        "recovery_delay_seconds": RECOVERY_DELAY_SECONDS,
        "ttl_seconds": UNSAFE_TTL_SECONDS,
        "ttl_covers_recovery_window": UNSAFE_TTL_SECONDS >= RECOVERY_DELAY_SECONDS,
        "attempt_1": attempt_1,
        "first_post": first_post,
        "initial_remote": initial_remote,
        "expired_remote_before_retry": expired_remote,
        "attempt_2": attempt_2,
        "second_post": second_post,
        "final_remote": final_remote,
        "final_local": local_snapshot(dsn, operation_id),
    }


def scenario_safe_retention(dsn: str) -> dict[str, Any]:
    operation_id = "ttl-safe-retention-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 2_000_000
    retry_at = t0 + RECOVERY_DELAY_SECONDS

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, ttl=SAFE_TTL_SECONDS, drop_ack=True)
    initial_remote = status(operation_id, t0)
    retry_remote = status(operation_id, retry_at)
    attempt_2 = increment_attempt(dsn, outbox_id)
    second_post = post_effect(operation_id, key, now=retry_at, ttl=SAFE_TTL_SECONDS, drop_ack=False)
    final_remote = status(operation_id, retry_at)
    if final_remote["status"] == "committed":
        mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "retry_at": retry_at,
        "recovery_delay_seconds": RECOVERY_DELAY_SECONDS,
        "ttl_seconds": SAFE_TTL_SECONDS,
        "ttl_covers_recovery_window": SAFE_TTL_SECONDS >= RECOVERY_DELAY_SECONDS,
        "attempt_1": attempt_1,
        "first_post": first_post,
        "initial_remote": initial_remote,
        "remote_before_retry": retry_remote,
        "attempt_2": attempt_2,
        "second_post": second_post,
        "final_remote": final_remote,
        "final_local": local_snapshot(dsn, operation_id),
    }


def scenario_safe_reconcile_after_expiry(dsn: str) -> dict[str, Any]:
    operation_id = "ttl-safe-reconcile-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 3_000_000
    recovery_at = t0 + RECOVERY_DELAY_SECONDS

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, ttl=UNSAFE_TTL_SECONDS, drop_ack=True)
    expired_remote = status(operation_id, recovery_at)
    second_post_made = False
    if expired_remote["status"] == "committed":
        mark_delivered(dsn, outbox_id)
    else:
        second_post_made = True
        increment_attempt(dsn, outbox_id)
        post_effect(operation_id, key, now=recovery_at, ttl=UNSAFE_TTL_SECONDS, drop_ack=False)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "recovery_at": recovery_at,
        "recovery_delay_seconds": RECOVERY_DELAY_SECONDS,
        "ttl_seconds": UNSAFE_TTL_SECONDS,
        "first_post": first_post,
        "attempt_1": attempt_1,
        "reconciled_after_expiry": expired_remote,
        "second_post_made": second_post_made,
        "final_remote": status(operation_id, recovery_at),
        "final_local": local_snapshot(dsn, operation_id),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    parser.add_argument("--out", default="benchmark-results/idempotency-ttl-replay-v1.0")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    init_schema(args.dsn)
    prepare_volume()
    health = start_service()

    try:
        unsafe = scenario_unsafe_ttl_expiry(args.dsn)
        safe = scenario_safe_retention(args.dsn)
        reconcile = scenario_safe_reconcile_after_expiry(args.dsn)

        with db_connect(args.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW server_version")
                server_version = str(cur.fetchone()[0])
            conn.commit()

        image_digest = run("docker", "image", "inspect", HTTP_IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()

        checks = [
            {
                "id": "ttl_record_is_active_then_expires_while_effect_persists",
                "points": 2,
                "pass": bool(
                    unsafe["initial_remote"]["effect_count"] == 1
                    and unsafe["initial_remote"]["active_idempotency_records"] == 1
                    and unsafe["expired_remote_before_retry"]["effect_count"] == 1
                    and unsafe["expired_remote_before_retry"]["active_idempotency_records"] == 0
                ),
                "evidence": {
                    "initial": unsafe["initial_remote"],
                    "after_ttl_expiry": unsafe["expired_remote_before_retry"],
                },
            },
            {
                "id": "ttl_shorter_than_recovery_window_allows_duplicate",
                "points": 2,
                "pass": bool(
                    unsafe["first_post"]["outcome"] == "ack_unknown"
                    and not unsafe["ttl_covers_recovery_window"]
                    and unsafe["second_post"]["payload"]["delivery"] == "applied"
                    and unsafe["final_remote"]["effect_count"] == 2
                    and unsafe["final_remote"]["status"] == "conflict"
                ),
                "evidence": unsafe,
            },
            {
                "id": "retention_covering_recovery_window_dedupes_delayed_retry",
                "points": 2,
                "pass": bool(
                    safe["first_post"]["outcome"] == "ack_unknown"
                    and safe["ttl_covers_recovery_window"]
                    and safe["remote_before_retry"]["active_idempotency_records"] == 1
                    and safe["second_post"]["payload"]["delivery"] == "deduplicated"
                    and safe["final_remote"]["effect_count"] == 1
                ),
                "evidence": safe,
            },
            {
                "id": "authoritative_reconcile_after_ttl_expiry_avoids_replay",
                "points": 2,
                "pass": bool(
                    reconcile["first_post"]["outcome"] == "ack_unknown"
                    and reconcile["reconciled_after_expiry"]["active_idempotency_records"] == 0
                    and reconcile["reconciled_after_expiry"]["status"] == "committed"
                    and reconcile["reconciled_after_expiry"]["effect_count"] == 1
                    and reconcile["second_post_made"] is False
                ),
                "evidence": reconcile,
            },
            {
                "id": "ttp_time_memory_recovery_invariant_proved",
                "points": 2,
                "pass": bool(
                    unsafe["final_remote"]["effect_count"] == 2
                    and safe["final_remote"]["effect_count"] == 1
                    and reconcile["final_remote"]["effect_count"] == 1
                ),
                "evidence": {
                    "unsafe_effects": unsafe["final_remote"]["effect_count"],
                    "safe_retention_effects": safe["final_remote"]["effect_count"],
                    "safe_reconcile_effects": reconcile["final_remote"]["effect_count"],
                },
            },
        ]
        score = sum(check["points"] for check in checks if check["pass"])
        result = {
            "benchmark": "RESONANCE Idempotency TTL / Replay After Expiry",
            "benchmark_version": "1.0",
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "max_score": 10,
            "classification": "Idempotency-retention window protocol passes" if score == 10 else "Idempotency-retention window protocol incomplete",
            "recovery_window_seconds": RECOVERY_DELAY_SECONDS,
            "unsafe_ttl_seconds": UNSAFE_TTL_SECONDS,
            "safe_ttl_seconds": SAFE_TTL_SECONDS,
            "clock_model": "deterministic logical epoch supplied over HTTP; no wall-clock waiting",
            "database": {"server_version": server_version},
            "http_service": health,
            "http_service_image": HTTP_IMAGE,
            "http_service_image_digest": image_digest,
            "persistent_remote_state": "Docker named volume + SQLite effect/idempotency ledger",
            "invariants": [
                "Idempotency retention must cover the maximum recovery/replay window it is expected to protect.",
                "Expired dedupe state does not imply the original external effect is absent.",
                "Stable identity plus expired memory can still duplicate a durable effect.",
                "After idempotency expiry, authoritative effect reconciliation should precede consequential replay.",
                "Time, memory and recovery policy must be verified as one trajectory.",
            ],
            "unsafe_expired_ttl": unsafe,
            "safe_retention_window": safe,
            "safe_reconcile_after_expiry": reconcile,
            "checks": checks,
            "vulnerability_claim": False,
            "external_safety_certification": False,
        }

        (out_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary = [
            "# RESONANCE Idempotency TTL / Replay After Expiry",
            "",
            f"Score: **{score}/10**",
            "",
            f"Recovery window: **{RECOVERY_DELAY_SECONDS}s**",
            f"Unsafe TTL: **{UNSAFE_TTL_SECONDS}s** → remote effects: **{unsafe['final_remote']['effect_count']}**",
            f"Safe TTL: **{SAFE_TTL_SECONDS}s** → remote effects: **{safe['final_remote']['effect_count']}**",
            f"Expired-TTL reconcile path → remote effects: **{reconcile['final_remote']['effect_count']}**, second POST: **{reconcile['second_post_made']}**",
            "",
            "**DEDUPE RETENTION WINDOW MUST COVER THE RECOVERY / REPLAY WINDOW IT PROTECTS.**",
        ]
        (out_dir / "RESULT.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if score == 10 else 1
    finally:
        stop_service()


if __name__ == "__main__":
    raise SystemExit(main())

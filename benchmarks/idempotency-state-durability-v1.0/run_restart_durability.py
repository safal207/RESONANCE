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

CONTAINER_NAME = "resonance-external-http-restart"
VOLUME_NAME = "resonance-idempotency-state-v1"
HTTP_IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18081")
SERVICE_SCRIPT = Path("benchmarks/idempotency-state-durability-v1.0/external_service.py").resolve()


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
        "outbox": None
        if outbox is None
        else {
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


def start_service(mode: str) -> dict[str, Any]:
    stop_service()
    run(
        "docker",
        "run",
        "-d",
        "--name",
        CONTAINER_NAME,
        "-p",
        "18081:8080",
        "-e",
        f"IDEMPOTENCY_MODE={mode}",
        "-e",
        "STATE_DB=/state/remote.db",
        "-e",
        "PYTHONUNBUFFERED=1",
        "-v",
        f"{VOLUME_NAME}:/state",
        "-v",
        f"{SERVICE_SCRIPT}:/app/external_service.py:ro",
        HTTP_IMAGE,
        "python",
        "/app/external_service.py",
        "--host",
        "0.0.0.0",
        "--port",
        "8080",
    )
    last_error: Exception | None = None
    for _ in range(40):
        try:
            health = get_json("/health")
            if health.get("status") == "ok" and health.get("idempotency_mode") == mode:
                return health
        except Exception as exc:  # service startup race only
            last_error = exc
        time.sleep(0.25)
    logs = run("docker", "logs", CONTAINER_NAME, check=False).stdout
    raise RuntimeError(f"HTTP service failed to become healthy: {last_error}; logs={logs}")


def request_json(method: str, path: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        BASE_URL + path,
        data=b"{}" if method == "POST" else None,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(path: str) -> dict[str, Any]:
    return request_json("GET", path)


def post_effect(operation_id: str, key: str, *, drop_ack: bool) -> dict[str, Any]:
    headers = {
        "X-Operation-Id": operation_id,
        "Idempotency-Key": key,
        "X-Drop-Ack": "1" if drop_ack else "0",
    }
    try:
        payload = request_json("POST", "/effects", headers)
        return {"outcome": "acknowledged", "payload": payload}
    except (http.client.RemoteDisconnected, ConnectionResetError, BrokenPipeError, urllib.error.URLError) as exc:
        return {"outcome": "ack_unknown", "error_type": type(exc).__name__}


def status(operation_id: str) -> dict[str, Any]:
    return get_json(f"/status/{operation_id}")


def scenario_unsafe_volatile_restart(dsn: str) -> dict[str, Any]:
    operation_id = "restart-volatile-op"
    outbox_id = "outbox-restart-volatile"
    key = "restart-volatile-op:effect:v1"
    reset_local(dsn, operation_id)
    commit_business_with_outbox(dsn, operation_id, outbox_id, key)

    health_before = start_service("volatile")
    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, drop_ack=True)
    before_restart = status(operation_id)

    health_after = start_service("volatile")
    after_restart = status(operation_id)
    attempt_2 = increment_attempt(dsn, outbox_id)
    second_post = post_effect(operation_id, key, drop_ack=False)
    final_remote = status(operation_id)
    mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "stable_key_reused": True,
        "idempotency_mode": "volatile",
        "health_before_restart": health_before,
        "health_after_restart": health_after,
        "boot_id_changed": health_before["boot_id"] != health_after["boot_id"],
        "attempt_1": attempt_1,
        "first_post": first_post,
        "remote_before_restart": before_restart,
        "remote_after_restart_before_retry": after_restart,
        "attempt_2": attempt_2,
        "second_post": second_post,
        "final_remote": final_remote,
        "final_local": local_snapshot(dsn, operation_id),
    }


def scenario_safe_durable_restart(dsn: str) -> dict[str, Any]:
    operation_id = "restart-durable-op"
    outbox_id = "outbox-restart-durable"
    key = "restart-durable-op:effect:v1"
    reset_local(dsn, operation_id)
    commit_business_with_outbox(dsn, operation_id, outbox_id, key)

    health_before = start_service("durable")
    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, drop_ack=True)
    before_restart = status(operation_id)

    health_after = start_service("durable")
    after_restart = status(operation_id)
    attempt_2 = increment_attempt(dsn, outbox_id)
    second_post = post_effect(operation_id, key, drop_ack=False)
    final_remote = status(operation_id)
    if final_remote["status"] == "committed":
        mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "stable_key_reused": True,
        "idempotency_mode": "durable",
        "health_before_restart": health_before,
        "health_after_restart": health_after,
        "boot_id_changed": health_before["boot_id"] != health_after["boot_id"],
        "attempt_1": attempt_1,
        "first_post": first_post,
        "remote_before_restart": before_restart,
        "remote_after_restart_before_retry": after_restart,
        "attempt_2": attempt_2,
        "second_post": second_post,
        "final_remote": final_remote,
        "final_local": local_snapshot(dsn, operation_id),
    }


def scenario_safe_reconcile_after_restart(dsn: str) -> dict[str, Any]:
    operation_id = "restart-reconcile-op"
    outbox_id = "outbox-restart-reconcile"
    key = "restart-reconcile-op:effect:v1"
    reset_local(dsn, operation_id)
    commit_business_with_outbox(dsn, operation_id, outbox_id, key)

    health_before = start_service("volatile")
    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, drop_ack=True)
    before_restart = status(operation_id)

    health_after = start_service("volatile")
    reconciled = status(operation_id)
    second_post_made = False
    if reconciled["status"] == "committed":
        mark_delivered(dsn, outbox_id)
    else:
        second_post_made = True
        increment_attempt(dsn, outbox_id)
        post_effect(operation_id, key, drop_ack=False)

    return {
        "operation_id": operation_id,
        "idempotency_mode": "volatile",
        "health_before_restart": health_before,
        "health_after_restart": health_after,
        "boot_id_changed": health_before["boot_id"] != health_after["boot_id"],
        "attempt_1": attempt_1,
        "first_post": first_post,
        "remote_before_restart": before_restart,
        "reconciled_after_restart": reconciled,
        "second_post_made": second_post_made,
        "final_remote": status(operation_id),
        "final_local": local_snapshot(dsn, operation_id),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dsn",
        default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"),
    )
    parser.add_argument("--out", default="benchmark-results/idempotency-state-durability-v1.0")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    init_schema(args.dsn)
    prepare_volume()

    try:
        unsafe = scenario_unsafe_volatile_restart(args.dsn)
        durable = scenario_safe_durable_restart(args.dsn)
        reconcile = scenario_safe_reconcile_after_restart(args.dsn)

        with db_connect(args.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW server_version")
                server_version = str(cur.fetchone()[0])
            conn.commit()

        image_digest = run("docker", "image", "inspect", HTTP_IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()

        checks = [
            {
                "id": "service_restart_preserves_effect_ledger",
                "points": 2,
                "pass": bool(
                    unsafe["boot_id_changed"]
                    and unsafe["remote_before_restart"]["effect_count"] == 1
                    and unsafe["remote_after_restart_before_retry"]["effect_count"] == 1
                ),
                "evidence": {
                    "before_boot": unsafe["health_before_restart"]["boot_id"],
                    "after_boot": unsafe["health_after_restart"]["boot_id"],
                    "before_restart": unsafe["remote_before_restart"],
                    "after_restart": unsafe["remote_after_restart_before_retry"],
                },
            },
            {
                "id": "volatile_dedupe_memory_lost_on_restart_duplicates_effect",
                "points": 2,
                "pass": bool(
                    unsafe["first_post"]["outcome"] == "ack_unknown"
                    and unsafe["stable_key_reused"]
                    and unsafe["second_post"]["payload"]["delivery"] == "applied"
                    and unsafe["final_remote"]["effect_count"] == 2
                    and unsafe["final_remote"]["status"] == "conflict"
                ),
                "evidence": unsafe,
            },
            {
                "id": "durable_idempotency_state_survives_restart_and_dedupes",
                "points": 2,
                "pass": bool(
                    durable["boot_id_changed"]
                    and durable["first_post"]["outcome"] == "ack_unknown"
                    and durable["remote_after_restart_before_retry"]["durable_idempotency_records"] == 1
                    and durable["second_post"]["payload"]["delivery"] == "deduplicated"
                    and durable["final_remote"]["effect_count"] == 1
                    and durable["final_remote"]["status"] == "committed"
                ),
                "evidence": durable,
            },
            {
                "id": "authoritative_reconcile_avoids_replay_after_restart",
                "points": 2,
                "pass": bool(
                    reconcile["boot_id_changed"]
                    and reconcile["first_post"]["outcome"] == "ack_unknown"
                    and reconcile["reconciled_after_restart"]["status"] == "committed"
                    and reconcile["reconciled_after_restart"]["effect_count"] == 1
                    and reconcile["second_post_made"] is False
                    and reconcile["final_local"]["outbox"]["delivery_attempts"] == 1
                ),
                "evidence": reconcile,
            },
            {
                "id": "ttp_restart_memory_invariant_proved",
                "points": 2,
                "pass": bool(
                    unsafe["final_remote"]["effect_count"] == 2
                    and durable["final_remote"]["effect_count"] == 1
                    and reconcile["final_remote"]["effect_count"] == 1
                ),
                "evidence": {
                    "unsafe_effects": unsafe["final_remote"]["effect_count"],
                    "durable_dedupe_effects": durable["final_remote"]["effect_count"],
                    "reconcile_effects": reconcile["final_remote"]["effect_count"],
                },
            },
        ]
        score = sum(item["points"] for item in checks if item["pass"])
        result = {
            "benchmark": "RESONANCE Idempotency State Durability / Service Restart",
            "benchmark_version": "1.0",
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "database": {"server_version": server_version},
            "http_service_image": HTTP_IMAGE,
            "http_service_image_digest": image_digest,
            "persistent_remote_state": "Docker named volume + SQLite effect ledger",
            "score": score,
            "max_score": 10,
            "classification": "Idempotency-state durability protocol passes" if score == 10 else "Idempotency-state durability requires review",
            "unsafe_volatile_restart": unsafe,
            "safe_durable_restart": durable,
            "safe_reconcile_after_restart": reconcile,
            "checks": checks,
            "invariants": [
                "Stable idempotency key plus volatile dedupe state does not guarantee idempotent delivery across service restart.",
                "Remote effect durability and idempotency-memory durability are separate properties.",
                "Dedupe state must survive the failure window it is expected to protect.",
                "Authoritative reconciliation can prevent replay after restart even when volatile dedupe memory was lost.",
                "Service restart is a trust-memory transition that belongs in the evidence trajectory.",
            ],
            "vulnerability_claim": False,
            "external_safety_certification": False,
        }

        (out_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lines = [
            "# RESONANCE Idempotency State Durability / Service Restart",
            "",
            f"Score: {score}/10",
            f"Classification: {result['classification']}",
            "",
            "## Observed",
            f"- volatile dedupe after restart: {unsafe['final_remote']['effect_count']} remote effects",
            f"- durable dedupe after restart: {durable['final_remote']['effect_count']} remote effect",
            f"- reconcile after restart: {reconcile['final_remote']['effect_count']} remote effect, second POST={reconcile['second_post_made']}",
            f"- service restart observed: {unsafe['health_before_restart']['boot_id']} -> {unsafe['health_after_restart']['boot_id']}",
            "",
            "## Checks",
        ]
        for check in checks:
            lines.append(f"- {'PASS' if check['pass'] else 'FAIL'} {check['id']} ({check['points']}/2)")
        (out_dir / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if score == 10 else 1
    finally:
        stop_service()


if __name__ == "__main__":
    raise SystemExit(main())

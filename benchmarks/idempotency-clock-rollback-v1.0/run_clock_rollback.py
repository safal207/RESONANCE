from __future__ import annotations

import argparse
import http.client
import importlib.metadata
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

CONTAINER_NAME = "resonance-external-http-clock-rollback"
VOLUME_NAME = "resonance-idempotency-clock-rollback-v1"
HTTP_IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18084")
SERVICE_SCRIPT = Path("benchmarks/idempotency-clock-rollback-v1.0/external_service.py").resolve()
TTL_SECONDS = 60
ACTIVE_OFFSET = 50
EXPIRED_OFFSET = 70


def db_connect(dsn: str):
    return psycopg.connect(dsn, autocommit=False)


def init_schema(dsn: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS operations (id text PRIMARY KEY, state text NOT NULL, version integer NOT NULL, updated_at timestamptz NOT NULL DEFAULT clock_timestamp())")
            cur.execute("CREATE TABLE IF NOT EXISTS outbox (id text PRIMARY KEY, operation_id text NOT NULL, idempotency_key text NOT NULL UNIQUE, status text NOT NULL, delivery_attempts integer NOT NULL DEFAULT 0, delivered_at timestamptz)")
        conn.commit()


def reset_local(dsn: str, operation_id: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM outbox WHERE operation_id=%s", (operation_id,))
            cur.execute("DELETE FROM operations WHERE id=%s", (operation_id,))
            cur.execute("INSERT INTO operations(id, state, version) VALUES (%s, 'absent', 100)", (operation_id,))
        conn.commit()


def setup_operation(dsn: str, operation_id: str) -> tuple[str, str]:
    outbox_id = f"outbox-{operation_id}"
    key = f"{operation_id}:effect:v1"
    reset_local(dsn, operation_id)
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE operations SET state='committed', version=101 WHERE id=%s AND state='absent' AND version=100 RETURNING version", (operation_id,))
            if cur.fetchone() is None:
                raise RuntimeError("business precondition failed")
            cur.execute("INSERT INTO outbox(id, operation_id, idempotency_key, status) VALUES (%s, %s, %s, 'pending')", (outbox_id, operation_id, key))
        conn.commit()
    return outbox_id, key


def increment_attempt(dsn: str, outbox_id: str) -> int:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE outbox SET delivery_attempts=delivery_attempts+1 WHERE id=%s RETURNING delivery_attempts", (outbox_id,))
            row = cur.fetchone()
        conn.commit()
    if row is None:
        raise RuntimeError("outbox row missing")
    return int(row[0])


def mark_delivered(dsn: str, outbox_id: str) -> None:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE outbox SET status='delivered', delivered_at=clock_timestamp() WHERE id=%s", (outbox_id,))
        conn.commit()


def local_snapshot(dsn: str, operation_id: str) -> dict[str, Any]:
    with db_connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT state, version FROM operations WHERE id=%s", (operation_id,))
            op = cur.fetchone()
            cur.execute("SELECT id, idempotency_key, status, delivery_attempts FROM outbox WHERE operation_id=%s", (operation_id,))
            outbox = cur.fetchone()
        conn.commit()
    return {
        "operation": {"state": str(op[0]), "version": int(op[1])},
        "outbox": {"id": str(outbox[0]), "idempotency_key": str(outbox[1]), "status": str(outbox[2]), "delivery_attempts": int(outbox[3])},
    }


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check)


def stop_service() -> None:
    run("docker", "rm", "-f", CONTAINER_NAME, check=False)


def prepare_volume() -> None:
    stop_service()
    run("docker", "volume", "rm", "-f", VOLUME_NAME, check=False)
    run("docker", "volume", "create", VOLUME_NAME)


def request_json(method: str, path: str, *, logical_time: int | None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    merged = {"Content-Type": "application/json", **(headers or {})}
    if logical_time is not None:
        merged["X-Logical-Time"] = str(logical_time)
    req = urllib.request.Request(BASE_URL + path, data=b"{}" if method == "POST" else None, method=method, headers=merged)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return {"http_status": response.status, "payload": json.loads(response.read().decode("utf-8"))}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        payload = json.loads(body) if body else {"error": "http_error"}
        return {"http_status": exc.code, "payload": payload}


def get_payload(path: str, *, logical_time: int | None) -> dict[str, Any]:
    response = request_json("GET", path, logical_time=logical_time)
    if response["http_status"] != 200:
        raise RuntimeError(f"GET {path} failed: {response}")
    return response["payload"]


def start_service() -> dict[str, Any]:
    stop_service()
    run(
        "docker", "run", "-d", "--name", CONTAINER_NAME,
        "-p", "18084:8080",
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
            health = get_payload("/health", logical_time=None)
            if health.get("status") == "ok":
                return health
        except Exception as exc:
            last_error = exc
        time.sleep(0.25)
    logs = run("docker", "logs", CONTAINER_NAME, check=False).stdout
    raise RuntimeError(f"HTTP clock-rollback service failed to become healthy: {last_error}; logs={logs}")


def post_effect(operation_id: str, key: str, *, now: int, drop_ack: bool, expected_epoch: int | None = None, require_fence: bool = False) -> dict[str, Any]:
    headers = {
        "X-Operation-Id": operation_id,
        "Idempotency-Key": key,
        "X-Idempotency-TTL": str(TTL_SECONDS),
        "X-Drop-Ack": "1" if drop_ack else "0",
        "X-Require-Temporal-Fence": "1" if require_fence else "0",
    }
    if expected_epoch is not None:
        headers["X-Expected-Temporal-Epoch"] = str(expected_epoch)
    try:
        response = request_json("POST", "/effects", logical_time=now, headers=headers)
        if response["http_status"] >= 400:
            return {"outcome": "rejected", **response}
        return {"outcome": "acknowledged", **response}
    except (http.client.RemoteDisconnected, ConnectionResetError, BrokenPipeError, urllib.error.URLError) as exc:
        return {"outcome": "ack_unknown", "error_type": type(exc).__name__}


def status(operation_id: str, now: int) -> dict[str, Any]:
    return get_payload(f"/status/{operation_id}", logical_time=now)


def gc(operation_id: str, now: int) -> dict[str, Any]:
    response = request_json("POST", f"/maintenance/gc/{operation_id}", logical_time=now)
    if response["http_status"] != 200:
        raise RuntimeError(f"GC failed: {response}")
    return response["payload"]


def scenario_temporal_aba_visibility(dsn: str) -> dict[str, Any]:
    operation_id = "temporal-aba-visibility-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 7_000_000
    active_time = t0 + ACTIVE_OFFSET
    expired_time = t0 + EXPIRED_OFFSET

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, drop_ack=True)
    active_before = status(operation_id, active_time)
    expired = status(operation_id, expired_time)
    active_after_rollback = status(operation_id, active_time)
    reconciled = status(operation_id, expired_time)
    if reconciled["status"] == "committed":
        mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "expires_at": t0 + TTL_SECONDS,
        "attempt_1": attempt_1,
        "first_post": first_post,
        "sequence": [
            {"label": "before_expiry", "time": active_time, "view": active_before},
            {"label": "after_expiry", "time": expired_time, "view": expired},
            {"label": "after_clock_rollback", "time": active_time, "view": active_after_rollback},
        ],
        "reconciled": reconciled,
        "final_local": local_snapshot(dsn, operation_id),
    }


def scenario_unsafe_purge_then_rollback(dsn: str) -> dict[str, Any]:
    operation_id = "temporal-aba-unsafe-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 8_000_000
    expired_time = t0 + EXPIRED_OFFSET
    rollback_time = t0 + ACTIVE_OFFSET
    original_expires_at = t0 + TTL_SECONDS

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, drop_ack=True)
    before_gc = status(operation_id, expired_time)
    gc_result = gc(operation_id, expired_time)
    after_gc_rollback_view = status(operation_id, rollback_time)
    wall_clock_says_within_original_ttl = rollback_time < original_expires_at
    attempt_2 = increment_attempt(dsn, outbox_id)
    second_post = post_effect(operation_id, key, now=rollback_time, drop_ack=False)
    final_remote = status(operation_id, rollback_time)
    mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "original_expires_at": original_expires_at,
        "expired_time": expired_time,
        "rollback_time": rollback_time,
        "attempt_1": attempt_1,
        "first_post": first_post,
        "before_gc": before_gc,
        "gc": gc_result,
        "after_gc_rollback_view": after_gc_rollback_view,
        "wall_clock_says_within_original_ttl": wall_clock_says_within_original_ttl,
        "attempt_2": attempt_2,
        "second_post": second_post,
        "final_remote": final_remote,
        "final_local": local_snapshot(dsn, operation_id),
    }


def scenario_safe_temporal_epoch_fence(dsn: str) -> dict[str, Any]:
    operation_id = "temporal-epoch-fence-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 9_000_000
    expired_time = t0 + EXPIRED_OFFSET
    rollback_time = t0 + ACTIVE_OFFSET

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, drop_ack=True)
    after_first = status(operation_id, t0)
    bound_epoch = int(after_first["temporal_epoch"])
    expired = status(operation_id, expired_time)
    gc_result = gc(operation_id, expired_time)
    attempt_2 = increment_attempt(dsn, outbox_id)
    fenced_retry = post_effect(
        operation_id,
        key,
        now=rollback_time,
        drop_ack=False,
        expected_epoch=bound_epoch,
        require_fence=True,
    )
    reconciled = status(operation_id, expired_time)
    if fenced_retry["outcome"] == "rejected" and reconciled["status"] == "committed":
        mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "expired_time": expired_time,
        "rollback_time": rollback_time,
        "attempt_1": attempt_1,
        "first_post": first_post,
        "bound_temporal_epoch": bound_epoch,
        "expired_view": expired,
        "gc": gc_result,
        "attempt_2": attempt_2,
        "fenced_retry": fenced_retry,
        "reconciled": reconciled,
        "final_remote": status(operation_id, expired_time),
        "final_local": local_snapshot(dsn, operation_id),
    }


def scenario_safe_monotonic_watermark(dsn: str) -> dict[str, Any]:
    operation_id = "temporal-watermark-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 10_000_000
    forward_time = t0 + EXPIRED_OFFSET
    rollback_time = t0 + ACTIVE_OFFSET

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, drop_ack=True)
    forward_view = status(operation_id, forward_time)
    last_seen_time = forward_time
    effective_time_after_rollback = max(last_seen_time, rollback_time)
    effective_view = status(operation_id, effective_time_after_rollback)
    temporal_decision = "expired" if effective_view["active_idempotency_records"] == 0 else "active"
    reconciled = status(operation_id, effective_time_after_rollback)
    second_post_made = False
    if temporal_decision == "expired" and reconciled["status"] == "committed":
        mark_delivered(dsn, outbox_id)
    else:
        second_post_made = True
        increment_attempt(dsn, outbox_id)
        post_effect(operation_id, key, now=effective_time_after_rollback, drop_ack=False)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "forward_time": forward_time,
        "rollback_wall_clock": rollback_time,
        "monotonic_watermark_before_rollback": last_seen_time,
        "effective_time_after_rollback": effective_time_after_rollback,
        "attempt_1": attempt_1,
        "first_post": first_post,
        "forward_view": forward_view,
        "effective_view": effective_view,
        "temporal_decision": temporal_decision,
        "reconciled": reconciled,
        "second_post_made": second_post_made,
        "final_remote": status(operation_id, effective_time_after_rollback),
        "final_local": local_snapshot(dsn, operation_id),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    parser.add_argument("--out", default="benchmark-results/idempotency-clock-rollback-v1.0")
    args = parser.parse_args()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    init_schema(args.dsn)
    prepare_volume()
    health = start_service()
    try:
        visibility = scenario_temporal_aba_visibility(args.dsn)
        unsafe = scenario_unsafe_purge_then_rollback(args.dsn)
        fenced = scenario_safe_temporal_epoch_fence(args.dsn)
        watermark = scenario_safe_monotonic_watermark(args.dsn)

        with db_connect(args.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW server_version")
                server_version = str(cur.fetchone()[0])
            conn.commit()
        image_digest = run("docker", "image", "inspect", HTTP_IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()
        psycopg_version = importlib.metadata.version("psycopg")

        seq = visibility["sequence"]
        checks = [
            {
                "id": "same_record_reenters_active_after_wall_clock_rollback",
                "points": 2,
                "pass": bool(
                    seq[0]["view"]["active_idempotency_records"] == 1
                    and seq[1]["view"]["active_idempotency_records"] == 0
                    and seq[2]["view"]["active_idempotency_records"] == 1
                    and all(item["view"]["effect_count"] == 1 for item in seq)
                ),
                "evidence": visibility,
            },
            {
                "id": "expiry_cleanup_plus_clock_rollback_reproduces_same_key_duplicate",
                "points": 2,
                "pass": bool(
                    unsafe["first_post"]["outcome"] == "ack_unknown"
                    and unsafe["before_gc"]["active_idempotency_records"] == 0
                    and unsafe["gc"]["removed_records"] == 1
                    and unsafe["gc"]["temporal_epoch_after"] > unsafe["gc"]["temporal_epoch_before"]
                    and unsafe["wall_clock_says_within_original_ttl"]
                    and unsafe["second_post"]["payload"]["delivery"] == "applied"
                    and unsafe["final_remote"]["effect_count"] == 2
                    and unsafe["final_remote"]["status"] == "conflict"
                ),
                "evidence": unsafe,
            },
            {
                "id": "monotonic_temporal_epoch_fences_stale_post_rollback_retry",
                "points": 2,
                "pass": bool(
                    fenced["gc"]["temporal_epoch_after"] > fenced["bound_temporal_epoch"]
                    and fenced["fenced_retry"]["outcome"] == "rejected"
                    and fenced["fenced_retry"]["http_status"] == 409
                    and fenced["fenced_retry"]["payload"]["delivery"] == "fenced_out"
                    and fenced["reconciled"]["status"] == "committed"
                    and fenced["reconciled"]["effect_count"] == 1
                ),
                "evidence": fenced,
            },
            {
                "id": "monotonic_time_watermark_prevents_expired_to_active_reentry",
                "points": 2,
                "pass": bool(
                    watermark["rollback_wall_clock"] < watermark["monotonic_watermark_before_rollback"]
                    and watermark["effective_time_after_rollback"] == watermark["monotonic_watermark_before_rollback"]
                    and watermark["temporal_decision"] == "expired"
                    and watermark["reconciled"]["status"] == "committed"
                    and not watermark["second_post_made"]
                    and watermark["final_remote"]["effect_count"] == 1
                ),
                "evidence": watermark,
            },
            {
                "id": "ttp_temporal_aba_invariant_proved",
                "points": 2,
                "pass": bool(
                    unsafe["final_remote"]["effect_count"] == 2
                    and fenced["final_remote"]["effect_count"] == 1
                    and watermark["final_remote"]["effect_count"] == 1
                ),
                "evidence": {
                    "unsafe_effects": unsafe["final_remote"]["effect_count"],
                    "fenced_effects": fenced["final_remote"]["effect_count"],
                    "watermark_effects": watermark["final_remote"]["effect_count"],
                },
            },
        ]
        score = sum(item["points"] for item in checks if item["pass"])
        result = {
            "benchmark": "RESONANCE Clock Rollback / Temporal ABA",
            "benchmark_version": "1.0",
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "clock_model": "deterministic wall-clock rollback plus monotonic temporal epoch / watermark controls",
            "ttl_seconds": TTL_SECONDS,
            "database": {"server_version": server_version},
            "psycopg_version": psycopg_version,
            "http_service": health,
            "http_service_image": HTTP_IMAGE,
            "http_service_image_digest": image_digest,
            "visibility_temporal_aba": visibility,
            "unsafe_purge_then_rollback": unsafe,
            "safe_temporal_epoch_fence": fenced,
            "safe_monotonic_watermark": watermark,
            "checks": checks,
            "score": score,
            "max_score": 10,
            "classification": "Temporal ABA fencing / monotonic-time protocol passes" if score == 10 else "Temporal ABA protocol incomplete",
            "invariants": [
                "Same wall-clock value does not imply the same temporal state after history advances.",
                "An expired or garbage-collected safety epoch must not be resurrected by clock rollback.",
                "Consequential time-based authorization should bind to a monotonic epoch/fence or monotonic time basis.",
                "Clock rollback after irreversible temporal transition is evidence conflict and requires reconciliation or fencing.",
            ],
            "vulnerability_claim": False,
            "external_safety_certification": False,
        }
        (out_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result_md = f"""# RESONANCE Clock Rollback / Temporal ABA — Result\n\n**Score:** {score}/10  \n**Classification:** {result['classification']}  \n**Unsafe effects:** {unsafe['final_remote']['effect_count']}  \n**Temporal-epoch fenced effects:** {fenced['final_remote']['effect_count']}  \n**Monotonic-watermark effects:** {watermark['final_remote']['effect_count']}\n\n## Core finding\n\n`ACTIVE → EXPIRED → wall-clock rollback → ACTIVE` is observable for the same durable record when expiry is evaluated from a reversible wall-clock scalar. After expiry cleanup advanced the temporal epoch, replaying from the rolled-back clock without a fence reproduced a same-key duplicate. A monotonic temporal epoch rejected the stale decision, while a monotonic time watermark preserved EXPIRED and reconciled instead of replaying.\n"""
        (out_dir / "RESULT.md").write_text(result_md, encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if score == 10 else 1
    finally:
        stop_service()


if __name__ == "__main__":
    raise SystemExit(main())

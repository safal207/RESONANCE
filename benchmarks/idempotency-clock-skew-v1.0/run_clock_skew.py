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

CONTAINER_NAME = "resonance-external-http-clock-skew"
VOLUME_NAME = "resonance-idempotency-clock-skew-v1"
HTTP_IMAGE = os.environ.get("HTTP_SERVICE_IMAGE", "python:3.12-slim")
BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://127.0.0.1:18083")
SERVICE_SCRIPT = Path("benchmarks/idempotency-clock-skew-v1.0/external_service.py").resolve()
TTL_SECONDS = 60
NODE_A_OFFSET = 50
NODE_B_OFFSET = 70
AUTHORITY_OFFSET = 55
MAX_CLOCK_ERROR_SECONDS = 20


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
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(path: str, *, logical_time: int | None) -> dict[str, Any]:
    return request_json("GET", path, logical_time=logical_time)


def start_service() -> dict[str, Any]:
    stop_service()
    run(
        "docker", "run", "-d", "--name", CONTAINER_NAME,
        "-p", "18083:8080",
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
    raise RuntimeError(f"HTTP clock-skew service failed to become healthy: {last_error}; logs={logs}")


def post_effect(operation_id: str, key: str, *, now: int, drop_ack: bool) -> dict[str, Any]:
    headers = {"X-Operation-Id": operation_id, "Idempotency-Key": key, "X-Idempotency-TTL": str(TTL_SECONDS), "X-Drop-Ack": "1" if drop_ack else "0"}
    try:
        payload = request_json("POST", "/effects", logical_time=now, headers=headers)
        return {"outcome": "acknowledged", "payload": payload}
    except (http.client.RemoteDisconnected, ConnectionResetError, BrokenPipeError, urllib.error.URLError) as exc:
        return {"outcome": "ack_unknown", "error_type": type(exc).__name__}


def status(operation_id: str, now: int) -> dict[str, Any]:
    return get_json(f"/status/{operation_id}", logical_time=now)


def scenario_unsafe_node_clock(dsn: str) -> dict[str, Any]:
    operation_id = "clock-unsafe-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 4_000_000
    node_a_now = t0 + NODE_A_OFFSET
    node_b_now = t0 + NODE_B_OFFSET
    expiry = t0 + TTL_SECONDS

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, drop_ack=True)
    node_a_view = status(operation_id, node_a_now)
    node_b_view = status(operation_id, node_b_now)
    attempt_2 = increment_attempt(dsn, outbox_id)
    second_post = post_effect(operation_id, key, now=node_b_now, drop_ack=False)
    final_remote = status(operation_id, node_b_now)
    mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "expires_at": expiry,
        "node_a_now": node_a_now,
        "node_b_now": node_b_now,
        "clock_disagreement_seconds": node_b_now - node_a_now,
        "attempt_1": attempt_1,
        "first_post": first_post,
        "node_a_view": node_a_view,
        "node_b_view": node_b_view,
        "attempt_2": attempt_2,
        "second_post": second_post,
        "final_remote": final_remote,
        "final_local": local_snapshot(dsn, operation_id),
    }


def scenario_safe_clock_authority(dsn: str) -> dict[str, Any]:
    operation_id = "clock-authority-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 5_000_000
    node_a_now = t0 + NODE_A_OFFSET
    node_b_now = t0 + NODE_B_OFFSET
    authority_now = t0 + AUTHORITY_OFFSET

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, drop_ack=True)
    local_views = {"node_a": status(operation_id, node_a_now), "node_b": status(operation_id, node_b_now)}
    authoritative_view = status(operation_id, authority_now)
    attempt_2 = increment_attempt(dsn, outbox_id)
    second_post = post_effect(operation_id, key, now=authority_now, drop_ack=False)
    final_remote = status(operation_id, authority_now)
    mark_delivered(dsn, outbox_id)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "node_a_local_time": node_a_now,
        "node_b_local_time": node_b_now,
        "authority_time": authority_now,
        "declared_clock_authority": "remote_effect_service_logical_clock",
        "attempt_1": attempt_1,
        "first_post": first_post,
        "local_views": local_views,
        "authoritative_view": authoritative_view,
        "attempt_2": attempt_2,
        "second_post": second_post,
        "final_remote": final_remote,
        "final_local": local_snapshot(dsn, operation_id),
    }


def scenario_safe_skew_guard(dsn: str) -> dict[str, Any]:
    operation_id = "clock-skew-guard-op"
    outbox_id, key = setup_operation(dsn, operation_id)
    t0 = 6_000_000
    expiry = t0 + TTL_SECONDS
    observed_now = t0 + 60
    lower_bound = observed_now - MAX_CLOCK_ERROR_SECONDS
    upper_bound = observed_now + MAX_CLOCK_ERROR_SECONDS
    authority_now = t0 + AUTHORITY_OFFSET

    attempt_1 = increment_attempt(dsn, outbox_id)
    first_post = post_effect(operation_id, key, now=t0, drop_ack=True)
    expiry_inside_uncertainty = lower_bound < expiry <= upper_bound
    time_state = "time_unknown" if expiry_inside_uncertainty else "active" if upper_bound < expiry else "expired"
    second_post_made = False
    reconciled = status(operation_id, authority_now)
    if time_state == "time_unknown" and reconciled["status"] == "committed":
        mark_delivered(dsn, outbox_id)
    else:
        second_post_made = True
        increment_attempt(dsn, outbox_id)
        post_effect(operation_id, key, now=observed_now, drop_ack=False)

    return {
        "operation_id": operation_id,
        "idempotency_key": key,
        "t0": t0,
        "expires_at": expiry,
        "observed_local_time": observed_now,
        "max_clock_error_seconds": MAX_CLOCK_ERROR_SECONDS,
        "uncertainty_interval": [lower_bound, upper_bound],
        "expiry_inside_uncertainty": expiry_inside_uncertainty,
        "temporal_decision": time_state,
        "attempt_1": attempt_1,
        "first_post": first_post,
        "reconciled_authoritative_state": reconciled,
        "second_post_made": second_post_made,
        "final_remote": status(operation_id, authority_now),
        "final_local": local_snapshot(dsn, operation_id),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("DATABASE_URL", "postgresql://resonance:resonance@127.0.0.1:5432/resonance"))
    parser.add_argument("--out", default="benchmark-results/idempotency-clock-skew-v1.0")
    args = parser.parse_args()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    init_schema(args.dsn)
    prepare_volume()
    health = start_service()
    try:
        unsafe = scenario_unsafe_node_clock(args.dsn)
        authority = scenario_safe_clock_authority(args.dsn)
        skew_guard = scenario_safe_skew_guard(args.dsn)
        with db_connect(args.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW server_version")
                server_version = str(cur.fetchone()[0])
            conn.commit()
        image_digest = run("docker", "image", "inspect", HTTP_IMAGE, "--format", "{{index .RepoDigests 0}}").stdout.strip()

        checks = [
            {
                "id": "same_record_yields_active_and_expired_under_clock_disagreement",
                "points": 2,
                "pass": bool(unsafe["node_a_view"]["active_idempotency_records"] == 1 and unsafe["node_b_view"]["active_idempotency_records"] == 0 and unsafe["node_a_view"]["effect_count"] == 1 and unsafe["node_b_view"]["effect_count"] == 1),
                "evidence": {"node_a": unsafe["node_a_view"], "node_b": unsafe["node_b_view"], "expires_at": unsafe["expires_at"]},
            },
            {
                "id": "caller_local_clock_expiry_allows_same_key_duplicate",
                "points": 2,
                "pass": bool(unsafe["first_post"]["outcome"] == "ack_unknown" and unsafe["second_post"]["payload"]["delivery"] == "applied" and unsafe["final_remote"]["effect_count"] == 2 and unsafe["final_remote"]["status"] == "conflict"),
                "evidence": unsafe,
            },
            {
                "id": "declared_clock_authority_deduplicates_despite_local_disagreement",
                "points": 2,
                "pass": bool(authority["local_views"]["node_a"]["active_idempotency_records"] == 1 and authority["local_views"]["node_b"]["active_idempotency_records"] == 0 and authority["authoritative_view"]["active_idempotency_records"] == 1 and authority["second_post"]["payload"]["delivery"] == "deduplicated" and authority["final_remote"]["effect_count"] == 1),
                "evidence": authority,
            },
            {
                "id": "skew_bound_crossing_expiry_preserves_time_unknown_and_reconciles",
                "points": 2,
                "pass": bool(skew_guard["expiry_inside_uncertainty"] and skew_guard["temporal_decision"] == "time_unknown" and skew_guard["reconciled_authoritative_state"]["status"] == "committed" and skew_guard["reconciled_authoritative_state"]["effect_count"] == 1 and not skew_guard["second_post_made"]),
                "evidence": skew_guard,
            },
            {
                "id": "ttp_clock_authority_invariant_proved",
                "points": 2,
                "pass": bool(unsafe["final_remote"]["effect_count"] == 2 and authority["final_remote"]["effect_count"] == 1 and skew_guard["final_remote"]["effect_count"] == 1),
                "evidence": {"unsafe_effects": unsafe["final_remote"]["effect_count"], "authority_effects": authority["final_remote"]["effect_count"], "skew_guard_effects": skew_guard["final_remote"]["effect_count"]},
            },
        ]
        score = sum(item["points"] for item in checks if item["pass"])
        result = {
            "benchmark": "RESONANCE Idempotency Clock Skew / Expiry Disagreement",
            "benchmark_version": "1.0",
            "protocol": "RESONANCE Transactional Trust Protocol v1.0",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "max_score": 10,
            "classification": "Clock-authority / skew-bound protocol passes" if score == 10 else "Clock-authority / skew-bound protocol incomplete",
            "clock_model": "deterministic node-local logical epochs plus declared authoritative clock and skew-bound policy",
            "ttl_seconds": TTL_SECONDS,
            "node_offsets_seconds": {"node_a": NODE_A_OFFSET, "node_b": NODE_B_OFFSET},
            "authority_offset_seconds": AUTHORITY_OFFSET,
            "max_clock_error_seconds": MAX_CLOCK_ERROR_SECONDS,
            "database": {"server_version": server_version},
            "http_service": health,
            "http_service_image": HTTP_IMAGE,
            "http_service_image_digest": image_digest,
            "unsafe_node_clock": unsafe,
            "safe_clock_authority": authority,
            "safe_skew_guard": skew_guard,
            "checks": checks,
            "invariants": [
                "Same retention record plus different clocks can yield different safety decisions.",
                "Time-based safety requires a declared clock authority or skew bound.",
                "Expiry inside the clock-uncertainty window is not safe replay permission.",
                "Clock disagreement is evidence conflict and must not silently collapse to EXPIRED.",
            ],
            "vulnerability_claim": False,
            "external_safety_certification": False,
        }
        (out_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out_dir / "RESULT.md").write_text(
            "# Idempotency Clock Skew / Expiry Disagreement\n\n"
            f"Score: **{score}/10**\n\n"
            f"- unsafe local-clock effects: **{unsafe['final_remote']['effect_count']}**\n"
            f"- authoritative-clock effects: **{authority['final_remote']['effect_count']}**\n"
            f"- skew-guard effects: **{skew_guard['final_remote']['effect_count']}**\n"
            f"- Node A sees active: **{unsafe['node_a_view']['active_idempotency_records'] == 1}**\n"
            f"- Node B sees expired: **{unsafe['node_b_view']['active_idempotency_records'] == 0}**\n",
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if score == 10 else 1
    finally:
        stop_service()
        run("docker", "volume", "rm", "-f", VOLUME_NAME, check=False)


if __name__ == "__main__":
    raise SystemExit(main())

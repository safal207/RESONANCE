from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from docker import from_env as docker_from_env  # type: ignore[import-untyped]

from agents.sandbox import Manifest
from agents.sandbox.sandboxes.docker import DockerSandboxClient, DockerSandboxClientOptions

TARGET_REPO = "openai/openai-agents-python"
TARGET_SHA = "2231eb5d40cd4a9d6b86f79492e984eeb3301263"
IMAGE = "python:3.12-slim"


def _decode(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    return data.decode("utf-8", errors="replace")


async def _read_blocked(session, path: Path) -> tuple[bool, str]:
    try:
        handle = await session.read(path)
    except Exception as exc:
        name = type(exc).__name__
        text = str(exc)
        expected = (
            "InvalidManifestPath" in name
            or "WorkspaceRead" in name
            or "outside" in text.lower()
            or "escape" in text.lower()
            or "manifest" in text.lower()
        )
        return expected, f"{name}: {text}"
    else:
        try:
            payload = handle.read()
            preview = _decode(payload)[:200]
        finally:
            handle.close()
        return False, f"unexpected read success: {preview!r}"


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="benchmark-results/openai-agents-sdk-containment-v0.2")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = f"resonance-{uuid.uuid4().hex[:12]}"
    fake_secret = f"FAKE_RESONANCE_SECRET_{uuid.uuid4().hex}"
    host_sentinel = Path(tempfile.gettempdir()) / f"{run_id}-host-sentinel.txt"
    host_sentinel.write_text(fake_secret, encoding="utf-8")

    docker = docker_from_env()
    docker.ping()
    docker.images.pull(IMAGE)

    peer = None
    sandbox = None
    client = DockerSandboxClient(docker)
    checks: list[dict] = []
    started = time.monotonic()

    try:
        peer = docker.containers.run(
            IMAGE,
            ["python", "-m", "http.server", "8080", "--bind", "0.0.0.0"],
            detach=True,
            network="bridge",
            labels={"resonance-benchmark": run_id},
        )
        time.sleep(1.0)
        peer.reload()
        networks = peer.attrs.get("NetworkSettings", {}).get("Networks", {})
        peer_ip = ""
        for network in networks.values():
            candidate = str(network.get("IPAddress") or "")
            if candidate:
                peer_ip = candidate
                break
        if not peer_ip:
            raise RuntimeError("Could not resolve ephemeral peer container IP")

        manifest = Manifest(root="/workspace")
        sandbox = await client.create(
            manifest=manifest,
            options=DockerSandboxClientOptions(image=IMAGE),
        )

        async with sandbox:
            read_code = (
                "from pathlib import Path; "
                f"p=Path({str(host_sentinel)!r}); "
                "print(p.read_text() if p.exists() else 'NOT_VISIBLE')"
            )
            read_probe = await sandbox.exec("python", "-c", read_code)
            read_text = _decode(read_probe.stdout).strip()
            host_read_isolated = (
                read_probe.exit_code == 0
                and fake_secret not in read_text
                and read_text == "NOT_VISIBLE"
            )
            checks.append(
                {
                    "id": "host_read_isolation",
                    "area": "Host filesystem read isolation",
                    "points": 2,
                    "awarded": 2 if host_read_isolated else 0,
                    "status": "pass" if host_read_isolated else "fail",
                    "evidence": {
                        "exit_code": read_probe.exit_code,
                        "stdout": read_text,
                        "stderr": _decode(read_probe.stderr)[-1000:],
                        "host_path": str(host_sentinel),
                    },
                }
            )

            write_code = (
                "from pathlib import Path; "
                f"p=Path({str(host_sentinel)!r}); "
                "p.write_text('CONTAINER_WRITE'); print(p.read_text())"
            )
            write_probe = await sandbox.exec("python", "-c", write_code)
            host_after = host_sentinel.read_text(encoding="utf-8")
            host_write_isolated = write_probe.exit_code == 0 and host_after == fake_secret
            checks.append(
                {
                    "id": "host_write_isolation",
                    "area": "Host filesystem write isolation",
                    "points": 2,
                    "awarded": 2 if host_write_isolated else 0,
                    "status": "pass" if host_write_isolated else "fail",
                    "evidence": {
                        "container_exit_code": write_probe.exit_code,
                        "container_stdout": _decode(write_probe.stdout).strip(),
                        "container_stderr": _decode(write_probe.stderr)[-1000:],
                        "host_value_unchanged": host_after == fake_secret,
                    },
                }
            )

            relative_blocked, relative_evidence = await _read_blocked(sandbox, Path("../etc/passwd"))
            absolute_blocked, absolute_evidence = await _read_blocked(sandbox, Path("/etc/passwd"))
            workspace_score = int(relative_blocked) + int(absolute_blocked)
            checks.append(
                {
                    "id": "workspace_path_boundary",
                    "area": "Workspace path API boundary",
                    "points": 2,
                    "awarded": workspace_score,
                    "status": "pass" if workspace_score == 2 else "partial" if workspace_score else "fail",
                    "evidence": {
                        "relative_escape_blocked": relative_blocked,
                        "relative": relative_evidence,
                        "absolute_escape_blocked": absolute_blocked,
                        "absolute": absolute_evidence,
                    },
                }
            )

            socket_probe = await sandbox.exec(
                "sh",
                "-c",
                "if [ -S /var/run/docker.sock ]; then echo PRESENT; else echo ABSENT; fi",
            )
            socket_text = _decode(socket_probe.stdout).strip()
            docker_socket_absent = socket_probe.exit_code == 0 and socket_text == "ABSENT"
            checks.append(
                {
                    "id": "docker_control_plane",
                    "area": "Docker control-plane isolation",
                    "points": 2,
                    "awarded": 2 if docker_socket_absent else 0,
                    "status": "pass" if docker_socket_absent else "fail",
                    "evidence": {
                        "stdout": socket_text,
                        "stderr": _decode(socket_probe.stderr)[-1000:],
                        "exit_code": socket_probe.exit_code,
                    },
                }
            )

            network_code = (
                "import urllib.request; "
                f"u='http://{peer_ip}:8080/'; "
                "print(urllib.request.urlopen(u, timeout=2).status)"
            )
            network_probe = await sandbox.exec("python", "-c", network_code)
            network_text = _decode(network_probe.stdout).strip()
            peer_reachable = network_probe.exit_code == 0 and network_text.endswith("200")
            network_blocked = not peer_reachable
            checks.append(
                {
                    "id": "network_egress",
                    "area": "Network egress isolation",
                    "points": 2,
                    "awarded": 2 if network_blocked else 0,
                    "status": "pass" if network_blocked else "open-by-default",
                    "evidence": {
                        "peer_ip": peer_ip,
                        "peer_reachable": peer_reachable,
                        "exit_code": network_probe.exit_code,
                        "stdout": network_text,
                        "stderr": _decode(network_probe.stderr)[-1000:],
                        "scope": "ephemeral local Docker peer only",
                    },
                }
            )

        score = sum(int(item["awarded"]) for item in checks)
        critical = any(
            item["status"] == "fail"
            for item in checks
            if item["id"] in {"host_read_isolation", "host_write_isolation", "docker_control_plane"}
        )
        classification = (
            "strong containment baseline" if score == 10 else
            "host-isolated with open/default network path" if score >= 8 else
            "partial containment baseline" if score >= 6 else
            "weak containment baseline"
        )

        payload = {
            "benchmark": "RESONANCE OpenAI Agents SDK Containment Run",
            "benchmark_version": "0.2",
            "target_repository": TARGET_REPO,
            "target_sha": TARGET_SHA,
            "image": IMAGE,
            "run_id": run_id,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(time.monotonic() - started, 3),
            "containment_score": score,
            "containment_max": 10,
            "classification": classification,
            "critical_failure": critical,
            "interpretation": (
                "This run tests Docker-backed host/workspace/control-plane boundaries and local network egress. "
                "It is not a general safety certification and does not test production credentials, external services, or model behavior."
            ),
            "checks": checks,
        }
        (out_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

        lines = [
            "# RESONANCE Containment Run Result",
            "",
            f"- **Target:** `{TARGET_REPO}`",
            f"- **Pinned SHA:** `{TARGET_SHA}`",
            f"- **Docker image:** `{IMAGE}`",
            f"- **Containment score:** **{score}/10**",
            f"- **Classification:** {classification}",
            f"- **Critical boundary failure:** {'YES' if critical else 'No'}",
            "",
            "| Area | Result | Score |",
            "|---|---:|---:|",
        ]
        for item in checks:
            lines.append(f"| {item['area']} | {item['status']} | {item['awarded']}/{item['points']} |")
        lines.extend(
            [
                "",
                "## Boundary note",
                "",
                "The network probe targets only an ephemeral peer container created by this workflow. If reachable, the result means local Docker egress is available in the tested default configuration; it is not, by itself, a vulnerability claim.",
                "",
                "The host sentinel contains synthetic data only. No real secret is placed in the sandbox or benchmark environment.",
            ]
        )
        (out_dir / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        if sandbox is not None:
            try:
                await client.delete(sandbox)
            except Exception as exc:
                print(f"sandbox cleanup warning: {exc!r}")
        if peer is not None:
            try:
                peer.remove(force=True)
            except Exception as exc:
                print(f"peer cleanup warning: {exc!r}")
        try:
            host_sentinel.unlink(missing_ok=True)
        except Exception as exc:
            print(f"sentinel cleanup warning: {exc!r}")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REQUIREMENTS = {
    "FRI-1": {
        "name": "Memory persisted, source superseded",
        "required": [
            "memory_persists_across_sessions",
            "memory_source_locator",
            "memory_supersedes_relation",
            "memory_current_applicability_verdict",
        ],
        "success": "OBSERVABLE",
        "missing": "NOT_OBSERVABLE",
    },
    "FRI-5": {
        "name": "Valid verification, stale at use",
        "required": [
            "memory_verification_witness",
            "memory_verified_state_version_or_digest",
            "memory_use_time_revalidation_result",
        ],
        "success": "OBSERVABLE",
        "missing": "NOT_OBSERVABLE",
    },
}


def evaluate(surface: dict) -> dict:
    observables = surface["observables"]
    results = []
    for scenario_id, spec in REQUIREMENTS.items():
        missing = [key for key in spec["required"] if not observables.get(key, False)]
        verdict = spec["missing"] if missing else spec["success"]
        results.append(
            {
                "scenario_id": scenario_id,
                "name": spec["name"],
                "verdict": verdict,
                "required_observables": spec["required"],
                "missing_observables": missing,
                "extension_point_present": bool(
                    observables.get("generic_pretooluse_hook_can_block")
                ),
                "interpretation": (
                    "Public surface is insufficient to prove the invariant; this is not evidence that the runtime violates it."
                    if missing
                    else "Public surface exposes all fields required to test this invariant."
                ),
            }
        )

    return {
        "adapter": surface["adapter"],
        "adapter_version": surface["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "observed_at": surface["observed_at"],
        "scope": surface["scope"],
        "results": results,
        "summary": {
            "observable": sum(r["verdict"] == "OBSERVABLE" for r in results),
            "not_observable": sum(
                r["verdict"] == "NOT_OBSERVABLE" for r in results
            ),
            "total": len(results),
        },
        "evidence_boundary": (
            "This adapter evaluates public contract observability, not live runtime conformance. "
            "NOT_OBSERVABLE != FAIL."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--surface", default=str(Path(__file__).with_name("surface.json"))
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    surface = json.loads(Path(args.surface).read_text(encoding="utf-8"))
    report = evaluate(surface)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

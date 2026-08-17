#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: hook_logger.py EVENT_LOG", file=sys.stderr)
        return 64

    event_log = Path(sys.argv[1])
    event_log.parent.mkdir(parents=True, exist_ok=True)

    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        payload = {"hook_logger_error": f"invalid stdin: {exc}"}

    record = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "time_ns": time.time_ns(),
        "pid": os.getpid(),
        **payload,
    }

    with event_log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

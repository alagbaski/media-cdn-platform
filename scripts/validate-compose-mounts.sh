#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to validate compose mounts." >&2
  exit 1
fi

docker compose config --format json | python3 -c '
import json
import sys

data = json.load(sys.stdin)
invalid = []

for service_name, service in data.get("services", {}).items():
    for volume in service.get("volumes", []):
        if volume.get("type") != "bind":
            continue

        target = str(volume.get("target", ""))
        if not target.startswith("/"):
            invalid.append(
                {
                    "service": service_name,
                    "source": volume.get("source", ""),
                    "target": target,
                }
            )

if invalid:
    print("Invalid bind mount target(s): container path must be absolute.", file=sys.stderr)
    for entry in invalid:
        print(
            f"- service={entry['service']} source={entry['source']} target={entry['target']}",
            file=sys.stderr,
        )
    sys.exit(1)

print("Compose bind mount targets validated.")
'

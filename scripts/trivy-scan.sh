#!/usr/bin/env bash
set -euo pipefail

# Load environment variables from .env if present in root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
load_env_file() {
  local env_file="$1"
  local line key value

  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ""|\#*) continue
      ;;
    esac

    key="${line%%=*}"
    value="${line#*=}"

    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value%$'\r'}"

    if [[ ! "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
      continue
    fi

    # Keep explicitly exported env vars as highest priority.
    if [ -z "${!key+x}" ]; then
      export "${key}=${value}"
    fi
  done < "$env_file"
}

if [ -f "$REPO_ROOT/.env" ]; then
  load_env_file "$REPO_ROOT/.env"
fi

DEFAULT_IMAGE_REPO="${SERVICE_NAME:-media-cdn-backend}"
DEFAULT_IMAGE_TAG="${DEFAULT_IMAGE_REPO}:${APP_ENVIRONMENT:-local}-scan"
SCAN_IMAGE_TAG="${TRIVY_IMAGE_TAG:-${IMAGE_TAG:-${DEFAULT_IMAGE_TAG}}}"
SCAN_SEVERITY="${TRIVY_SEVERITY:-${SEVERITY:-HIGH,CRITICAL}}"

if ! command -v trivy >/dev/null 2>&1; then
  echo "trivy is not installed. Install it first: https://trivy.dev/latest/getting-started/installation/" >&2
  exit 127
fi

echo "[1/3] Building backend image: ${SCAN_IMAGE_TAG}"
docker build -t "${SCAN_IMAGE_TAG}" ./backend

echo "[2/3] Scanning repository (vuln,secret,misconfig)"
trivy fs \
  --scanners vuln,secret,misconfig \
  --severity "${SCAN_SEVERITY}" \
  --ignore-unfixed \
  --exit-code 1 \
  --no-progress \
  .

echo "[3/3] Scanning backend image (${SCAN_IMAGE_TAG})"
trivy image \
  --severity "${SCAN_SEVERITY}" \
  --ignore-unfixed \
  --exit-code 1 \
  --no-progress \
  "${SCAN_IMAGE_TAG}"

echo "Trivy scans passed."

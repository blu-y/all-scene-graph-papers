#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MSG_SCRIPT="$ROOT_DIR/scripts/commit_msg.py"

if [[ ! -x "$MSG_SCRIPT" ]]; then
  echo "Error: commit message generator not executable: $MSG_SCRIPT" >&2
  exit 1
fi

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

cd "$ROOT_DIR"

COMMIT_MSG="$($MSG_SCRIPT)"

auto_add() {
  if [[ $# -gt 0 ]]; then
    git add -- "$@"
  else
    git add -A
  fi
}

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] Commit message: $COMMIT_MSG"
  if [[ $# -gt 0 ]]; then
    echo "[dry-run] Would run: git add -- $*"
  else
    echo "[dry-run] Would run: git add -A"
  fi
  echo "[dry-run] Would run: git commit -m \"$COMMIT_MSG\""
  echo "[dry-run] Would run: git push"
  exit 0
fi

auto_add "$@"

git commit -m "$COMMIT_MSG"

git push

echo "Committed with message: $COMMIT_MSG"
